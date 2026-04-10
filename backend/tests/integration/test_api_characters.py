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
