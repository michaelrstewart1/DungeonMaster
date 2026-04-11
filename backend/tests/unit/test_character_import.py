"""Unit tests for character import parsing logic."""
import pytest

from app.api.routes.characters import _parse_r20_data, _parse_generic_data


class TestParseR20Data:
    """Tests for r20Exporter JSON parsing."""

    def test_parse_valid_r20_data(self):
        """Parse a complete r20 export with all fields."""
        data = {
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
        }
        result = _parse_r20_data(data)
        assert result["name"] == "Thorin"
        assert result["strength"] == 18
        assert result["dexterity"] == 12
        assert result["constitution"] == 16
        assert result["intelligence"] == 10
        assert result["wisdom"] == 13
        assert result["charisma"] == 8
        assert result["class_name"] == "fighter"
        assert result["level"] == 5
        assert result["race"] == "dwarf"
        assert result["hp"] == 45
        assert result["ac"] == 18

    def test_parse_r20_missing_attributes_uses_no_overrides(self):
        """Missing attribs should not appear in result (defaults come from schema)."""
        data = {
            "name": "Minimal",
            "attribs": [
                {"name": "base_level", "current": "Wizard 1", "max": ""},
                {"name": "race", "current": "Elf", "max": ""},
            ],
        }
        result = _parse_r20_data(data)
        assert result["name"] == "Minimal"
        assert result["class_name"] == "wizard"
        assert result["level"] == 1
        assert result["race"] == "elf"
        assert "strength" not in result
        assert "hp" not in result

    def test_parse_r20_fighter_5(self):
        """Parse 'Fighter 5' class/level format."""
        data = {
            "name": "Test",
            "attribs": [
                {"name": "base_level", "current": "Fighter 5", "max": ""},
                {"name": "race", "current": "Human", "max": ""},
            ],
        }
        result = _parse_r20_data(data)
        assert result["class_name"] == "fighter"
        assert result["level"] == 5

    def test_parse_r20_wizard_10(self):
        """Parse 'Wizard 10' class/level format."""
        data = {
            "name": "Test",
            "attribs": [
                {"name": "base_level", "current": "Wizard 10", "max": ""},
                {"name": "race", "current": "Human", "max": ""},
            ],
        }
        result = _parse_r20_data(data)
        assert result["class_name"] == "wizard"
        assert result["level"] == 10

    def test_parse_r20_rogue_1(self):
        """Parse 'Rogue 1' class/level format."""
        data = {
            "name": "Test",
            "attribs": [
                {"name": "base_level", "current": "Rogue 1", "max": ""},
                {"name": "race", "current": "Human", "max": ""},
            ],
        }
        result = _parse_r20_data(data)
        assert result["class_name"] == "rogue"
        assert result["level"] == 1

    def test_parse_r20_race_normalization(self):
        """Race names should be lowercased."""
        data = {
            "name": "Test",
            "attribs": [
                {"name": "race", "current": "Half-Elf", "max": ""},
                {"name": "base_level", "current": "Bard 3", "max": ""},
            ],
        }
        result = _parse_r20_data(data)
        assert result["race"] == "half-elf"

    def test_parse_r20_class_normalization(self):
        """Class names should be lowercased."""
        data = {
            "name": "Test",
            "attribs": [
                {"name": "base_level", "current": "PALADIN 7", "max": ""},
                {"name": "race", "current": "DRAGONBORN", "max": ""},
            ],
        }
        result = _parse_r20_data(data)
        assert result["class_name"] == "paladin"
        assert result["race"] == "dragonborn"

    def test_parse_r20_missing_name_defaults(self):
        """Missing name should default to 'Unknown'."""
        data = {
            "attribs": [
                {"name": "base_level", "current": "Fighter 1", "max": ""},
                {"name": "race", "current": "Human", "max": ""},
            ],
        }
        result = _parse_r20_data(data)
        assert result["name"] == "Unknown"

    def test_parse_r20_empty_attribs(self):
        """Empty attribs list should still return name."""
        data = {"name": "Empty", "attribs": []}
        result = _parse_r20_data(data)
        assert result["name"] == "Empty"


class TestParseGenericData:
    """Tests for generic flat JSON parsing."""

    def test_parse_generic_data(self):
        """Generic format should pass through fields directly."""
        data = {
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
        }
        result = _parse_generic_data(data)
        assert result["name"] == "Gandalf"
        assert result["race"] == "human"
        assert result["class_name"] == "wizard"
        assert result["level"] == 5
        assert result["intelligence"] == 20

    def test_parse_generic_race_normalization(self):
        """Race should be lowercased in generic format."""
        data = {
            "name": "Test",
            "race": "Half-Orc",
            "class_name": "barbarian",
            "level": 1,
        }
        result = _parse_generic_data(data)
        assert result["race"] == "half-orc"

    def test_parse_generic_class_normalization(self):
        """Class name should be lowercased in generic format."""
        data = {
            "name": "Test",
            "race": "human",
            "class_name": "Sorcerer",
            "level": 1,
        }
        result = _parse_generic_data(data)
        assert result["class_name"] == "sorcerer"
