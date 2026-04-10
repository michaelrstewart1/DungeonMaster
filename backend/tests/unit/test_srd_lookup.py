"""
Tests for SRD lookup service.
"""
import pytest
from app.services.srd.lookup import SRDLookupService
from app.services.srd.data import srd_spells, srd_monsters, srd_equipment, srd_classes, srd_races


@pytest.fixture
def lookup_service():
    """Provide an SRDLookupService instance."""
    return SRDLookupService()


class TestSpellLookup:
    """Test spell lookup and search functionality."""

    async def test_get_spell_by_exact_name(self, lookup_service):
        """Test getting a spell by exact name."""
        spell = await lookup_service.get_spell("Fireball")
        assert spell is not None
        assert spell.name.lower() == "fireball"

    async def test_get_spell_case_insensitive(self, lookup_service):
        """Test that spell lookup is case-insensitive."""
        spell1 = await lookup_service.get_spell("fireball")
        spell2 = await lookup_service.get_spell("FIREBALL")
        spell3 = await lookup_service.get_spell("Fireball")
        assert spell1 is not None
        assert spell2 is not None
        assert spell3 is not None
        assert spell1.name == spell2.name == spell3.name

    async def test_get_nonexistent_spell(self, lookup_service):
        """Test getting a spell that doesn't exist."""
        spell = await lookup_service.get_spell("NonexistentSpell")
        assert spell is None

    async def test_search_spells_by_query(self, lookup_service):
        """Test searching spells by name substring."""
        results = await lookup_service.search_spells("ball")
        assert len(results) > 0
        assert any("ball" in spell.name.lower() for spell in results)

    async def test_search_spells_by_level(self, lookup_service):
        """Test searching spells by level."""
        results = await lookup_service.search_spells(level=3)
        assert len(results) > 0
        assert all(spell.level == 3 for spell in results)

    async def test_search_spells_by_class(self, lookup_service):
        """Test searching spells by class."""
        results = await lookup_service.search_spells(class_name="Wizard")
        assert len(results) > 0
        assert all("Wizard" in spell.classes for spell in results)

    async def test_search_spells_combined_filters(self, lookup_service):
        """Test searching spells with combined filters."""
        results = await lookup_service.search_spells(level=1, class_name="Cleric")
        assert all(spell.level == 1 for spell in results)
        assert all("Cleric" in spell.classes for spell in results)

    async def test_search_spells_empty_query(self, lookup_service):
        """Test searching spells with empty query returns all."""
        all_spells = await lookup_service.search_spells()
        assert len(all_spells) == len(srd_spells)


class TestMonsterLookup:
    """Test monster lookup and search functionality."""

    async def test_get_monster_by_exact_name(self, lookup_service):
        """Test getting a monster by exact name."""
        monster = await lookup_service.get_monster("Goblin")
        assert monster is not None
        assert monster.name.lower() == "goblin"

    async def test_get_monster_case_insensitive(self, lookup_service):
        """Test that monster lookup is case-insensitive."""
        monster1 = await lookup_service.get_monster("goblin")
        monster2 = await lookup_service.get_monster("GOBLIN")
        monster3 = await lookup_service.get_monster("Goblin")
        assert monster1 is not None
        assert monster2 is not None
        assert monster3 is not None
        assert monster1.name == monster2.name == monster3.name

    async def test_get_nonexistent_monster(self, lookup_service):
        """Test getting a monster that doesn't exist."""
        monster = await lookup_service.get_monster("NonexistentMonster")
        assert monster is None

    async def test_search_monsters_by_query(self, lookup_service):
        """Test searching monsters by name substring."""
        results = await lookup_service.search_monsters("goblin")
        assert len(results) > 0
        assert any("goblin" in monster.name.lower() for monster in results)

    async def test_search_monsters_by_cr(self, lookup_service):
        """Test searching monsters by challenge rating range."""
        results = await lookup_service.search_monsters(cr_min=0, cr_max=1)
        assert all(monster.challenge_rating <= 1 for monster in results)
        assert all(monster.challenge_rating >= 0 for monster in results)

    async def test_search_monsters_empty_query(self, lookup_service):
        """Test searching monsters with no filters returns all."""
        all_monsters = await lookup_service.search_monsters()
        assert len(all_monsters) == len(srd_monsters)


