"""Tests for the spell casting system — written FIRST (TDD RED phase)."""

import pytest
from app.services.dice import DiceRoller
from app.services.rules.spells import (
    Spell,
    SpellSlots,
    SpellCastResult,
    SpellCaster,
    SpellSchool,
    SpellTarget,
)


class TestSpellSlots:
    """Test spell slot management."""

    def test_create_spell_slots_for_level_1_wizard(self):
        """Level 1 wizard has 2 first-level slots."""
        slots = SpellSlots.for_full_caster(level=1)
        assert slots.get_slots(1) == 2
        assert slots.get_slots(2) == 0

    def test_create_spell_slots_for_level_5_wizard(self):
        """Level 5 wizard has slots up to 3rd level."""
        slots = SpellSlots.for_full_caster(level=5)
        assert slots.get_slots(1) == 4
        assert slots.get_slots(2) == 3
        assert slots.get_slots(3) == 2
        assert slots.get_slots(4) == 0

    def test_create_spell_slots_for_level_20_wizard(self):
        """Level 20 wizard has slots up to 9th level."""
        slots = SpellSlots.for_full_caster(level=20)
        assert slots.get_slots(9) > 0

    def test_use_spell_slot(self):
        slots = SpellSlots.for_full_caster(level=1)
        initial = slots.get_slots(1)
        slots.use_slot(1)
        assert slots.get_slots(1) == initial - 1

    def test_use_spell_slot_when_none_available_raises(self):
        slots = SpellSlots.for_full_caster(level=1)
        # Use all level 1 slots
        for _ in range(slots.get_slots(1)):
            slots.use_slot(1)
        with pytest.raises(ValueError, match="No .* slots available"):
            slots.use_slot(1)

    def test_restore_all_slots(self):
        slots = SpellSlots.for_full_caster(level=1)
        slots.use_slot(1)
        slots.restore_all()
        assert slots.get_slots(1) == 2

    def test_slots_remaining_vs_max(self):
        slots = SpellSlots.for_full_caster(level=1)
        assert slots.get_max_slots(1) == 2
        slots.use_slot(1)
        assert slots.get_slots(1) == 1
        assert slots.get_max_slots(1) == 2


class TestSpellDefinition:
    """Test spell data structure."""

    def test_create_spell(self):
        spell = Spell(
            name="Magic Missile",
            level=1,
            school=SpellSchool.EVOCATION,
            casting_time="1 action",
            range_ft=120,
            duration="Instantaneous",
            description="Three darts of magical force.",
            damage_dice="1d4+1",
            target=SpellTarget.CREATURE,
        )
        assert spell.name == "Magic Missile"
        assert spell.level == 1

    def test_cantrip_is_level_0(self):
        spell = Spell(
            name="Fire Bolt",
            level=0,
            school=SpellSchool.EVOCATION,
            casting_time="1 action",
            range_ft=120,
            duration="Instantaneous",
            damage_dice="1d10",
            target=SpellTarget.CREATURE,
        )
        assert spell.level == 0
        assert spell.is_cantrip

    def test_concentration_spell(self):
        spell = Spell(
            name="Bless",
            level=1,
            school=SpellSchool.ENCHANTMENT,
            casting_time="1 action",
            range_ft=30,
            duration="Concentration, up to 1 minute",
            concentration=True,
            description="Buff allies.",
            target=SpellTarget.ALLY,
        )
        assert spell.concentration is True


