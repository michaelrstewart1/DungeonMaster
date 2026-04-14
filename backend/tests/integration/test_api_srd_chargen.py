"""Integration tests for SRD character generation endpoints."""
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


class TestSubraceEndpoints:
    """Tests for GET /api/srd/chargen/subraces"""

    async def test_list_all_subraces(self, client: AsyncClient):
        """Listing subraces should return a non-empty list."""
        response = await client.get("/api/srd/chargen/subraces")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 5  # At least dwarf, elf, halfling, gnome, dragonborn subraces

    async def test_subraces_have_required_fields(self, client: AsyncClient):
        """Each subrace should have name and parent_race."""
        response = await client.get("/api/srd/chargen/subraces")
        data = response.json()
        for subrace in data:
            assert "name" in subrace
            assert "parent_race" in subrace
            assert isinstance(subrace["name"], str)
            assert len(subrace["name"]) > 0

    async def test_subraces_have_optional_fields(self, client: AsyncClient):
        """Subraces should include ability_bonuses and traits."""
        response = await client.get("/api/srd/chargen/subraces")
        data = response.json()
        assert len(data) > 0
        first = data[0]
        assert "ability_bonuses" in first
        assert "traits" in first
        assert isinstance(first["ability_bonuses"], dict)
        assert isinstance(first["traits"], list)

    async def test_filter_subraces_by_race_dwarf(self, client: AsyncClient):
        """Filtering subraces by race=dwarf should return only dwarf subraces."""
        response = await client.get("/api/srd/chargen/subraces?race=dwarf")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Hill Dwarf, Mountain Dwarf
        for subrace in data:
            assert subrace["parent_race"].lower() == "dwarf"

    async def test_filter_subraces_by_race_elf(self, client: AsyncClient):
        """Filtering subraces by race=elf should return only elf subraces."""
        response = await client.get("/api/srd/chargen/subraces?race=elf")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2  # High Elf, Wood Elf (+ possibly Drow)
        for subrace in data:
            assert subrace["parent_race"].lower() == "elf"

    async def test_filter_subraces_by_nonexistent_race(self, client: AsyncClient):
        """Filtering by a race with no subraces should return empty list."""
        response = await client.get("/api/srd/chargen/subraces?race=nonexistent")
        assert response.status_code == 200
        assert response.json() == []

    async def test_filter_subraces_case_insensitive(self, client: AsyncClient):
        """Race filter should be case-insensitive."""
        response_lower = await client.get("/api/srd/chargen/subraces?race=dwarf")
        response_upper = await client.get("/api/srd/chargen/subraces?race=Dwarf")
        assert response_lower.json() == response_upper.json()


class TestSubclassEndpoints:
    """Tests for GET /api/srd/chargen/subclasses"""

    async def test_list_all_subclasses(self, client: AsyncClient):
        """Listing subclasses should return a non-empty list."""
        response = await client.get("/api/srd/chargen/subclasses")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 10  # At least one per class

    async def test_subclasses_have_required_fields(self, client: AsyncClient):
        """Each subclass should have name, parent_class, and subclass_level."""
        response = await client.get("/api/srd/chargen/subclasses")
        data = response.json()
        for subclass in data:
            assert "name" in subclass
            assert "parent_class" in subclass
            assert "subclass_level" in subclass
            assert isinstance(subclass["subclass_level"], int)
            assert subclass["subclass_level"] >= 1

    async def test_subclasses_have_features(self, client: AsyncClient):
        """Subclasses should include features list."""
        response = await client.get("/api/srd/chargen/subclasses")
        data = response.json()
        # At least some subclasses should have features
        has_features = [sc for sc in data if sc.get("features")]
        assert len(has_features) > 0

    async def test_filter_subclasses_by_fighter(self, client: AsyncClient):
        """Filtering subclasses by class_name=fighter should return fighter subclasses."""
        response = await client.get("/api/srd/chargen/subclasses?class_name=fighter")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1  # At least Champion
        for subclass in data:
            assert subclass["parent_class"].lower() == "fighter"

    async def test_filter_subclasses_by_nonexistent_class(self, client: AsyncClient):
        """Filtering by a nonexistent class should return empty list."""
        response = await client.get("/api/srd/chargen/subclasses?class_name=nonexistent")
        assert response.status_code == 200
        assert response.json() == []

    async def test_filter_subclasses_case_insensitive(self, client: AsyncClient):
        """Class filter should be case-insensitive."""
        response_lower = await client.get("/api/srd/chargen/subclasses?class_name=fighter")
        response_upper = await client.get("/api/srd/chargen/subclasses?class_name=Fighter")
        assert response_lower.json() == response_upper.json()


