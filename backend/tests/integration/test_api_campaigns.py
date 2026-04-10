"""Integration tests for campaign CRUD endpoints."""
import pytest
from httpx import AsyncClient


class TestCampaignCreate:
    """Tests for POST /api/campaigns"""

    async def test_create_campaign_returns_201(self, client: AsyncClient):
        """Creating a campaign should return 201 with campaign data."""
        response = await client.post(
            "/api/campaigns",
            json={
                "name": "The Lost Mines",
                "description": "A campaign in the Lost Mines of Phandelver",
                "character_ids": [],
                "world_state": {},
                "dm_settings": {},
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "The Lost Mines"
        assert data["description"] == "A campaign in the Lost Mines of Phandelver"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_campaign_with_empty_name_returns_422(self, client: AsyncClient):
        """Creating a campaign with empty name should return 422."""
        response = await client.post(
            "/api/campaigns",
            json={
                "name": "",
                "description": "A campaign",
                "character_ids": [],
                "world_state": {},
                "dm_settings": {},
            },
        )
        assert response.status_code == 422

    async def test_create_campaign_with_character_ids(self, client: AsyncClient):
        """Creating a campaign with character IDs should work."""
        response = await client.post(
            "/api/campaigns",
            json={
                "name": "Dragon Heist",
                "description": "A campaign in Waterdeep",
                "character_ids": ["char1", "char2"],
                "world_state": {"location": "Waterdeep"},
                "dm_settings": {"difficulty": "hard"},
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["character_ids"] == ["char1", "char2"]
        assert data["world_state"]["location"] == "Waterdeep"
        assert data["dm_settings"]["difficulty"] == "hard"


class TestCampaignList:
    """Tests for GET /api/campaigns"""

    async def test_list_campaigns_empty(self, client: AsyncClient):
        """Listing campaigns when none exist should return empty list."""
        response = await client.get("/api/campaigns")
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_campaigns_returns_all(self, client: AsyncClient):
        """Listing campaigns should return all campaigns."""
        # Create two campaigns
        await client.post(
            "/api/campaigns",
            json={
                "name": "Campaign 1",
                "description": "First campaign",
                "character_ids": [],
                "world_state": {},
                "dm_settings": {},
            },
        )
        await client.post(
            "/api/campaigns",
            json={
                "name": "Campaign 2",
                "description": "Second campaign",
                "character_ids": [],
                "world_state": {},
                "dm_settings": {},
            },
        )

        response = await client.get("/api/campaigns")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Campaign 1"
        assert data[1]["name"] == "Campaign 2"


class TestCampaignGet:
    """Tests for GET /api/campaigns/{id}"""

    async def test_get_campaign_returns_200(self, client: AsyncClient):
        """Getting an existing campaign should return 200."""
        create_response = await client.post(
            "/api/campaigns",
            json={
                "name": "Test Campaign",
                "description": "A test campaign",
                "character_ids": [],
                "world_state": {},
                "dm_settings": {},
            },
        )
        campaign_id = create_response.json()["id"]

        response = await client.get(f"/api/campaigns/{campaign_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Campaign"
        assert data["id"] == campaign_id

    async def test_get_campaign_not_found_returns_404(self, client: AsyncClient):
        """Getting a non-existent campaign should return 404."""
        response = await client.get("/api/campaigns/nonexistent-id")
        assert response.status_code == 404


class TestCampaignUpdate:
    """Tests for PUT /api/campaigns/{id}"""

    async def test_update_campaign_returns_200(self, client: AsyncClient):
        """Updating an existing campaign should return 200."""
        create_response = await client.post(
            "/api/campaigns",
            json={
                "name": "Original Name",
                "description": "Original description",
                "character_ids": [],
                "world_state": {},
                "dm_settings": {},
            },
        )
        campaign_id = create_response.json()["id"]

        response = await client.put(
            f"/api/campaigns/{campaign_id}",
            json={
                "name": "Updated Name",
                "description": "Updated description",
                "character_ids": ["char1"],
                "world_state": {"location": "New Location"},
                "dm_settings": {"difficulty": "medium"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "Updated description"
        assert data["character_ids"] == ["char1"]
        assert data["world_state"]["location"] == "New Location"

    async def test_update_campaign_not_found_returns_404(self, client: AsyncClient):
        """Updating a non-existent campaign should return 404."""
        response = await client.put(
            "/api/campaigns/nonexistent-id",
            json={
                "name": "Updated Name",
                "description": "Updated",
                "character_ids": [],
                "world_state": {},
                "dm_settings": {},
            },
        )
        assert response.status_code == 404


class TestCampaignDelete:
    """Tests for DELETE /api/campaigns/{id}"""

    async def test_delete_campaign_returns_204(self, client: AsyncClient):
        """Deleting an existing campaign should return 204."""
        create_response = await client.post(
            "/api/campaigns",
            json={
                "name": "Campaign to Delete",
                "description": "Will be deleted",
                "character_ids": [],
                "world_state": {},
                "dm_settings": {},
            },
        )
        campaign_id = create_response.json()["id"]

        response = await client.delete(f"/api/campaigns/{campaign_id}")
        assert response.status_code == 204

        # Verify it's actually deleted
        get_response = await client.get(f"/api/campaigns/{campaign_id}")
        assert get_response.status_code == 404

    async def test_delete_campaign_not_found_returns_404(self, client: AsyncClient):
        """Deleting a non-existent campaign should return 404."""
        response = await client.delete("/api/campaigns/nonexistent-id")
        assert response.status_code == 404
