"""Integration tests for character import endpoint."""
import pytest
from httpx import AsyncClient


class TestCharacterImportR20:
    """Tests for POST /api/characters/import with r20 format."""

    async def test_import_r20_character(self, client: AsyncClient):
        """Importing a valid r20 character should return 201."""
        response = await client.post(
            "/api/characters/import",
            json={
                "format": "r20",
                "data": {
                    "name": "Thorin",
                    "attribs": [
                        {"name": "strength", "current": "18", "max": ""},
                        {"name": "dexterity", "current": "12", "max": ""},
                        {"name": "constitution", "current": "16", "max": ""},
                        {"name": "intelligence", "current": "10", "max": ""},
                        {"name": "wisdom", "current": "13", "max": ""},
                        {"name": "charisma", "current": "8", "max": ""},
                        {"name": "base_level", "current": "Fighter 5", "max": ""},
                        {"name": "race", "current": "Dwarf", "max": ""},
                        {"name": "hp", "current": "45", "max": "45"},
                        {"name": "ac", "current": "18", "max": ""},
                    ],
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Thorin"
        assert data["race"] == "dwarf"
        assert data["class_name"] == "fighter"
        assert data["level"] == 5
        assert data["strength"] == 18
        assert data["hp"] == 45
        assert data["ac"] == 18
        assert "id" in data

    async def test_import_r20_with_defaults(self, client: AsyncClient):
        """r20 import with missing ability scores uses defaults."""
        response = await client.post(
            "/api/characters/import",
            json={
                "format": "r20",
                "data": {
                    "name": "Minimal",
                    "attribs": [
                        {"name": "base_level", "current": "Wizard 1", "max": ""},
                        {"name": "race", "current": "Elf", "max": ""},
                    ],
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal"
        assert data["strength"] == 10  # default
        assert data["hp"] == 8  # default

    async def test_import_r20_character_persists(self, client: AsyncClient):
        """Imported character should be retrievable via GET."""
        response = await client.post(
            "/api/characters/import",
            json={
                "format": "r20",
                "data": {
                    "name": "Persisted",
                    "attribs": [
                        {"name": "base_level", "current": "Rogue 3", "max": ""},
                        {"name": "race", "current": "Halfling", "max": ""},
                    ],
                },
            },
        )
        assert response.status_code == 201
        char_id = response.json()["id"]

        get_response = await client.get(f"/api/characters/{char_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "Persisted"


class TestCharacterImportGeneric:
    """Tests for POST /api/characters/import with generic format."""

    async def test_import_generic_character(self, client: AsyncClient):
        """Importing a valid generic character should return 201."""
        response = await client.post(
            "/api/characters/import",
            json={
                "format": "generic",
                "data": {
                    "name": "Gandalf",
                    "race": "human",
                    "class_name": "wizard",
                    "level": 5,
                    "strength": 10,
                    "dexterity": 14,
                    "constitution": 12,
                    "intelligence": 20,
                    "wisdom": 18,
                    "charisma": 16,
                    "hp": 32,
                    "ac": 12,
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Gandalf"
        assert data["race"] == "human"
        assert data["class_name"] == "wizard"
        assert data["level"] == 5
        assert "id" in data

    async def test_import_generic_normalizes_case(self, client: AsyncClient):
        """Generic import should normalize race and class case."""
        response = await client.post(
            "/api/characters/import",
            json={
                "format": "generic",
                "data": {
                    "name": "CaseyTest",
                    "race": "Half-Orc",
                    "class_name": "Barbarian",
                    "level": 1,
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["race"] == "half-orc"
        assert data["class_name"] == "barbarian"


class TestCharacterImportErrors:
    """Tests for error handling in character import."""

    async def test_invalid_format_returns_422(self, client: AsyncClient):
        """Invalid format should return 422."""
        response = await client.post(
            "/api/characters/import",
            json={
                "format": "unknown_format",
                "data": {"name": "Test"},
            },
        )
        assert response.status_code == 422

    async def test_missing_format_returns_422(self, client: AsyncClient):
        """Missing format field should return 422."""
        response = await client.post(
            "/api/characters/import",
            json={
                "data": {"name": "Test"},
            },
        )
        assert response.status_code == 422

    async def test_r20_invalid_race_returns_422(self, client: AsyncClient):
        """r20 import with invalid race should return 422."""
        response = await client.post(
            "/api/characters/import",
            json={
                "format": "r20",
                "data": {
                    "name": "Bad",
                    "attribs": [
                        {"name": "base_level", "current": "Fighter 1", "max": ""},
                        {"name": "race", "current": "Dragon", "max": ""},
                    ],
                },
            },
        )
        assert response.status_code == 422
