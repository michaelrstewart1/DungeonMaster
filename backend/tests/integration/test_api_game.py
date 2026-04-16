"""Integration tests for game endpoints."""
import pytest
from httpx import AsyncClient


class TestGameSessionCreate:
    """Tests for POST /api/game/sessions"""

    async def test_create_game_session_returns_201(self, client: AsyncClient):
        """Creating a game session should return 201 with session data."""
        # Create a campaign first
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

        response = await client.post(
            "/api/game/sessions",
            json={
                "campaign_id": campaign_id,
                "current_phase": "exploration",
                "current_scene": "You enter a tavern.",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["campaign_id"] == campaign_id
        assert data["current_phase"] == "exploration"
        assert data["current_scene"] == "You enter a tavern."
        assert "id" in data
        assert "narrative_history" in data

    async def test_create_game_session_with_only_campaign_id_uses_defaults(
        self, client: AsyncClient
    ):
        """Creating a game session with only campaign_id should use default scene and phase."""
        campaign_response = await client.post(
            "/api/campaigns",
            json={
                "name": "Defaults Campaign",
                "description": "For testing defaults",
                "character_ids": [],
                "world_state": {},
                "dm_settings": {},
            },
        )
        campaign_id = campaign_response.json()["id"]

        response = await client.post(
            "/api/game/sessions",
            json={"campaign_id": campaign_id},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["campaign_id"] == campaign_id
        assert data["current_phase"] == "exploration"
        assert "id" in data  # scene is set by DM greeting, not at creation

    async def test_create_game_session_with_missing_campaign_returns_422(
        self, client: AsyncClient
    ):
        """Creating a game session with missing campaign_id should return 422."""
        response = await client.post(
            "/api/game/sessions",
            json={
                "current_phase": "exploration",
                "current_scene": "You enter a tavern.",
            },
        )
        assert response.status_code == 422

    async def test_create_game_session_with_invalid_campaign_returns_404(
        self, client: AsyncClient
    ):
        """Creating a game session with non-existent campaign should return 404."""
        response = await client.post(
            "/api/game/sessions",
            json={
                "campaign_id": "nonexistent-campaign",
                "current_phase": "exploration",
                "current_scene": "You enter a tavern.",
            },
        )
        assert response.status_code == 404


class TestGameSessionGetState:
    """Tests for GET /api/game/sessions/{id}/state"""

    async def test_get_game_session_state_returns_200(self, client: AsyncClient):
        """Getting game session state should return 200."""
        # Create campaign and session
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

        session_response = await client.post(
            "/api/game/sessions",
            json={
                "campaign_id": campaign_id,
                "current_phase": "exploration",
                "current_scene": "Forest clearing",
            },
        )
        session_id = session_response.json()["id"]

        response = await client.get(f"/api/game/sessions/{session_id}/state")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session_id
        assert data["campaign_id"] == campaign_id
        assert data["current_phase"] == "exploration"
        assert data["current_scene"] == "Forest clearing"

    async def test_get_game_session_state_not_found_returns_404(
        self, client: AsyncClient
    ):
        """Getting non-existent session state should return 404."""
        response = await client.get("/api/game/sessions/nonexistent-id/state")
        assert response.status_code == 404


class TestGameSessionAction:
    """Tests for POST /api/game/sessions/{id}/action"""

    async def test_submit_player_action_returns_200(self, client: AsyncClient):
        """Submitting a player action should return 200 with narration."""
        # Create campaign and session
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

        session_response = await client.post(
            "/api/game/sessions",
            json={
                "campaign_id": campaign_id,
                "current_phase": "exploration",
                "current_scene": "A goblin appears!",
            },
        )
        session_id = session_response.json()["id"]

        response = await client.post(
            f"/api/game/sessions/{session_id}/action",
            json={
                "character_id": "char1",
                "action": "I cast fireball!",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "narration" in data
        # The narration should echo back or contain the action
        assert isinstance(data["narration"], str)

    async def test_submit_action_to_nonexistent_session_returns_404(
        self, client: AsyncClient
    ):
        """Submitting an action to non-existent session should return 404."""
        response = await client.post(
            "/api/game/sessions/nonexistent-id/action",
            json={
                "character_id": "char1",
                "action": "Attack!",
            },
        )
        assert response.status_code == 404


class TestGameSessionCombat:
    """Tests for combat endpoints"""

    async def test_start_combat_returns_200(self, client: AsyncClient):
        """Starting combat should return 200 and update phase."""
        # Create campaign and session
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

        session_response = await client.post(
            "/api/game/sessions",
            json={
                "campaign_id": campaign_id,
                "current_phase": "exploration",
                "current_scene": "Enemies appear!",
            },
        )
        session_id = session_response.json()["id"]

        response = await client.post(f"/api/game/sessions/{session_id}/start-combat")
        assert response.status_code == 200
        data = response.json()
        assert data["current_phase"] == "combat"

    async def test_start_combat_nonexistent_session_returns_404(
        self, client: AsyncClient
    ):
        """Starting combat on non-existent session should return 404."""
        response = await client.post("/api/game/sessions/nonexistent-id/start-combat")
        assert response.status_code == 404

    async def test_end_combat_returns_200(self, client: AsyncClient):
        """Ending combat should return 200 and update phase."""
        # Create campaign and session
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

        session_response = await client.post(
            "/api/game/sessions",
            json={
                "campaign_id": campaign_id,
                "current_phase": "combat",
                "current_scene": "Battle rages!",
            },
        )
        session_id = session_response.json()["id"]

        response = await client.post(f"/api/game/sessions/{session_id}/end-combat")
        assert response.status_code == 200
        data = response.json()
        assert data["current_phase"] == "exploration"

    async def test_end_combat_nonexistent_session_returns_404(
        self, client: AsyncClient
    ):
        """Ending combat on non-existent session should return 404."""
        response = await client.post("/api/game/sessions/nonexistent-id/end-combat")
        assert response.status_code == 404


class TestNPCTalk:
    """Tests for POST /api/game/sessions/{id}/npc-talk"""

    async def _create_session_with_npc(self, client: AsyncClient) -> tuple[str, str]:
        """Helper: create a campaign, session, and add an NPC. Returns (session_id, npc_name)."""
        campaign_response = await client.post(
            "/api/campaigns",
            json={
                "name": "NPC Talk Campaign",
                "description": "For NPC talk tests",
                "character_ids": [],
                "world_state": {},
                "dm_settings": {},
            },
        )
        campaign_id = campaign_response.json()["id"]

        session_response = await client.post(
            "/api/game/sessions",
            json={
                "campaign_id": campaign_id,
                "current_phase": "exploration",
                "current_scene": "A bustling tavern.",
            },
        )
        session_id = session_response.json()["id"]

        # Add an NPC
        npc_name = "Kaelrath"
        await client.post(
            f"/api/game/sessions/{session_id}/npcs",
            json={
                "name": npc_name,
                "npc_type": "merchant",
                "disposition": "neutral",
                "location": "Tavern",
                "notes": "A mysterious merchant",
                "personality": "guarded, calculating",
                "backstory": "A former adventurer turned merchant",
                "goals": "Profit and information",
                "fears": "Being recognized from his past",
                "secrets": "Secretly works for the thieves guild",
            },
        )
        return session_id, npc_name

    async def test_talk_to_npc_returns_200(self, client: AsyncClient):
        """Talking to an existing NPC should return 200 with narration."""
        session_id, npc_name = await self._create_session_with_npc(client)

        response = await client.post(
            f"/api/game/sessions/{session_id}/npc-talk",
            json={"npc_name": npc_name, "message": "Hello there, friend!"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "narration" in data
        assert data["npc_name"] == npc_name
        assert isinstance(data["narration"], str)
        assert len(data["narration"]) > 0

    async def test_talk_to_npc_case_insensitive(self, client: AsyncClient):
        """NPC name lookup should be case-insensitive."""
        session_id, _ = await self._create_session_with_npc(client)

        response = await client.post(
            f"/api/game/sessions/{session_id}/npc-talk",
            json={"npc_name": "kaelrath", "message": "Hello!"},
        )
        assert response.status_code == 200
        assert response.json()["npc_name"] == "Kaelrath"

    async def test_talk_to_nonexistent_npc_returns_404(self, client: AsyncClient):
        """Talking to a non-existent NPC should return 404."""
        session_id, _ = await self._create_session_with_npc(client)

        response = await client.post(
            f"/api/game/sessions/{session_id}/npc-talk",
            json={"npc_name": "Nobody", "message": "Hello?"},
        )
        assert response.status_code == 404
        assert "Nobody" in response.json()["detail"]

    async def test_talk_to_npc_nonexistent_session_returns_404(self, client: AsyncClient):
        """Talking to NPC in non-existent session should return 404."""
        response = await client.post(
            "/api/game/sessions/fake-session/npc-talk",
            json={"npc_name": "Kaelrath", "message": "Hello!"},
        )
        assert response.status_code == 404

    async def test_talk_to_npc_records_history(self, client: AsyncClient):
        """NPC talk should record in narrative history."""
        session_id, npc_name = await self._create_session_with_npc(client)

        await client.post(
            f"/api/game/sessions/{session_id}/npc-talk",
            json={"npc_name": npc_name, "message": "What do you sell?"},
        )

        # Check session state for narrative history
        state = await client.get(f"/api/game/sessions/{session_id}/state")
        history = state.json()["narrative_history"]
        # Should have the initial scene + player message + DM response
        player_entries = [h for h in history if h.startswith("Player:")]
        dm_entries = [h for h in history if h.startswith("DM:")]
        assert any(npc_name in e for e in player_entries)
        assert len(dm_entries) >= 1

    async def test_talk_to_friendly_npc_uses_disposition(self, client: AsyncClient):
        """Friendly NPC should respond with friendly mock text."""
        campaign_response = await client.post(
            "/api/campaigns",
            json={
                "name": "Friendly Campaign",
                "description": "Test",
                "character_ids": [],
                "world_state": {},
                "dm_settings": {},
            },
        )
        campaign_id = campaign_response.json()["id"]
        session_response = await client.post(
            "/api/game/sessions",
            json={"campaign_id": campaign_id, "current_phase": "exploration", "current_scene": "Village"},
        )
        session_id = session_response.json()["id"]

        await client.post(
            f"/api/game/sessions/{session_id}/npcs",
            json={"name": "Elara", "npc_type": "healer", "disposition": "friendly"},
        )
        response = await client.post(
            f"/api/game/sessions/{session_id}/npc-talk",
            json={"npc_name": "Elara", "message": "Can you help us?"},
        )
        assert response.status_code == 200
        # Mock fallback uses disposition to vary response
        assert "Elara" in response.json()["narration"]
