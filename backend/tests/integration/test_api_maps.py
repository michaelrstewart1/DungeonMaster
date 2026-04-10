"""Integration tests for map state API endpoints."""
import pytest
from httpx import AsyncClient


class TestGetMapState:
    """Tests for GET /api/maps/{session_id}"""

    async def test_get_map_returns_404_for_nonexistent_session(self, client: AsyncClient):
        """GET /api/maps/{session_id} returns 404 when session doesn't exist."""
        resp = await client.get("/api/maps/nonexistent-session")
        assert resp.status_code == 404

    async def test_get_map_returns_initial_map_state(self, client: AsyncClient):
        """GET /api/maps/{session_id} returns map state for existing session."""
        session_id = "test-session-1"
        
        # First create a map
        map_data = {
            "width": 10,
            "height": 10,
            "terrain_grid": [["empty"] * 10 for _ in range(10)],
            "token_positions": [],
            "fog_of_war": [[False] * 10 for _ in range(10)],
        }
        await client.put(f"/api/maps/{session_id}", json=map_data)
        
        # Then get it
        resp = await client.get(f"/api/maps/{session_id}")
        assert resp.status_code == 200
        
        body = resp.json()
        assert body["width"] == 10
        assert body["height"] == 10
        assert body["terrain_grid"] == map_data["terrain_grid"]
        assert body["token_positions"] == []
        assert body["fog_of_war"] == map_data["fog_of_war"]


class TestCreateOrUpdateMap:
    """Tests for PUT /api/maps/{session_id}"""

    async def test_put_map_creates_new_map(self, client: AsyncClient):
        """PUT /api/maps/{session_id} creates map if it doesn't exist."""
        session_id = "test-session-2"
        map_data = {
            "width": 20,
            "height": 15,
            "terrain_grid": [["water"] * 20 for _ in range(15)],
            "token_positions": [],
            "fog_of_war": [[False] * 20 for _ in range(15)],
        }
        
        resp = await client.put(f"/api/maps/{session_id}", json=map_data)
        assert resp.status_code == 200
        
        body = resp.json()
        assert body["width"] == 20
        assert body["height"] == 15
        assert body["terrain_grid"] == map_data["terrain_grid"]

    async def test_put_map_updates_existing_map(self, client: AsyncClient):
        """PUT /api/maps/{session_id} updates map if it exists."""
        session_id = "test-session-3"
        
        # Create initial map
        map_data_1 = {
            "width": 10,
            "height": 10,
            "terrain_grid": [["empty"] * 10 for _ in range(10)],
            "token_positions": [],
            "fog_of_war": [[False] * 10 for _ in range(10)],
        }
        await client.put(f"/api/maps/{session_id}", json=map_data_1)
        
        # Update with new map
        map_data_2 = {
            "width": 20,
            "height": 20,
            "terrain_grid": [["wall"] * 20 for _ in range(20)],
            "token_positions": [],
            "fog_of_war": [[False] * 20 for _ in range(20)],
        }
        resp = await client.put(f"/api/maps/{session_id}", json=map_data_2)
        assert resp.status_code == 200
        
        body = resp.json()
        assert body["width"] == 20
        assert body["height"] == 20
        assert body["terrain_grid"] == map_data_2["terrain_grid"]

    async def test_put_map_with_token_positions(self, client: AsyncClient):
        """PUT /api/maps/{session_id} accepts token positions."""
        session_id = "test-session-4"
        map_data = {
            "width": 10,
            "height": 10,
            "terrain_grid": [["empty"] * 10 for _ in range(10)],
            "token_positions": [
                {"entity_id": "char1", "x": 5, "y": 5},
                {"entity_id": "char2", "x": 3, "y": 3},
            ],
            "fog_of_war": [[False] * 10 for _ in range(10)],
        }
        
        resp = await client.put(f"/api/maps/{session_id}", json=map_data)
        assert resp.status_code == 200
        
        body = resp.json()
        assert len(body["token_positions"]) == 2
        assert body["token_positions"][0]["entity_id"] == "char1"
        assert body["token_positions"][0]["x"] == 5


