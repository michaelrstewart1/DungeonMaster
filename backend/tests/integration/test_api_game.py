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