class TestEquipmentLookup:
    """Test equipment lookup and search functionality."""

    async def test_get_equipment_by_exact_name(self, lookup_service):
        """Test getting equipment by exact name."""
        equipment = await lookup_service.get_equipment("Longsword")
        assert equipment is not None
        assert equipment.name.lower() == "longsword"

    async def test_get_equipment_case_insensitive(self, lookup_service):
        """Test that equipment lookup is case-insensitive."""
        eq1 = await lookup_service.get_equipment("longsword")
        eq2 = await lookup_service.get_equipment("LONGSWORD")
        eq3 = await lookup_service.get_equipment("Longsword")
        assert eq1 is not None
        assert eq2 is not None
        assert eq3 is not None
        assert eq1.name == eq2.name == eq3.name

    async def test_get_nonexistent_equipment(self, lookup_service):
        """Test getting equipment that doesn't exist."""
        equipment = await lookup_service.get_equipment("NonexistentEquipment")
        assert equipment is None

    async def test_search_equipment_by_query(self, lookup_service):
        """Test searching equipment by name substring."""
        results = await lookup_service.search_equipment("sword")
        assert len(results) > 0
        assert any("sword" in item.name.lower() for item in results)

    async def test_search_equipment_by_category(self, lookup_service):
        """Test searching equipment by category."""
        results = await lookup_service.search_equipment(category="Weapons")
        assert all(item.category == "Weapons" for item in results)

    async def test_search_equipment_empty_query(self, lookup_service):
        """Test searching equipment with no filters returns all."""
        all_equipment = await lookup_service.search_equipment()
        assert len(all_equipment) == len(srd_equipment)


class TestClassLookup:
    """Test class lookup functionality."""

    async def test_get_class_by_name(self, lookup_service):
        """Test getting a class by name."""
        cls = await lookup_service.get_class_info("Wizard")
        assert cls is not None
        assert cls.name.lower() == "wizard"

    async def test_get_class_case_insensitive(self, lookup_service):
        """Test that class lookup is case-insensitive."""
        cls1 = await lookup_service.get_class_info("wizard")
        cls2 = await lookup_service.get_class_info("WIZARD")
        cls3 = await lookup_service.get_class_info("Wizard")
        assert cls1 is not None
        assert cls2 is not None
        assert cls3 is not None
        assert cls1.name == cls2.name == cls3.name

    async def test_get_nonexistent_class(self, lookup_service):
        """Test getting a class that doesn't exist."""
        cls = await lookup_service.get_class_info("NonexistentClass")
        assert cls is None

    async def test_get_all_classes(self, lookup_service):
        """Test getting all classes."""
        classes = await lookup_service.get_all_classes()
        assert len(classes) == 12
        class_names = {cls.name.lower() for cls in classes}
        expected = {
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
        assert class_names == expected


class TestRaceLookup:
    """Test race lookup functionality."""

    async def test_get_race_by_name(self, lookup_service):
        """Test getting a race by name."""
        race = await lookup_service.get_race_info("Human")
        assert race is not None
        assert race.name.lower() == "human"

    async def test_get_race_case_insensitive(self, lookup_service):
        """Test that race lookup is case-insensitive."""
        race1 = await lookup_service.get_race_info("human")
        race2 = await lookup_service.get_race_info("HUMAN")
        race3 = await lookup_service.get_race_info("Human")
        assert race1 is not None
        assert race2 is not None
        assert race3 is not None
        assert race1.name == race2.name == race3.name

    async def test_get_nonexistent_race(self, lookup_service):
        """Test getting a race that doesn't exist."""
        race = await lookup_service.get_race_info("NonexistentRace")
        assert race is None

    async def test_get_all_races(self, lookup_service):
        """Test getting all races."""
        races = await lookup_service.get_all_races()
        assert len(races) >= 5
