"""
Tests for SRD data completeness and model validation.
"""
import pytest
from app.services.srd.data import (
    SRDSpell,
    SRDMonster,
    SRDEquipment,
    SRDClass,
    SRDRace,
    srd_spells,
    srd_monsters,
    srd_equipment,
    srd_classes,
    srd_races,
)


class TestSRDSpellModel:
    """Test SRDSpell Pydantic model validation."""

    def test_spell_creation_with_all_fields(self):
        spell = SRDSpell(
            name="Fireball",
            level=3,
            school="Evocation",
            casting_time="1 action",
            range="150 feet",
            components=["V", "S", "M"],
            duration="Instantaneous",
            description="A bright streak flashes from your pointing finger to a point...",
            classes=["Sorcerer", "Wizard"],
        )
        assert spell.name == "Fireball"
        assert spell.level == 3
        assert spell.school == "Evocation"
        assert len(spell.classes) == 2

    def test_spell_level_bounds(self):
        """Test spell level validation (0-9)."""
        spell = SRDSpell(
            name="Test",
            level=0,
            school="Test",
            casting_time="1 action",
            range="Self",
            components=[],
            duration="1 minute",
            description="Test",
            classes=[],
        )
        assert spell.level == 0

        with pytest.raises(ValueError):
            SRDSpell(
                name="Test",
                level=10,
                school="Test",
                casting_time="1 action",
                range="Self",
                components=[],
                duration="1 minute",
                description="Test",
                classes=[],
            )


class TestSRDMonsterModel:
    """Test SRDMonster Pydantic model validation."""

    def test_monster_creation_with_all_fields(self):
        monster = SRDMonster(
            name="Goblin",
            size="Small",
            type="Humanoid",
            alignment="Chaotic Evil",
            ac=15,
            hp=7,
            speed="30 ft.",
            strength=8,
            dexterity=14,
            constitution=10,
            intelligence=10,
            wisdom=8,
            charisma=8,
            challenge_rating=0.25,
            actions="Scimitar. Melee Weapon Attack: +4 to hit...",
        )
        assert monster.name == "Goblin"
        assert monster.size == "Small"
        assert monster.ac == 15
        assert monster.hp == 7

    def test_monster_ability_scores_valid(self):
        """Test that ability scores are 1-20."""
        monster = SRDMonster(
            name="Test",
            size="Medium",
            type="Test",
            alignment="Neutral",
            ac=10,
            hp=1,
            speed="30 ft.",
            strength=1,
            dexterity=20,
            constitution=10,
            intelligence=10,
            wisdom=10,
            charisma=10,
            challenge_rating=0,
            actions="Test",
        )
        assert monster.strength == 1
        assert monster.dexterity == 20


class TestSRDEquipmentModel:
    """Test SRDEquipment Pydantic model validation."""

    def test_equipment_creation_with_all_fields(self):
        equipment = SRDEquipment(
            name="Longsword",
            category="Weapons",
            cost="15 gp",
            weight=3.0,
            properties="Versatile",
        )
        assert equipment.name == "Longsword"
        assert equipment.category == "Weapons"
        assert equipment.cost == "15 gp"


class TestSRDClassModel:
    """Test SRDClass Pydantic model validation."""

    def test_class_creation_with_all_fields(self):
        cls = SRDClass(
            name="Wizard",
            hit_die=6,
            primary_ability="Intelligence",
            saving_throws=["Intelligence", "Wisdom"],
            proficiencies=["daggers", "darts", "slings", "quarterstaffs"],
        )
        assert cls.name == "Wizard"
        assert cls.hit_die == 6
        assert cls.primary_ability == "Intelligence"


class TestSRDRaceModel:
    """Test SRDRace Pydantic model validation."""

    def test_race_creation_with_all_fields(self):
        race = SRDRace(
            name="Human",
            speed=30,
            size="Medium",
            ability_bonuses={"Strength": 1, "Intelligence": 1},
            traits=["Languages"],
        )
        assert race.name == "Human"
        assert race.speed == 30
        assert race.size == "Medium"


class TestSRDDataCompleteness:
    """Test that SRD data has minimum required entries."""

    def test_spells_count(self):
        """Should have at least 20 spells."""
        assert len(srd_spells) >= 20

    def test_monsters_count(self):
        """Should have at least 15 monsters."""
        assert len(srd_monsters) >= 15

    def test_equipment_count(self):
        """Should have at least 15 equipment items."""
        assert len(srd_equipment) >= 15

    def test_classes_count(self):
        """Should have all 12 SRD classes."""
        assert len(srd_classes) == 12

    def test_races_count(self):
        """Should have core SRD races (at least 5)."""
        assert len(srd_races) >= 5

    def test_spell_names_valid(self):
        """All spells should have valid names."""
        for spell in srd_spells:
            assert spell.name
            assert isinstance(spell.name, str)
            assert len(spell.name) > 0

    def test_spell_schools_valid(self):
        """All spells should have valid schools."""
        valid_schools = {
            "Abjuration",
            "Conjuration",
            "Divination",
            "Enchantment",
            "Evocation",
            "Illusion",
            "Necromancy",
            "Transmutation",
        }
        for spell in srd_spells:
            assert spell.school in valid_schools

    def test_monster_names_valid(self):
        """All monsters should have valid names."""
        for monster in srd_monsters:
            assert monster.name
            assert isinstance(monster.name, str)

    def test_common_spells_exist(self):
        """Test that common spells are present."""
        spell_names = {spell.name.lower() for spell in srd_spells}
        common_spells = {
            "fireball",
            "magic missile",
            "cure wounds",
            "shield",
        }
        for spell in common_spells:
            assert spell in spell_names, f"Missing spell: {spell}"

    def test_common_monsters_exist(self):
        """Test that common monsters are present."""
        monster_names = {monster.name.lower() for monster in srd_monsters}
        common_monsters = {
            "goblin",
            "skeleton",
            "dragon",
        }
        for monster in common_monsters:
            assert monster in monster_names, f"Missing monster: {monster}"

    def test_classes_have_all_12(self):
        """Test that all 12 SRD classes are present."""
        class_names = {cls.name.lower() for cls in srd_classes}
        expected_classes = {
            "barbarian",
            "bard",
            "cleric",
            "druid",
            "fighter",
            "monk",
            "paladin",
            "ranger",
            "rogue",
            "sorcerer",
            "warlock",
            "wizard",
        }
        assert class_names == expected_classes
