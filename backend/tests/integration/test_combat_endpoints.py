"""Integration tests — rules-engine-driven combat endpoints."""
import pytest
from httpx import AsyncClient


async def _make_session(client: AsyncClient, with_character: bool = True) -> tuple[str, str, str | None]:
    """Create campaign (+optional character) + session. Returns (campaign_id, session_id, char_id)."""
    char_id = None
    character_ids = []
    if with_character:
        char_resp = await client.post(
            "/api/characters",
            json={
                "name": "Thorin",
                "race": "dwarf",
                "class_name": "fighter",
                "level": 3,
                "strength": 16,
                "dexterity": 12,
                "constitution": 14,
                "intelligence": 10,
                "wisdom": 10,
                "charisma": 8,
                "max_hp": 28,
                "ac": 16,
            },
        )
        assert char_resp.status_code == 201, char_resp.text
        char_id = char_resp.json()["id"]
        character_ids = [char_id]

    camp_resp = await client.post(
        "/api/campaigns",
        json={
            "name": "Combat Campaign",
            "description": "Testing combat",
            "character_ids": character_ids,
            "world_state": {},
            "dm_settings": {},
        },
    )
    campaign_id = camp_resp.json()["id"]
    sess_resp = await client.post("/api/game/sessions", json={"campaign_id": campaign_id})
    return campaign_id, sess_resp.json()["id"], char_id


class TestStartCombatWithEnemies:
    async def test_start_combat_rolls_full_initiative(self, client: AsyncClient):
        _, session_id, _ = await _make_session(client)
        resp = await client.post(
            f"/api/game/sessions/{session_id}/start-combat",
            json={"enemies": [{"name": "Goblin", "hp": 7, "ac": 15, "cr": 0.25, "count": 2}]},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["current_phase"] == "combat"
        cs = data["combat_state"]
        assert len(cs["initiative_order"]) == 3
        assert len(cs["combatants"]) == 3
        assert cs["round_number"] == 1
        names = {c["name"] for c in cs["combatants"]}
        assert "Thorin" in names

    async def test_start_combat_without_body_keeps_legacy_behavior(self, client: AsyncClient):
        _, session_id, _ = await _make_session(client, with_character=False)
        resp = await client.post(f"/api/game/sessions/{session_id}/start-combat")
        assert resp.status_code == 200
        cs = resp.json()["combat_state"]
        assert cs["initiative_order"] == []
        assert cs["round_number"] == 1

    async def test_combat_state_survives_reload(self, client: AsyncClient):
        _, session_id, _ = await _make_session(client)
        await client.post(
            f"/api/game/sessions/{session_id}/start-combat",
            json={"enemies": [{"name": "Goblin", "hp": 7, "ac": 15, "cr": 0.25, "count": 1}]},
        )
        state = await client.get(f"/api/game/sessions/{session_id}/state")
        cs = state.json()["combat_state"]
        assert len(cs["combatants"]) == 2


class TestCombatAction:
    async def _start(self, client: AsyncClient, enemy_hp: int = 1, enemy_ac: int = 1):
        _, session_id, char_id = await _make_session(client)
        resp = await client.post(
            f"/api/game/sessions/{session_id}/start-combat",
            json={"enemies": [{"name": "Goblin", "hp": enemy_hp, "ac": enemy_ac, "cr": 0.25, "count": 1}]},
        )
        return session_id, char_id, resp.json()["combat_state"]

    async def test_attack_resolves_and_persists(self, client: AsyncClient):
        # Weak goblin: fight until combat ends (bounded rounds)
        session_id, char_id, cs = await self._start(client)
        for _ in range(30):
            state = (await client.get(f"/api/game/sessions/{session_id}/state")).json()
            if state["current_phase"] != "combat":
                break
            resp = await client.post(
                f"/api/game/sessions/{session_id}/combat-action",
                json={"actor_id": char_id, "action_type": "attack", "target_id": "enemy-1"},
            )
            assert resp.status_code == 200, resp.text
            data = resp.json()
            assert data["events"]
            if data["combat_over"]:
                assert data["victory"] is True
                assert data["xp_awarded"] == 25
                break
        # After victory the session returns to exploration
        state = (await client.get(f"/api/game/sessions/{session_id}/state")).json()
        assert state["current_phase"] == "exploration"
        assert any("Goblin" in line or "Victory" in line for line in state["narrative_history"])

    async def test_combat_action_without_combat_returns_409(self, client: AsyncClient):
        _, session_id, char_id = await _make_session(client)
        resp = await client.post(
            f"/api/game/sessions/{session_id}/combat-action",
            json={"actor_id": char_id or "x", "action_type": "attack"},
        )
        assert resp.status_code == 409

    async def test_combat_action_unknown_actor_returns_422(self, client: AsyncClient):
        session_id, _, _ = await self._start(client, enemy_hp=30, enemy_ac=15)
        resp = await client.post(
            f"/api/game/sessions/{session_id}/combat-action",
            json={"actor_id": "not-a-combatant", "action_type": "attack"},
        )
        assert resp.status_code == 422

    async def test_combat_action_missing_session_returns_404(self, client: AsyncClient):
        resp = await client.post(
            "/api/game/sessions/nope/combat-action",
            json={"actor_id": "x", "action_type": "attack"},
        )
        assert resp.status_code == 404