class TestMoveToken:
    """Tests for PATCH /api/maps/{session_id}/tokens/{token_id}/position"""

    async def test_patch_token_position_updates_token_location(self, client: AsyncClient):
        """PATCH updates a token's position."""
        session_id = "test-session-5"
        
        # Create map with token
        map_data = {
            "width": 10,
            "height": 10,
            "terrain_grid": [["empty"] * 10 for _ in range(10)],
            "token_positions": [{"entity_id": "char1", "x": 5, "y": 5}],
            "fog_of_war": [[False] * 10 for _ in range(10)],
        }
        await client.put(f"/api/maps/{session_id}", json=map_data)
        
        # Move token
        new_position = {"x": 7, "y": 8}
        resp = await client.patch(
            f"/api/maps/{session_id}/tokens/char1/position",
            json=new_position
        )
        assert resp.status_code == 200
        
        body = resp.json()
        token = next((t for t in body["token_positions"] if t["entity_id"] == "char1"), None)
        assert token is not None
        assert token["x"] == 7
        assert token["y"] == 8

    async def test_patch_token_position_returns_404_for_nonexistent_token(
        self, client: AsyncClient
    ):
        """PATCH returns 404 if token doesn't exist."""
        session_id = "test-session-6"
        
        # Create map without tokens
        map_data = {
            "width": 10,
            "height": 10,
            "terrain_grid": [["empty"] * 10 for _ in range(10)],
            "token_positions": [],
            "fog_of_war": [[False] * 10 for _ in range(10)],
        }
        await client.put(f"/api/maps/{session_id}", json=map_data)
        
        # Try to move nonexistent token
        new_position = {"x": 7, "y": 8}
        resp = await client.patch(
            f"/api/maps/{session_id}/tokens/nonexistent/position",
            json=new_position
        )
        assert resp.status_code == 404

    async def test_patch_token_position_returns_404_for_nonexistent_session(
        self, client: AsyncClient
    ):
        """PATCH returns 404 if session doesn't exist."""
        new_position = {"x": 7, "y": 8}
        resp = await client.patch(
            "/api/maps/nonexistent-session/tokens/char1/position",
            json=new_position
        )
        assert resp.status_code == 404

    async def test_patch_token_position_validates_bounds(self, client: AsyncClient):
        """PATCH validates that new position is within grid bounds."""
        session_id = "test-session-7"
        
        # Create small map
        map_data = {
            "width": 5,
            "height": 5,
            "terrain_grid": [["empty"] * 5 for _ in range(5)],
            "token_positions": [{"entity_id": "char1", "x": 2, "y": 2}],
            "fog_of_war": [[False] * 5 for _ in range(5)],
        }
        await client.put(f"/api/maps/{session_id}", json=map_data)
        
        # Try to move outside bounds
        new_position = {"x": 10, "y": 10}
        resp = await client.patch(
            f"/api/maps/{session_id}/tokens/char1/position",
            json=new_position
        )
        assert resp.status_code == 400


class TestUpdateFogOfWar:
    """Tests for POST /api/maps/{session_id}/fog"""

    async def test_post_fog_reveals_cells(self, client: AsyncClient):
        """POST /api/maps/{session_id}/fog reveals fog cells."""
        session_id = "test-session-8"
        
        # Create map
        map_data = {
            "width": 10,
            "height": 10,
            "terrain_grid": [["empty"] * 10 for _ in range(10)],
            "token_positions": [],
            "fog_of_war": [[True] * 10 for _ in range(10)],  # All fogged
        }
        await client.put(f"/api/maps/{session_id}", json=map_data)
        
        # Reveal some cells
        revealed = [[0, 0], [1, 1], [2, 2]]
        resp = await client.post(
            f"/api/maps/{session_id}/fog",
            json={"revealed": revealed}
        )
        assert resp.status_code == 200
        
        body = resp.json()
        # Check that revealed cells are now False (not fogged)
        assert body["fog_of_war"][0][0] is False
        assert body["fog_of_war"][1][1] is False
        assert body["fog_of_war"][2][2] is False
        # Check that other cells remain fogged
        assert body["fog_of_war"][0][1] is True

    async def test_post_fog_returns_404_for_nonexistent_session(self, client: AsyncClient):
        """POST /api/maps/{session_id}/fog returns 404 if session doesn't exist."""
        resp = await client.post(
            "/api/maps/nonexistent-session/fog",
            json={"revealed": [[0, 0]]}
        )
        assert resp.status_code == 404

    async def test_post_fog_handles_edge_cases(self, client: AsyncClient):
        """POST /api/maps/{session_id}/fog handles edge coordinates."""
        session_id = "test-session-9"
        
        # Create map
        map_data = {
            "width": 10,
            "height": 10,
            "terrain_grid": [["empty"] * 10 for _ in range(10)],
            "token_positions": [],
            "fog_of_war": [[True] * 10 for _ in range(10)],
        }
        await client.put(f"/api/maps/{session_id}", json=map_data)
        
        # Reveal edges and corners
        revealed = [[0, 0], [9, 9], [0, 9], [9, 0]]
        resp = await client.post(
            f"/api/maps/{session_id}/fog",
            json={"revealed": revealed}
        )
        assert resp.status_code == 200
        
        body = resp.json()
        assert body["fog_of_war"][0][0] is False
        assert body["fog_of_war"][9][9] is False
        assert body["fog_of_war"][0][9] is False
        assert body["fog_of_war"][9][0] is False


class TestMapPersistence:
    """Tests for map state persistence across requests."""

    async def test_map_state_persists_across_requests(self, client: AsyncClient):
        """Map state persists when updated."""
        session_id = "test-session-10"
        
        # Create map
        map_data_1 = {
            "width": 10,
            "height": 10,
            "terrain_grid": [["empty"] * 10 for _ in range(10)],
            "token_positions": [{"entity_id": "char1", "x": 5, "y": 5}],
            "fog_of_war": [[False] * 10 for _ in range(10)],
        }
        await client.put(f"/api/maps/{session_id}", json=map_data_1)
        
        # Move token
        await client.patch(
            f"/api/maps/{session_id}/tokens/char1/position",
            json={"x": 7, "y": 8}
        )
        
        # Update fog
        await client.post(
            f"/api/maps/{session_id}/fog",
            json={"revealed": [[0, 0], [1, 1]]}
        )
        
        # Get map and verify all changes persisted
        resp = await client.get(f"/api/maps/{session_id}")
        assert resp.status_code == 200
        
        body = resp.json()
        token = next((t for t in body["token_positions"] if t["entity_id"] == "char1"), None)
        assert token["x"] == 7
        assert token["y"] == 8
        assert body["fog_of_war"][0][0] is False
        assert body["fog_of_war"][1][1] is False
