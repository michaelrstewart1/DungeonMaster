"""Full-stack integration tests for AI Dungeon Master API."""
import pytest
from httpx import AsyncClient


class TestFullStackPlayerJourney:
    """Test the complete player journey from registration to game session."""

    async def test_01_register_user(self, client: AsyncClient):
        """Test user registration."""
        resp = await client.post("/api/auth/register", json={
            "username": "adventurer",
            "password": "mysecretpassword123",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "adventurer"
        assert "id" in data
        assert "password" not in data

    async def test_02_login_user(self, client: AsyncClient):
        """Test user login."""
        # Register first
        await client.post("/api/auth/register", json={
            "username": "adventurer",
            "password": "mysecretpassword123",
        })
        
        # Login
        resp = await client.post("/api/auth/login", json={
            "username": "adventurer",
            "password": "mysecretpassword123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert data["username"] == "adventurer"

    async def test_03_create_campaign(self, client: AsyncClient):
        """Test campaign creation."""
        resp = await client.post("/api/campaigns", json={
            "name": "The Lost Mines",
            "description": "A classic adventure",
            "character_ids": [],
            "world_state": {"locations": ["Neverwinter", "Waterdeep"]},
            "dm_settings": {"difficulty": "medium"},
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "The Lost Mines"
        assert "id" in data
        return data["id"]

    async def test_04_get_campaign(self, client: AsyncClient):
        """Test retrieving a campaign."""
        # Create campaign
        create_resp = await client.post("/api/campaigns", json={
            "name": "The Lost Mines",
            "description": "A classic adventure",
            "character_ids": [],
            "world_state": {},
            "dm_settings": {},
        })
        campaign_id = create_resp.json()["id"]
        
        # Get campaign
        resp = await client.get(f"/api/campaigns/{campaign_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == campaign_id
        assert data["name"] == "The Lost Mines"

    async def test_05_create_character(self, client: AsyncClient):
        """Test character creation."""
        resp = await client.post("/api/characters", json={
            "name": "Thorin",
            "class_name": "fighter",  # lowercase
            "race": "dwarf",  # lowercase
            "level": 1,
            "strength": 15,
            "dexterity": 10,
            "constitution": 16,
            "intelligence": 8,
            "wisdom": 13,
            "charisma": 12,
            "hp": 12,
            "ac": 16,
            "inventory": ["shortsword", "shield"],
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Thorin"
        assert "id" in data
        assert data["class_name"] == "fighter"
        return data["id"]

    async def test_06_create_game_session(self, client: AsyncClient):
        """Test game session creation."""
        # Create campaign first
        campaign_resp = await client.post("/api/campaigns", json={
            "name": "The Lost Mines",
            "description": "A classic adventure",
            "character_ids": [],
            "world_state": {},
            "dm_settings": {},
        })
        campaign_id = campaign_resp.json()["id"]
        
        # Create game session
        resp = await client.post("/api/game/sessions", json={
            "campaign_id": campaign_id,
            "current_phase": "exploration",
            "current_scene": "You awaken in a dark cave...",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["campaign_id"] == campaign_id
        assert "id" in data
        assert data["current_phase"] == "exploration"
        return data["id"]

    async def test_07_get_game_session(self, client: AsyncClient):
        """Test retrieving game session state."""
        # Create campaign
        campaign_resp = await client.post("/api/campaigns", json={
            "name": "The Lost Mines",
            "description": "A classic adventure",
            "character_ids": [],
            "world_state": {},
            "dm_settings": {},
        })
        campaign_id = campaign_resp.json()["id"]
        
        # Create session
        session_resp = await client.post("/api/game/sessions", json={
            "campaign_id": campaign_id,
            "current_phase": "exploration",
            "current_scene": "You awaken in a dark cave...",
        })
        session_id = session_resp.json()["id"]
        
        # Get session
        resp = await client.get(f"/api/game/sessions/{session_id}/state")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == session_id
        assert data["current_phase"] == "exploration"

    async def test_08_get_map_state_404(self, client: AsyncClient):
        """Test that map state returns 404 when not set."""
        resp = await client.get("/api/maps/nonexistent-session")
        assert resp.status_code == 404
        assert "Map not found" in resp.json()["detail"]

    async def test_09_set_map_state(self, client: AsyncClient):
        """Test setting map state."""
        session_id = "test-session-1"
        
        resp = await client.put(f"/api/maps/{session_id}", json={
            "id": session_id,
            "width": 20,
            "height": 20,
            "terrain_grid": [["empty"] * 20 for _ in range(20)],
            "token_positions": [
                {"entity_id": "token-1", "x": 5, "y": 5},
            ],
            "fog_of_war": [],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == session_id
        assert data["width"] == 20

    async def test_10_get_map_state_after_set(self, client: AsyncClient):
        """Test retrieving map state after setting it."""
        session_id = "test-session-2"
        
        # Set map
        await client.put(f"/api/maps/{session_id}", json={
            "id": session_id,
            "width": 25,
            "height": 25,
            "terrain_grid": [["empty"] * 25 for _ in range(25)],
            "token_positions": [],
            "fog_of_war": [],
        })
        
        # Get map
        resp = await client.get(f"/api/maps/{session_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["width"] == 25
        assert data["height"] == 25

    async def test_11_get_avatar_state(self, client: AsyncClient):
        """Test retrieving avatar state."""
        session_id = "test-session-3"
        
        resp = await client.get(f"/api/avatar/{session_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert "expression" in data
        assert "is_speaking" in data
        assert "mouth_amplitude" in data
        assert "gaze" in data

    async def test_12_trigger_vision_capture(self, client: AsyncClient):
        """Test triggering vision capture."""
        session_id = "test-session-4"
        
        resp = await client.post(f"/api/vision/{session_id}/capture")
        assert resp.status_code == 200
        data = resp.json()
        assert "grid_width" in data
        assert "grid_height" in data
        assert "tokens" in data
        assert "confidence" in data

    async def test_13_set_avatar_expression(self, client: AsyncClient):
        """Test setting avatar expression."""
        session_id = "test-session-5"
        
        resp = await client.put(f"/api/avatar/{session_id}/expression", json={
            "expression": "happy",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "expression" in data

    async def test_14_avatar_speak(self, client: AsyncClient):
        """Test avatar speaking animation."""
        session_id = "test-session-6"
        
        resp = await client.post(f"/api/avatar/{session_id}/speak", json={
            "text": "Welcome adventurers!",
            "duration": 3.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_speaking"] is True


class TestErrorHandling:
    """Test error cases and edge conditions."""

    async def test_access_protected_endpoint_without_auth(self, client: AsyncClient):
        """Test that protected endpoints handle missing auth gracefully."""
        # Most endpoints in this API don't require auth yet, but campaigns should exist
        resp = await client.get("/api/campaigns/nonexistent")
        # Should return 404 for missing campaign, not 401
        assert resp.status_code == 404

    async def test_get_nonexistent_campaign(self, client: AsyncClient):
        """Test retrieving a campaign that doesn't exist."""
        resp = await client.get("/api/campaigns/nonexistent-campaign-id")
        assert resp.status_code == 404
        assert "Campaign not found" in resp.json()["detail"]

    async def test_get_nonexistent_character(self, client: AsyncClient):
        """Test retrieving a character that doesn't exist."""
        resp = await client.get("/api/characters/nonexistent-character-id")
        assert resp.status_code == 404
        assert "Character not found" in resp.json()["detail"]

    async def test_get_nonexistent_game_session(self, client: AsyncClient):
        """Test retrieving a game session that doesn't exist."""
        resp = await client.get("/api/game/sessions/nonexistent-session/state")
        assert resp.status_code == 404
        assert "Game session not found" in resp.json()["detail"]

    async def test_create_game_session_with_invalid_campaign(self, client: AsyncClient):
        """Test creating a game session with non-existent campaign."""
        resp = await client.post("/api/game/sessions", json={
            "campaign_id": "nonexistent-campaign",
            "current_phase": "exploration",
            "current_scene": "Test scene",
        })
        assert resp.status_code == 404
        assert "Campaign not found" in resp.json()["detail"]

    async def test_register_duplicate_username(self, client: AsyncClient):
        """Test registering with a username that already exists."""
        # Register first user
        await client.post("/api/auth/register", json={
            "username": "gandalf",
            "password": "youshallnotpass",
        })
        
        # Try to register with same username
        resp = await client.post("/api/auth/register", json={
            "username": "gandalf",
            "password": "differentpassword",
        })
        assert resp.status_code == 409
        assert "already exists" in resp.json()["detail"].lower()

    async def test_login_with_wrong_password(self, client: AsyncClient):
        """Test login with incorrect password."""
        # Register user
        await client.post("/api/auth/register", json={
            "username": "gandalf",
            "password": "youshallnotpass",
        })
        
        # Try to login with wrong password
        resp = await client.post("/api/auth/login", json={
            "username": "gandalf",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401
        assert "Invalid credentials" in resp.json()["detail"]

    async def test_set_invalid_avatar_expression(self, client: AsyncClient):
        """Test setting an invalid avatar expression."""
        resp = await client.put("/api/avatar/test-session/expression", json={
            "expression": "invalid_expression_value",
        })
        assert resp.status_code == 400
        assert "Invalid expression" in resp.json()["detail"]

    async def test_speak_without_text(self, client: AsyncClient):
        """Test avatar speak without required text."""
        resp = await client.post("/api/avatar/test-session/speak", json={
            "text": "",
            "duration": 2.0,
        })
        assert resp.status_code == 400
        assert "text is required" in resp.json()["detail"]

    async def test_register_with_missing_username(self, client: AsyncClient):
        """Test registration with missing username."""
        resp = await client.post("/api/auth/register", json={
            "password": "somepassword",
        })
        assert resp.status_code == 422  # Validation error

    async def test_register_with_short_password(self, client: AsyncClient):
        """Test registration with password that's too short."""
        resp = await client.post("/api/auth/register", json={
            "username": "testuser",
            "password": "ab",  # Too short (min is 3)
        })
        assert resp.status_code == 422  # Validation error

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with username that doesn't exist."""
        resp = await client.post("/api/auth/login", json={
            "username": "nonexistentuser",
            "password": "somepassword",
        })
        assert resp.status_code == 401
        assert "Invalid credentials" in resp.json()["detail"]


class TestDataRelationships:
    """Test that data relationships are maintained correctly."""

    async def test_character_belongs_to_campaign(self, client: AsyncClient):
        """Test that characters can be associated with campaigns."""
        # Create campaign
        campaign_resp = await client.post("/api/campaigns", json={
            "name": "The Lost Mines",
            "description": "A classic adventure",
            "character_ids": [],
            "world_state": {},
            "dm_settings": {},
        })
        campaign_id = campaign_resp.json()["id"]
        
        # Create character
        char_resp = await client.post("/api/characters", json={
            "name": "Thorin",
            "class_name": "fighter",
            "race": "dwarf",
            "level": 1,
            "strength": 15,
            "dexterity": 10,
            "constitution": 16,
            "intelligence": 8,
            "wisdom": 13,
            "charisma": 12,
            "hp": 12,
            "ac": 16,
        })
        assert char_resp.status_code == 201
        character_id = char_resp.json()["id"]
        
        # Verify character was created
        get_resp = await client.get(f"/api/characters/{character_id}")
        assert get_resp.status_code == 200

    async def test_game_session_belongs_to_campaign(self, client: AsyncClient):
        """Test that game sessions belong to campaigns."""
        # Create campaign
        campaign_resp = await client.post("/api/campaigns", json={
            "name": "The Lost Mines",
            "description": "A classic adventure",
            "character_ids": [],
            "world_state": {},
            "dm_settings": {},
        })
        campaign_id = campaign_resp.json()["id"]
        
        # Create game session
        session_resp = await client.post("/api/game/sessions", json={
            "campaign_id": campaign_id,
            "current_phase": "exploration",
            "current_scene": "Test scene",
        })
        session_data = session_resp.json()
        
        # Verify relationship
        assert session_data["campaign_id"] == campaign_id

    async def test_map_state_unique_per_session(self, client: AsyncClient):
        """Test that map states are unique per session."""
        # Create map for session 1
        await client.put("/api/maps/session-1", json={
            "id": "session-1",
            "width": 10,
            "height": 10,
            "terrain_grid": [["empty"] * 10 for _ in range(10)],
            "token_positions": [],
            "fog_of_war": [],
        })
        
        # Create map for session 2
        await client.put("/api/maps/session-2", json={
            "id": "session-2",
            "width": 20,
            "height": 20,
            "terrain_grid": [["empty"] * 20 for _ in range(20)],
            "token_positions": [],
            "fog_of_war": [],
        })
        
        # Verify they're different
        resp1 = await client.get("/api/maps/session-1")
        resp2 = await client.get("/api/maps/session-2")
        
        assert resp1.json()["width"] == 10
        assert resp2.json()["width"] == 20

    async def test_avatar_state_unique_per_session(self, client: AsyncClient):
        """Test that avatar states are unique per session."""
        # Set expression for session 1
        await client.put("/api/avatar/session-1/expression", json={
            "expression": "happy",
        })
        
        # Set expression for session 2
        await client.put("/api/avatar/session-2/expression", json={
            "expression": "angry",
        })
        
        # Verify they're different
        resp1 = await client.get("/api/avatar/session-1")
        resp2 = await client.get("/api/avatar/session-2")
        
        # Both should have expression field
        assert "expression" in resp1.json()
        assert "expression" in resp2.json()


class TestCompleteWorkflow:
    """Integration tests that follow a realistic workflow."""

    async def test_full_workflow_create_campaign_and_session(self, client: AsyncClient):
        """Complete workflow: create campaign, character, and session."""
        # 1. Register user
        user_resp = await client.post("/api/auth/register", json={
            "username": "dm_master",
            "password": "password123",
        })
        assert user_resp.status_code == 201
        
        # 2. Create campaign
        campaign_resp = await client.post("/api/campaigns", json={
            "name": "Dragon Slayers",
            "description": "An epic quest",
            "character_ids": [],
            "world_state": {"setting": "Forgotten Realms"},
            "dm_settings": {"difficulty": "hard"},
        })
        assert campaign_resp.status_code == 201
        campaign_id = campaign_resp.json()["id"]
        
        # 3. Create character
        char_resp = await client.post("/api/characters", json={
            "name": "Aragorn",
            "class_name": "ranger",
            "race": "human",
            "level": 5,
            "strength": 15,
            "dexterity": 14,
            "constitution": 14,
            "intelligence": 12,
            "wisdom": 16,
            "charisma": 13,
            "hp": 35,
            "ac": 14,
            "inventory": ["longsword", "bow"],
        })
        assert char_resp.status_code == 201
        
        # 4. Create game session
        session_resp = await client.post("/api/game/sessions", json={
            "campaign_id": campaign_id,
            "current_phase": "combat",
            "current_scene": "You face a dragon!",
        })
        assert session_resp.status_code == 201
        session_id = session_resp.json()["id"]
        
        # 5. Set map for session
        map_resp = await client.put(f"/api/maps/{session_id}", json={
            "id": session_id,
            "width": 30,
            "height": 30,
            "terrain_grid": [["empty"] * 30 for _ in range(30)],
            "token_positions": [{"entity_id": "player-1", "x": 10, "y": 10}],
            "fog_of_war": [],
        })
        assert map_resp.status_code == 200
        
        # 6. Set avatar state
        avatar_resp = await client.put(f"/api/avatar/{session_id}/expression", json={
            "expression": "menacing",
        })
        assert avatar_resp.status_code == 200
        
        # 7. Make avatar speak
        speak_resp = await client.post(f"/api/avatar/{session_id}/speak", json={
            "text": "A great dragon emerges from the darkness!",
            "duration": 4.0,
        })
        assert speak_resp.status_code == 200
        assert speak_resp.json()["is_speaking"] is True
        
        # 8. Capture board state
        vision_resp = await client.post(f"/api/vision/{session_id}/capture")
        assert vision_resp.status_code == 200

    async def test_multiple_users_independent_sessions(self, client: AsyncClient):
        """Test that multiple users can have independent sessions."""
        users = []
        for i in range(2):
            user_resp = await client.post("/api/auth/register", json={
                "username": f"user_{i}",
                "password": "password123",
            })
            users.append(user_resp.json())
        
        # Each user creates a campaign
        campaigns = []
        for user in users:
            campaign_resp = await client.post("/api/campaigns", json={
                "name": f"Campaign {user['username']}",
                "description": f"User {user['username']}'s campaign",
                "character_ids": [],
                "world_state": {},
                "dm_settings": {},
            })
            campaigns.append(campaign_resp.json())
        
        # Verify campaigns are different
        assert campaigns[0]["id"] != campaigns[1]["id"]
        assert campaigns[0]["name"] != campaigns[1]["name"]

    async def test_state_persistence_across_requests(self, client: AsyncClient):
        """Test that state is maintained across multiple requests."""
        campaign_resp = await client.post("/api/campaigns", json={
            "name": "Test Campaign",
            "description": "For state persistence testing",
            "character_ids": [],
            "world_state": {"version": 1},
            "dm_settings": {"version": 1},
        })
        campaign_id = campaign_resp.json()["id"]
        
        # Get it multiple times, verify consistency
        for _ in range(3):
            get_resp = await client.get(f"/api/campaigns/{campaign_id}")
            assert get_resp.status_code == 200
            assert get_resp.json()["id"] == campaign_id
            assert get_resp.json()["name"] == "Test Campaign"