class TestBackgroundEndpoints:
    """Tests for GET /api/srd/chargen/backgrounds"""

    async def test_list_backgrounds(self, client: AsyncClient):
        """Listing backgrounds should return a non-empty list."""
        response = await client.get("/api/srd/chargen/backgrounds")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 5  # SRD has multiple backgrounds

    async def test_backgrounds_have_required_fields(self, client: AsyncClient):
        """Each background should have name and skill_proficiencies."""
        response = await client.get("/api/srd/chargen/backgrounds")
        data = response.json()
        for bg in data:
            assert "name" in bg
            assert "skill_proficiencies" in bg
            assert isinstance(bg["skill_proficiencies"], list)
            assert len(bg["skill_proficiencies"]) > 0

    async def test_backgrounds_have_optional_fields(self, client: AsyncClient):
        """Backgrounds should include equipment, feature, and personality options."""
        response = await client.get("/api/srd/chargen/backgrounds")
        data = response.json()
        first = data[0]
        assert "equipment" in first
        assert "feature_name" in first
        assert "feature_description" in first
        assert "personality_traits" in first
        assert "ideals" in first
        assert "bonds" in first
        assert "flaws" in first

    async def test_acolyte_background_present(self, client: AsyncClient):
        """The Acolyte background (SRD standard) should be present."""
        response = await client.get("/api/srd/chargen/backgrounds")
        data = response.json()
        names = [bg["name"].lower() for bg in data]
        assert "acolyte" in names


class TestSkillEndpoints:
    """Tests for GET /api/srd/chargen/skills"""

    async def test_list_skills(self, client: AsyncClient):
        """Listing skills should return exactly 18 D&D 5e skills."""
        response = await client.get("/api/srd/chargen/skills")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 18

    async def test_skills_have_required_fields(self, client: AsyncClient):
        """Each skill should have name and ability."""
        response = await client.get("/api/srd/chargen/skills")
        data = response.json()
        for skill in data:
            assert "name" in skill
            assert "ability" in skill
            assert isinstance(skill["name"], str)
            assert isinstance(skill["ability"], str)

    async def test_skills_include_known_skills(self, client: AsyncClient):
        """Skills should include well-known D&D 5e skills."""
        response = await client.get("/api/srd/chargen/skills")
        data = response.json()
        skill_names = {s["name"].lower() for s in data}
        expected = {"athletics", "acrobatics", "stealth", "perception", "arcana", "persuasion"}
        assert expected.issubset(skill_names)

    async def test_skills_mapped_to_correct_abilities(self, client: AsyncClient):
        """Skills should be associated with correct ability scores."""
        response = await client.get("/api/srd/chargen/skills")
        data = response.json()
        skill_map = {s["name"].lower(): s["ability"].upper() for s in data}
        # Verify some well-known mappings (uses abbreviated ability names)
        assert skill_map.get("athletics") == "STR"
        assert skill_map.get("acrobatics") == "DEX"
        assert skill_map.get("arcana") == "INT"
        assert skill_map.get("perception") == "WIS"
        assert skill_map.get("persuasion") == "CHA"


class TestFeatEndpoints:
    """Tests for GET /api/srd/chargen/feats"""

    async def test_list_feats(self, client: AsyncClient):
        """Listing feats should return a list (may be empty if data not loaded)."""
        response = await client.get("/api/srd/chargen/feats")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_feats_structure_if_present(self, client: AsyncClient):
        """If feats are returned, each should have name and description."""
        response = await client.get("/api/srd/chargen/feats")
        data = response.json()
        for feat in data:
            assert "name" in feat
            assert "description" in feat