class TestSpellCasting:
    """Test the spell casting mechanics."""

    def setup_method(self):
        self.dice = DiceRoller(seed=42)
        self.caster = SpellCaster(self.dice)

    def test_cast_spell_consumes_slot(self):
        slots = SpellSlots.for_full_caster(level=1)
        spell = Spell(
            name="Magic Missile",
            level=1,
            school=SpellSchool.EVOCATION,
            casting_time="1 action",
            range_ft=120,
            duration="Instantaneous",
            damage_dice="1d4+1",
            target=SpellTarget.CREATURE,
        )
        initial = slots.get_slots(1)
        result = self.caster.cast(spell, slots, caster_level=1, spell_save_dc=13)
        assert slots.get_slots(1) == initial - 1

    def test_cantrip_does_not_consume_slot(self):
        slots = SpellSlots.for_full_caster(level=1)
        cantrip = Spell(
            name="Fire Bolt",
            level=0,
            school=SpellSchool.EVOCATION,
            casting_time="1 action",
            range_ft=120,
            duration="Instantaneous",
            damage_dice="1d10",
            target=SpellTarget.CREATURE,
        )
        initial = slots.get_slots(1)
        result = self.caster.cast(cantrip, slots, caster_level=1, spell_save_dc=13)
        assert slots.get_slots(1) == initial

    def test_cast_returns_result(self):
        slots = SpellSlots.for_full_caster(level=5)
        spell = Spell(
            name="Fireball",
            level=3,
            school=SpellSchool.EVOCATION,
            casting_time="1 action",
            range_ft=150,
            duration="Instantaneous",
            damage_dice="8d6",
            target=SpellTarget.AREA,
            is_save_spell=True,
        )
        result = self.caster.cast(spell, slots, caster_level=5, spell_save_dc=15)
        assert isinstance(result, SpellCastResult)
        assert result.spell_name == "Fireball"
        assert result.slot_used == 3
        assert result.damage > 0

    def test_cannot_cast_spell_above_highest_slot(self):
        slots = SpellSlots.for_full_caster(level=1)  # Only has level 1 slots
        spell = Spell(
            name="Fireball",
            level=3,
            school=SpellSchool.EVOCATION,
            casting_time="1 action",
            range_ft=150,
            duration="Instantaneous",
            damage_dice="8d6",
            target=SpellTarget.AREA,
        )
        with pytest.raises(ValueError, match="No .* slots available"):
            self.caster.cast(spell, slots, caster_level=1, spell_save_dc=13)

    def test_upcast_spell_at_higher_level(self):
        """Casting a spell at a higher level uses that level's slot."""
        slots = SpellSlots.for_full_caster(level=5)
        spell = Spell(
            name="Magic Missile",
            level=1,
            school=SpellSchool.EVOCATION,
            casting_time="1 action",
            range_ft=120,
            duration="Instantaneous",
            damage_dice="1d4+1",
            upcast_dice="1d4+1",  # Extra dart per level
            target=SpellTarget.CREATURE,
        )
        initial_l2 = slots.get_slots(2)
        result = self.caster.cast(spell, slots, caster_level=5, spell_save_dc=13, cast_at_level=2)
        assert slots.get_slots(2) == initial_l2 - 1
        assert result.slot_used == 2

    def test_spell_attack_roll(self):
        """Spell attacks roll d20 + spellcasting modifier."""
        slots = SpellSlots.for_full_caster(level=1)
        spell = Spell(
            name="Fire Bolt",
            level=0,
            school=SpellSchool.EVOCATION,
            casting_time="1 action",
            range_ft=120,
            duration="Instantaneous",
            damage_dice="1d10",
            is_attack_spell=True,
            target=SpellTarget.CREATURE,
        )
        result = self.caster.cast(
            spell, slots, caster_level=1, spell_save_dc=13,
            spell_attack_bonus=5, target_ac=15
        )
        assert result.attack_roll is not None
        assert result.hit is not None

    def test_save_spell_uses_dc(self):
        """Save-based spells use the caster's spell save DC."""
        slots = SpellSlots.for_full_caster(level=5)
        spell = Spell(
            name="Fireball",
            level=3,
            school=SpellSchool.EVOCATION,
            casting_time="1 action",
            range_ft=150,
            duration="Instantaneous",
            damage_dice="8d6",
            is_save_spell=True,
            save_ability="dexterity",
            half_damage_on_save=True,
            target=SpellTarget.AREA,
        )
        result = self.caster.cast(spell, slots, caster_level=5, spell_save_dc=15)
        assert result.save_dc == 15
        assert result.damage > 0


class TestConcentration:
    """Test concentration tracking."""

    def setup_method(self):
        self.dice = DiceRoller(seed=42)
        self.caster = SpellCaster(self.dice)

    def test_casting_concentration_spell_sets_concentration(self):
        slots = SpellSlots.for_full_caster(level=1)
        spell = Spell(
            name="Bless",
            level=1,
            school=SpellSchool.ENCHANTMENT,
            casting_time="1 action",
            range_ft=30,
            duration="Concentration, up to 1 minute",
            concentration=True,
            target=SpellTarget.ALLY,
        )
        result = self.caster.cast(spell, slots, caster_level=1, spell_save_dc=13)
        assert result.requires_concentration is True

    def test_concentration_check_on_damage(self):
        """When concentrating and taking damage, make CON save DC = max(10, damage/2)."""
        # DC should be 10 for damage < 20, or damage/2 for higher
        dc = self.caster.concentration_save_dc(damage=10)
        assert dc == 10  # max(10, 10/2) = 10

        dc = self.caster.concentration_save_dc(damage=30)
        assert dc == 15  # max(10, 30/2) = 15


class TestSpellSchoolEnum:
    def test_all_schools_exist(self):
        schools = [
            SpellSchool.ABJURATION,
            SpellSchool.CONJURATION,
            SpellSchool.DIVINATION,
            SpellSchool.ENCHANTMENT,
            SpellSchool.EVOCATION,
            SpellSchool.ILLUSION,
            SpellSchool.NECROMANCY,
            SpellSchool.TRANSMUTATION,
        ]
        assert len(schools) == 8
