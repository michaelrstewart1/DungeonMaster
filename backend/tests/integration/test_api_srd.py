"""
Integration tests for SRD API endpoints.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import create_app


@pytest.fixture
async def client():
    """Provide an AsyncClient for testing the API."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestSpellEndpoints:
    """Test spell API endpoints."""

    async def test_get_spell_by_name(self, client):
        """Test GET /api/srd/spells/{name}"""
        response = await client.get("/api/srd/spells/fireball")
        assert response.status_code == 200
        data = response.json()
        assert data["name"].lower() == "fireball"
        assert data["level"] == 3
        assert "school" in data

    async def test_get_spell_not_found(self, client):
        """Test GET /api/srd/spells/{name} with nonexistent spell."""
        response = await client.get("/api/srd/spells/nonexistent")
        assert response.status_code == 404

    async def test_list_all_spells(self, client):
        """Test GET /api/srd/spells"""
        response = await client.get("/api/srd/spells")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 20

    async def test_search_spells_by_query(self, client):
        """Test GET /api/srd/spells?q=ball"""
        response = await client.get("/api/srd/spells?q=ball")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert any("ball" in spell["name"].lower() for spell in data)

    async def test_search_spells_by_level(self, client):
        """Test GET /api/srd/spells?level=3"""
        response = await client.get("/api/srd/spells?level=3")
        assert response.status_code == 200
        data = response.json()
        assert all(spell["level"] == 3 for spell in data)

    async def test_search_spells_by_class(self, client):
        """Test GET /api/srd/spells?class_name=Wizard"""
        response = await client.get("/api/srd/spells?class_name=Wizard")
        assert response.status_code == 200
        data = response.json()
        assert all("Wizard" in spell["classes"] for spell in data)


class TestMonsterEndpoints:
    """Test monster API endpoints."""

    async def test_get_monster_by_name(self, client):
        """Test GET /api/srd/monsters/{name}"""
        response = await client.get("/api/srd/monsters/goblin")
        assert response.status_code == 200
        data = response.json()
        assert data["name"].lower() == "goblin"
        assert "ac" in data
        assert "hp" in data

    async def test_get_monster_not_found(self, client):
        """Test GET /api/srd/monsters/{name} with nonexistent monster."""
        response = await client.get("/api/srd/monsters/nonexistent")
        assert response.status_code == 404

    async def test_list_all_monsters(self, client):
        """Test GET /api/srd/monsters"""
        response = await client.get("/api/srd/monsters")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 15

    async def test_search_monsters_by_query(self, client):
        """Test GET /api/srd/monsters?q=dragon"""
        response = await client.get("/api/srd/monsters?q=dragon")
        assert response.status_code == 200
        data = response.json()
        assert any("dragon" in monster["name"].lower() for monster in data)

    async def test_search_monsters_by_cr(self, client):
        """Test GET /api/srd/monsters?cr_min=0&cr_max=1"""
        response = await client.get("/api/srd/monsters?cr_min=0&cr_max=1")
        assert response.status_code == 200
        data = response.json()
        assert all(0 <= monster["challenge_rating"] <= 1 for monster in data)


class TestEquipmentEndpoints:
    """Test equipment API endpoints."""

    async def test_get_equipment_by_name(self, client):
        """Test GET /api/srd/equipment/{name}"""
        response = await client.get("/api/srd/equipment/longsword")
        assert response.status_code == 200
        data = response.json()
        assert data["name"].lower() == "longsword"
        assert "category" in data

    async def test_get_equipment_not_found(self, client):
        """Test GET /api/srd/equipment/{name} with nonexistent item."""
        response = await client.get("/api/srd/equipment/nonexistent")
        assert response.status_code == 404

    async def test_list_all_equipment(self, client):
        """Test GET /api/srd/equipment"""
        response = await client.get("/api/srd/equipment")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 15

    async def test_search_equipment_by_query(self, client):
        """Test GET /api/srd/equipment?q=sword"""
        response = await client.get("/api/srd/equipment?q=sword")
        assert response.status_code == 200
        data = response.json()
        assert any("sword" in item["name"].lower() for item in data)

    async def test_search_equipment_by_category(self, client):
        """Test GET /api/srd/equipment?category=Weapons"""
        response = await client.get("/api/srd/equipment?category=Weapons")
        assert response.status_code == 200
        data = response.json()
        assert all(item["category"] == "Weapons" for item in data)


class TestClassEndpoints:
    """Test class API endpoints."""

    async def test_get_class_by_name(self, client):
        """Test GET /api/srd/classes/{name}"""
        response = await client.get("/api/srd/classes/wizard")
        assert response.status_code == 200
        data = response.json()
        assert data["name"].lower() == "wizard"
        assert "hit_die" in data

    async def test_get_class_not_found(self, client):
        """Test GET /api/srd/classes/{name} with nonexistent class."""
        response = await client.get("/api/srd/classes/nonexistent")
        assert response.status_code == 404

    async def test_list_all_classes(self, client):
        """Test GET /api/srd/classes"""
        response = await client.get("/api/srd/classes")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 12


class TestRaceEndpoints:
    """Test race API endpoints."""

    async def test_get_race_by_name(self, client):
        """Test GET /api/srd/races/{name}"""
        response = await client.get("/api/srd/races/human")
        assert response.status_code == 200
        data = response.json()
        assert data["name"].lower() == "human"
        assert "speed" in data

    async def test_get_race_not_found(self, client):
        """Test GET /api/srd/races/{name} with nonexistent race."""
        response = await client.get("/api/srd/races/nonexistent")
        assert response.status_code == 404

    async def test_list_all_races(self, client):
        """Test GET /api/srd/races"""
        response = await client.get("/api/srd/races")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 5
