"""Integration tests for character CRUD endpoints."""
import pytest
from httpx import AsyncClient


class TestCharacterCreate:
    """Tests for POST /api/characters"""

    async def test_create_character_returns_201(self, client: AsyncClient):
        """Creating a character should return 201 with character data."""
        response = await client.post(
            "/api/characters",
            json={
                "name": "Aragorn",
                "race": "human",
                "class_name": "ranger",
                "level": 5,
                "strength": 16,
                "dexterity": 14,
                "constitution": 14,
                "intelligence": 12,
                "wisdom": 13,
                "charisma": 11,
                "hp": 45,
                "ac": 14,
                "conditions": [],
                "inventory": [],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Aragorn"
        assert data["race"] == "human"
        assert data["class_name"] == "ranger"
        assert data["level"] == 5
        assert "id" in data

    async def test_create_character_with_invalid_race_returns_422(
        self, client: AsyncClient
    ):
        """Creating a character with invalid race should return 422."""
        response = await client.post(
            "/api/characters",
            json={
                "name": "Bogus",
                "race": "dragon",  # Invalid race
                "class_name": "ranger",
                "level": 5,
                "hp": 45,
                "ac": 14,
            },
        )
        assert response.status_code == 422

    async def test_create_character_with_invalid_class_returns_422(
        self, client: AsyncClient
    ):
        """Creating a character with invalid class should return 422."""
        response = await client.post(
            "/api/characters",
            json={
                "name": "Bogus",
                "race": "human",
                "class_name": "invalid-class",  # Invalid class
                "level": 5,
                "hp": 45,
                "ac": 14,
            },
        )
        assert response.status_code == 422

    async def test_create_character_with_defaults(self, client: AsyncClient):
        """Creating a character with minimal fields should use defaults."""
        response = await client.post(
            "/api/characters",
            json={
                "name": "Fighter",
                "race": "dwarf",
                "class_name": "fighter",
                "level": 1,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["strength"] == 10  # Default
        assert data["hp"] == 8  # Default
        assert data["ac"] == 10  # Default

    async def test_create_character_with_inventory(self, client: AsyncClient):
        """Creating a character with inventory should work."""
        response = await client.post(
            "/api/characters",
            json={
                "name": "Equipped",
                "race": "elf",
                "class_name": "wizard",
                "level": 3,
                "inventory": ["spellbook", "dagger", "rope"],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["inventory"] == ["spellbook", "dagger", "rope"]


class TestCharacterList:
    """Tests for GET /api/characters"""

    async def test_list_characters_empty(self, client: AsyncClient):
        """Listing characters when none exist should return empty list."""
        response = await client.get("/api/characters")
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_characters_returns_all(self, client: AsyncClient):
        """Listing characters should return all characters."""
        # Create two characters
        await client.post(
            "/api/characters",
            json={
                "name": "Character 1",
                "race": "human",
                "class_name": "ranger",
                "level": 1,
            },
        )
        await client.post(
            "/api/characters",
            json={
                "name": "Character 2",
                "race": "elf",
                "class_name": "wizard",
                "level": 1,
            },
        )

        response = await client.get("/api/characters")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Character 1"
        assert data[1]["name"] == "Character 2"

    async def test_list_characters_filter_by_campaign(self, client: AsyncClient):
        """Listing characters can be filtered by campaign_id."""
        # Create a campaign
        campaign_response = await client.post(
            "/api/campaigns",
            json={
                "name": "Test Campaign",
                "description": "For testing",
                "character_ids": [],
                "world_state": {},
                "dm_settings": {},
            },
        )
        campaign_id = campaign_response.json()["id"]

        # Create characters with and without campaign
        char1_response = await client.post(
            "/api/characters",
            json={
                "name": "Campaign Char",
                "race": "human",
                "class_name": "ranger",
                "level": 1,
            },
        )
        char1_id = char1_response.json()["id"]

        # Add character to campaign
        await client.put(
            f"/api/campaigns/{campaign_id}",
            json={
                "name": "Test Campaign",
                "description": "For testing",
                "character_ids": [char1_id],
                "world_state": {},
                "dm_settings": {},
            },
        )

        # Create character not in campaign
        await client.post(
            "/api/characters",
            json={
                "name": "Unaffiliated Char",
                "race": "elf",
                "class_name": "wizard",
                "level": 1,
            },
        )

        # Filter by campaign
        response = await client.get(f"/api/characters?campaign_id={campaign_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Campaign Char"


class TestCharacterGet:
    """Tests for GET /api/characters/{id}"""

    async def test_get_character_returns_200(self, client: AsyncClient):
        """Getting an existing character should return 200."""
        create_response = await client.post(
            "/api/characters",
            json={
                "name": "Legolas",
                "race": "elf",
                "class_name": "ranger",
                "level": 5,
            },
        )
        character_id = create_response.json()["id"]

        response = await client.get(f"/api/characters/{character_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Legolas"
        assert data["id"] == character_id

    async def test_get_character_not_found_returns_404(self, client: AsyncClient):
        """Getting a non-existent character should return 404."""
        response = await client.get("/api/characters/nonexistent-id")
        assert response.status_code == 404


class TestCharacterUpdate:
    """Tests for PUT /api/characters/{id}"""

    async def test_update_character_returns_200(self, client: AsyncClient):
        """Updating an existing character should return 200."""
        create_response = await client.post(
            "/api/characters",
            json={
                "name": "Original",
                "race": "human",
                "class_name": "fighter",
                "level": 1,
                "hp": 10,
            },
        )
        character_id = create_response.json()["id"]

        response = await client.put(
            f"/api/characters/{character_id}",
            json={
                "name": "Updated",
                "level": 3,
                "hp": 25,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated"
        assert data["level"] == 3
        assert data["hp"] == 25

    async def test_update_character_partial(self, client: AsyncClient):
        """Updating only some character fields should work (partial update)."""
        create_response = await client.post(
            "/api/characters",
            json={
                "name": "Partial",
                "race": "dwarf",
                "class_name": "cleric",
                "level": 2,
                "strength": 15,
                "hp": 20,
            },
        )
        character_id = create_response.json()["id"]

        # Only update level and hp, leave others unchanged
        response = await client.put(
            f"/api/characters/{character_id}",
            json={
                "level": 5,
                "hp": 35,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Partial"  # Unchanged
        assert data["race"] == "dwarf"  # Unchanged
        assert data["level"] == 5  # Updated
        assert data["hp"] == 35  # Updated

    async def test_update_character_not_found_returns_404(self, client: AsyncClient):
        """Updating a non-existent character should return 404."""
        response = await client.put(
            "/api/characters/nonexistent-id",
            json={
                "level": 5,
            },
        )
        assert response.status_code == 404


class TestCharacterDelete:
    """Tests for DELETE /api/characters/{id}"""

    async def test_delete_character_returns_204(self, client: AsyncClient):
        """Deleting an existing character should return 204."""
        create_response = await client.post(
            "/api/characters",
            json={
                "name": "To Delete",
                "race": "human",
                "class_name": "ranger",
                "level": 1,
            },
        )
        character_id = create_response.json()["id"]

        response = await client.delete(f"/api/characters/{character_id}")
        assert response.status_code == 204

        # Verify it's actually deleted
        get_response = await client.get(f"/api/characters/{character_id}")
        assert get_response.status_code == 404

    async def test_delete_character_not_found_returns_404(self, client: AsyncClient):
        """Deleting a non-existent character should return 404."""
        response = await client.delete("/api/characters/nonexistent-id")
        assert response.status_code == 404


class TestCharacterCreateExpanded:
    """Tests for POST /api/characters with expanded chargen fields."""

    async def test_create_character_with_all_new_fields(self, client: AsyncClient):
        """Creating a character with all new 5e fields should work."""
        response = await client.post(
            "/api/characters",
            json={
                "name": "Thorin",
                "race": "dwarf",
                "class_name": "fighter",
                "level": 5,
                "subrace": "hill-dwarf",
                "subclass": "champion",
                "background": "soldier",
                "alignment": "lawful-good",
                "strength": 16,
                "dexterity": 12,
                "constitution": 15,
                "intelligence": 10,
                "wisdom": 13,
                "charisma": 8,
                "hp": 44,
                "max_hp": 44,
                "ac": 18,
                "speed": 25,
                "hit_dice": "5d10",
                "skills": ["athletics", "intimidation"],
                "saving_throws": ["strength", "constitution"],
                "languages": ["common", "dwarvish"],
                "tool_proficiencies": ["smith's tools"],
                "armor_proficiencies": ["light", "medium", "heavy", "shields"],
                "weapon_proficiencies": ["simple", "martial"],
                "features": ["second wind", "action surge", "improved critical"],
                "equipment": ["chain mail", "shield", "longsword"],
                "inventory": ["backpack", "torch", "rations"],
                "personality_traits": "I face problems head-on.",
                "ideals": "Honor above all.",
                "bonds": "I fight for my clan.",
                "flaws": "I have a weakness for ale.",
                "backstory": "A veteran of many battles.",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Thorin"
        assert data["subrace"] == "hill-dwarf"
        assert data["subclass"] == "champion"
        assert data["background"] == "soldier"
        assert data["alignment"] == "lawful-good"
        assert data["skills"] == ["athletics", "intimidation"]
        assert data["saving_throws"] == ["strength", "constitution"]
        assert data["languages"] == ["common", "dwarvish"]
        assert data["tool_proficiencies"] == ["smith's tools"]
        assert data["armor_proficiencies"] == ["light", "medium", "heavy", "shields"]
        assert data["weapon_proficiencies"] == ["simple", "martial"]
        assert data["features"] == ["second wind", "action surge", "improved critical"]
        assert data["equipment"] == ["chain mail", "shield", "longsword"]
        assert data["personality_traits"] == "I face problems head-on."
        assert data["ideals"] == "Honor above all."
        assert data["bonds"] == "I fight for my clan."
        assert data["flaws"] == "I have a weakness for ale."
        assert data["backstory"] == "A veteran of many battles."
        assert data["max_hp"] == 44
        assert data["speed"] == 25
        assert data["hit_dice"] == "5d10"

    async def test_backward_compat_minimal_create(self, client: AsyncClient):
        """Old-style create without new fields should still work."""
        response = await client.post(
            "/api/characters",
            json={
                "name": "Simple",
                "race": "human",
                "class_name": "fighter",
                "level": 1,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Simple"
        # New fields should have defaults
        assert data["subrace"] is None
        assert data["subclass"] is None
        assert data["background"] is None
        assert data["alignment"] is None
        assert data["skills"] == []
        assert data["saving_throws"] == []
        assert data["languages"] == []
        assert data["features"] == []
        assert data["equipment"] == []
        assert data["personality_traits"] is None

    async def test_create_with_spellcaster_fields(self, client: AsyncClient):
        """Creating a spellcaster with spells should work."""
        response = await client.post(
            "/api/characters",
            json={
                "name": "Gandalf",
                "race": "human",
                "class_name": "wizard",
                "level": 5,
                "intelligence": 18,
                "spells_known": ["fireball", "shield", "magic missile"],
                "cantrips_known": ["fire bolt", "mage hand", "prestidigitation"],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["spells_known"] == ["fireball", "shield", "magic missile"]
        assert data["cantrips_known"] == ["fire bolt", "mage hand", "prestidigitation"]

    async def test_new_fields_persist_on_get(self, client: AsyncClient):
        """New fields should be returned when fetching the character."""
        create_resp = await client.post(
            "/api/characters",
            json={
                "name": "Persisted",
                "race": "elf",
                "class_name": "ranger",
                "level": 3,
                "subrace": "wood-elf",
                "background": "outlander",
                "skills": ["survival", "nature", "stealth"],
                "languages": ["common", "elvish", "sylvan"],
            },
        )
        char_id = create_resp.json()["id"]

        get_resp = await client.get(f"/api/characters/{char_id}")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["subrace"] == "wood-elf"
        assert data["background"] == "outlander"
        assert data["skills"] == ["survival", "nature", "stealth"]
        assert data["languages"] == ["common", "elvish", "sylvan"]

    async def test_update_new_fields(self, client: AsyncClient):
        """New fields should be updatable via PUT."""
        create_resp = await client.post(
            "/api/characters",
            json={
                "name": "Updatable",
                "race": "human",
                "class_name": "fighter",
                "level": 1,
            },
        )
        char_id = create_resp.json()["id"]

        update_resp = await client.put(
            f"/api/characters/{char_id}",
            json={
                "subclass": "champion",
                "background": "soldier",
                "skills": ["athletics", "intimidation"],
                "alignment": "neutral-good",
            },
        )
        assert update_resp.status_code == 200
        data = update_resp.json()
        assert data["subclass"] == "champion"
        assert data["background"] == "soldier"
        assert data["skills"] == ["athletics", "intimidation"]
        assert data["alignment"] == "neutral-good"

    async def test_create_with_experience_points(self, client: AsyncClient):
        """Creating a character with XP should work."""
        response = await client.post(
            "/api/characters",
            json={
                "name": "Experienced",
                "race": "human",
                "class_name": "fighter",
                "level": 5,
                "experience_points": 6500,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["experience_points"] == 6500


class TestCharacterExport:
    """Tests for GET /api/characters/{id}/export"""

    async def test_export_character_returns_json(self, client: AsyncClient):
        """Exporting a character should return JSON with Content-Disposition header."""
        create_resp = await client.post(
            "/api/characters",
            json={
                "name": "Exportable",
                "race": "human",
                "class_name": "fighter",
                "level": 5,
                "hp": 40,
                "ac": 16,
            },
        )
        char_id = create_resp.json()["id"]

        export_resp = await client.get(f"/api/characters/{char_id}/export")
        assert export_resp.status_code == 200
        assert "application/json" in export_resp.headers["content-type"]
        assert "attachment" in export_resp.headers.get("content-disposition", "")
        assert "exportable.json" in export_resp.headers["content-disposition"]

        data = export_resp.json()
        assert data["name"] == "Exportable"
        assert data["id"] == char_id
        assert data["hp"] == 40
        assert data["ac"] == 16

    async def test_export_character_with_new_fields(self, client: AsyncClient):
        """Exported character should include all new chargen fields."""
        create_resp = await client.post(
            "/api/characters",
            json={
                "name": "Full Export",
                "race": "dwarf",
                "class_name": "cleric",
                "level": 3,
                "subrace": "hill-dwarf",
                "subclass": "life-domain",
                "background": "acolyte",
                "alignment": "lawful-good",
                "skills": ["medicine", "religion"],
                "languages": ["common", "dwarvish", "celestial"],
                "equipment": ["mace", "scale mail", "shield"],
                "spells_known": ["cure wounds", "bless"],
                "cantrips_known": ["sacred flame", "guidance"],
                "personality_traits": "I see omens everywhere.",
                "ideals": "Faith guides my path.",
            },
        )
        char_id = create_resp.json()["id"]

        export_resp = await client.get(f"/api/characters/{char_id}/export")
        assert export_resp.status_code == 200
        data = export_resp.json()
        assert data["subrace"] == "hill-dwarf"
        assert data["subclass"] == "life-domain"
        assert data["background"] == "acolyte"
        assert data["alignment"] == "lawful-good"
        assert data["skills"] == ["medicine", "religion"]
        assert data["languages"] == ["common", "dwarvish", "celestial"]
        assert data["equipment"] == ["mace", "scale mail", "shield"]
        assert data["spells_known"] == ["cure wounds", "bless"]
        assert data["cantrips_known"] == ["sacred flame", "guidance"]
        assert data["personality_traits"] == "I see omens everywhere."
        assert data["ideals"] == "Faith guides my path."

    async def test_export_not_found(self, client: AsyncClient):
        """Exporting a nonexistent character should return 404."""
        response = await client.get("/api/characters/nonexistent-id/export")
        assert response.status_code == 404

    async def test_export_filename_sanitized(self, client: AsyncClient):
        """Export filename should be derived from character name."""
        create_resp = await client.post(
            "/api/characters",
            json={
                "name": "Sir Galahad",
                "race": "human",
                "class_name": "paladin",
                "level": 1,
            },
        )
        char_id = create_resp.json()["id"]

        export_resp = await client.get(f"/api/characters/{char_id}/export")
        assert export_resp.status_code == 200
        disposition = export_resp.headers["content-disposition"]
        assert "sir_galahad.json" in disposition
