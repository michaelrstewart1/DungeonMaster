"""Tests for auto-save persistence, loot distribution, XP events, and level-up."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch


# ─── Auto-Save Tests ────────────────────────────────────────────────────


class TestAutoSave:
    """Test file-based persistence."""

    def test_save_and_load_roundtrip(self):
        """Saving and loading preserves campaigns, characters, sessions."""
        from app.api import storage

        storage.campaigns["c1"] = {"id": "c1", "name": "Test Campaign"}
        storage.characters["ch1"] = {
            "id": "ch1", "name": "Gandalf", "race": "human",
            "class_name": "wizard", "level": 5, "experience_points": 6500,
        }
        storage.game_sessions["s1"] = {
            "id": "s1", "campaign_id": "c1", "turn_count": 3,
            "narrative_history": ["scene", "Player: hi", "DM: hello"],
        }

        with patch.object(storage, "_SAVE_DIR", Path("test_save_tmp")):
            with patch.object(storage, "_SAVE_FILE", Path("test_save_tmp/save.json")):
                storage.save_to_disk()

                # Clear and reload
                storage.campaigns.clear()
                storage.characters.clear()
                storage.game_sessions.clear()
                assert len(storage.campaigns) == 0

                loaded = storage.load_from_disk()
                assert loaded is True
                assert storage.campaigns["c1"]["name"] == "Test Campaign"
                assert storage.characters["ch1"]["name"] == "Gandalf"
                assert storage.characters["ch1"]["experience_points"] == 6500
                assert storage.game_sessions["s1"]["turn_count"] == 3

                # Cleanup
                import shutil
                shutil.rmtree("test_save_tmp", ignore_errors=True)

    def test_load_missing_file_returns_false(self):
        """Loading when no save file exists returns False."""
        from app.api import storage
        with patch.object(storage, "_SAVE_FILE", Path("/nonexistent/save.json")):
            assert storage.load_from_disk() is False

    def test_save_uses_atomic_write(self):
        """Save writes to .tmp then renames (no partial writes)."""
        from app.api import storage
        storage.campaigns["c1"] = {"id": "c1", "name": "Test"}

        with patch.object(storage, "_SAVE_DIR", Path("test_save_tmp2")):
            with patch.object(storage, "_SAVE_FILE", Path("test_save_tmp2/save.json")):
                storage.save_to_disk()
                # .tmp should not exist after save
                assert not Path("test_save_tmp2/save.json.tmp").exists()
                assert Path("test_save_tmp2/save.json").exists()

                import shutil
                shutil.rmtree("test_save_tmp2", ignore_errors=True)


# ─── Loot Distribution Tests ────────────────────────────────────────────


class TestLootDistribution:
    """Test distributing loot from party to characters."""

    @pytest.fixture
    def setup_session(self):
        """Create a session with party loot and a character."""
        from app.api import storage
        storage.campaigns["camp1"] = {
            "id": "camp1", "name": "Test", "character_ids": ["char1"],
        }
        storage.characters["char1"] = {
            "id": "char1", "name": "Thorin", "race": "dwarf",
            "class_name": "fighter", "level": 3,
            "inventory": [], "equipment": [],
            "experience_points": 0,
        }
        storage.game_sessions["sess1"] = {
            "id": "sess1", "campaign_id": "camp1",
            "current_phase": "exploration", "current_scene": "A dungeon",
            "narrative_history": [], "combat_state": None, "active_effects": [],
            "party_loot": [
                {"name": "Longsword +1", "description": "A magical sword", "rarity": "uncommon",
                 "quantity": 1, "item_type": "weapon"},
                {"name": "Healing Potion", "description": "Restores 2d4+2 HP", "rarity": "common",
                 "quantity": 3, "item_type": "potion"},
            ],
            "party_gold": 150,
        }

    @pytest.mark.asyncio
    async def test_distribute_single_item(self, client, setup_session):
        resp = await client.post("/api/game/sessions/sess1/distribute-loot", json={
            "item_index": 0, "character_id": "char1",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["distributed"]["item"] == "Longsword +1"
        assert data["distributed"]["to"] == "Thorin"
        assert "Longsword +1" in data["character_inventory"]
        # Item removed from party loot
        assert len(data["party_loot"]) == 1

    @pytest.mark.asyncio
    async def test_distribute_partial_stack(self, client, setup_session):
        resp = await client.post("/api/game/sessions/sess1/distribute-loot", json={
            "item_index": 1, "character_id": "char1", "quantity": 2,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["distributed"]["quantity"] == 2
        # 1 potion left in party
        assert data["party_loot"][1]["quantity"] == 1

    @pytest.mark.asyncio
    async def test_distribute_invalid_index(self, client, setup_session):
        resp = await client.post("/api/game/sessions/sess1/distribute-loot", json={
            "item_index": 99, "character_id": "char1",
        })
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_distribute_unknown_character(self, client, setup_session):
        resp = await client.post("/api/game/sessions/sess1/distribute-loot", json={
            "item_index": 0, "character_id": "nobody",
        })
        assert resp.status_code == 404


# ─── XP Event Tests ─────────────────────────────────────────────────────


class TestXPEvent:
    """Test structured XP awarding from game events."""

    @pytest.fixture
    def setup_xp(self):
        from app.api import storage
        storage.campaigns["camp1"] = {
            "id": "camp1", "name": "Test", "character_ids": ["char1", "char2"],
        }
        storage.characters["char1"] = {
            "id": "char1", "name": "Aria", "race": "elf",
            "class_name": "ranger", "level": 3,
            "experience_points": 800, "inventory": [], "equipment": [],
        }
        storage.characters["char2"] = {
            "id": "char2", "name": "Brom", "race": "human",
            "class_name": "fighter", "level": 3,
            "experience_points": 800, "inventory": [], "equipment": [],
        }
        storage.game_sessions["sess1"] = {
            "id": "sess1", "campaign_id": "camp1",
            "current_phase": "combat", "current_scene": "Battle",
            "narrative_history": [], "combat_state": None, "active_effects": [],
        }

    @pytest.mark.asyncio
    async def test_award_xp_by_cr(self, client, setup_xp):
        resp = await client.post("/api/game/sessions/sess1/xp-event", json={
            "event_type": "combat",
            "description": "Defeated 3 goblins",
            "cr": "1/4",
            "creature_count": 3,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_xp"] == 150  # 50 * 3
        assert data["xp_per_character"] == 75  # split between 2

    @pytest.mark.asyncio
    async def test_award_xp_by_total(self, client, setup_xp):
        resp = await client.post("/api/game/sessions/sess1/xp-event", json={
            "event_type": "quest",
            "description": "Completed the rescue mission",
            "xp_total": 500,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["xp_per_character"] == 250

    @pytest.mark.asyncio
    async def test_xp_triggers_level_up(self, client, setup_xp):
        """Awarding enough XP should trigger level-up and create pending choices."""
        from app.api import storage
        # Characters at 800 XP (level 3). Need 2700 for level 4.
        resp = await client.post("/api/game/sessions/sess1/xp-event", json={
            "event_type": "combat",
            "description": "Defeated the ogre boss",
            "xp_total": 4000,
        })
        assert resp.status_code == 200
        data = resp.json()
        # Each gets 2000, total = 2800. That's level 4 (threshold 2700).
        for award in data["awards"]:
            assert award["leveled_up"] is True
            assert award["new_level"] == 4

        # Check pending level-up exists
        char = storage.characters["char1"]
        assert len(char.get("pending_level_ups", [])) == 1
        assert char["pending_level_ups"][0]["to_level"] == 4

    @pytest.mark.asyncio
    async def test_xp_specific_characters(self, client, setup_xp):
        """Can award XP to specific characters only."""
        resp = await client.post("/api/game/sessions/sess1/xp-event", json={
            "event_type": "roleplay",
            "description": "Excellent diplomacy",
            "xp_total": 100,
            "character_ids": ["char1"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["awards"]) == 1
        assert data["awards"][0]["character_id"] == "char1"
        assert data["xp_per_character"] == 100

    @pytest.mark.asyncio
    async def test_xp_no_cr_or_total_fails(self, client, setup_xp):
        resp = await client.post("/api/game/sessions/sess1/xp-event", json={
            "event_type": "combat",
            "description": "Something happened",
        })
        assert resp.status_code == 400


# ─── Level-Up Tests ─────────────────────────────────────────────────────


class TestLevelUp:
    """Test level-up management."""

    @pytest.fixture
    def setup_level_up(self):
        from app.api import storage
        storage.characters["char1"] = {
            "id": "char1", "name": "Aria", "race": "elf",
            "class_name": "fighter", "level": 4,
            "experience_points": 2700, "hp": 28, "max_hp": 28,
            "strength": 16, "dexterity": 14, "constitution": 14,
            "intelligence": 10, "wisdom": 12, "charisma": 8,
            "inventory": [], "equipment": [], "skills": ["athletics", "perception"],
            "features": [], "spells_known": [],
            "pending_level_ups": [{
                "from_level": 3, "to_level": 4,
                "choices_made": False, "hp_rolled": False,
            }],
        }

    @pytest.mark.asyncio
    async def test_get_pending_level_ups(self, client, setup_level_up):
        resp = await client.get("/api/game/characters/char1/pending-level-ups")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["pending"]) == 1
        assert data["pending"][0]["to_level"] == 4

    @pytest.mark.asyncio
    async def test_apply_level_up_with_asi(self, client, setup_level_up):
        """Apply level-up at ASI level with ability score increase."""
        resp = await client.post("/api/game/characters/char1/apply-level-up", json={
            "ability_score_increase": {"strength": 2},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["changes_applied"] is True
        assert data["hp_gained"] > 0
        assert data["remaining_level_ups"] == 0
        # Strength should have increased
        assert data["character"]["strength"] == 18

    @pytest.mark.asyncio
    async def test_apply_level_up_with_feat(self, client, setup_level_up):
        resp = await client.post("/api/game/characters/char1/apply-level-up", json={
            "feat": "Great Weapon Master",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "Feat: Great Weapon Master" in data["character"]["features"]

    @pytest.mark.asyncio
    async def test_apply_level_up_average_hp(self, client, setup_level_up):
        """Without hp_roll, should take average."""
        resp = await client.post("/api/game/characters/char1/apply-level-up", json={})
        assert resp.status_code == 200
        data = resp.json()
        # Fighter: d10 → avg = 6, con_mod = +2 → 8 HP
        assert data["hp_gained"] == 8

    @pytest.mark.asyncio
    async def test_apply_level_up_with_hp_roll(self, client, setup_level_up):
        resp = await client.post("/api/game/characters/char1/apply-level-up", json={
            "hp_roll": 9,
        })
        assert resp.status_code == 200
        # 9 (roll) + 2 (con mod) = 11
        assert resp.json()["hp_gained"] == 11

    @pytest.mark.asyncio
    async def test_no_pending_level_ups_fails(self, client):
        from app.api import storage
        storage.characters["char1"] = {
            "id": "char1", "name": "Aria", "race": "elf",
            "class_name": "fighter", "level": 3,
            "experience_points": 800, "inventory": [], "equipment": [],
        }
        resp = await client.post("/api/game/characters/char1/apply-level-up", json={})
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_asi_capped_at_20(self, client):
        """ASI cannot push ability scores above 20."""
        from app.api import storage
        storage.characters["char1"] = {
            "id": "char1", "name": "Aria", "race": "elf",
            "class_name": "fighter", "level": 4,
            "experience_points": 2700, "hp": 28, "max_hp": 28,
            "strength": 19, "dexterity": 14, "constitution": 14,
            "intelligence": 10, "wisdom": 12, "charisma": 8,
            "inventory": [], "equipment": [], "skills": [],
            "features": [], "spells_known": [],
            "pending_level_ups": [{
                "from_level": 3, "to_level": 4,
                "choices_made": False, "hp_rolled": False,
            }],
        }
        resp = await client.post("/api/game/characters/char1/apply-level-up", json={
            "ability_score_increase": {"strength": 2},
        })
        assert resp.status_code == 200
        assert resp.json()["character"]["strength"] == 20  # Capped
