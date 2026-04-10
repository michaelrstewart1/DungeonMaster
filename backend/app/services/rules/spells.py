"""Spell casting system for D&D 5e."""

from dataclasses import dataclass, field
from enum import Enum
from math import ceil

from app.services.dice import DiceRoller


class SpellSchool(str, Enum):
    ABJURATION = "abjuration"
    CONJURATION = "conjuration"
    DIVINATION = "divination"
    ENCHANTMENT = "enchantment"
    EVOCATION = "evocation"
    ILLUSION = "illusion"
    NECROMANCY = "necromancy"
    TRANSMUTATION = "transmutation"


class SpellTarget(str, Enum):
    CREATURE = "creature"
    AREA = "area"
    SELF = "self"
    ALLY = "ally"
    OBJECT = "object"


@dataclass
class Spell:
    name: str
    level: int  # 0 = cantrip
    school: SpellSchool
    casting_time: str
    range_ft: int
    duration: str
    target: SpellTarget
    description: str = ""
    damage_dice: str = ""
    upcast_dice: str = ""
    concentration: bool = False
    is_attack_spell: bool = False
    is_save_spell: bool = False
    save_ability: str = ""
    half_damage_on_save: bool = False

    @property
    def is_cantrip(self) -> bool:
        return self.level == 0


# Full caster spell slot table (PHB p. 201)
_FULL_CASTER_SLOTS: dict[int, dict[int, int]] = {
    1:  {1: 2},
    2:  {1: 3},
    3:  {1: 4, 2: 2},
    4:  {1: 4, 2: 3},
    5:  {1: 4, 2: 3, 3: 2},
    6:  {1: 4, 2: 3, 3: 3},
    7:  {1: 4, 2: 3, 3: 3, 4: 1},
    8:  {1: 4, 2: 3, 3: 3, 4: 2},
    9:  {1: 4, 2: 3, 3: 3, 4: 3, 5: 1},
    10: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2},
    11: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},
    12: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},
    13: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},
    14: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},
    15: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},
    16: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},
    17: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1, 9: 1},
    18: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 1, 7: 1, 8: 1, 9: 1},
    19: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 1, 8: 1, 9: 1},
    20: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 2, 8: 1, 9: 1},
}


@dataclass
class SpellSlots:
    """Manages spell slot availability."""

    _current: dict[int, int] = field(default_factory=dict)
    _maximum: dict[int, int] = field(default_factory=dict)

    @classmethod
    def for_full_caster(cls, level: int) -> "SpellSlots":
        level = max(1, min(20, level))
        max_slots = dict(_FULL_CASTER_SLOTS.get(level, {}))
        current = dict(max_slots)
        return cls(_current=current, _maximum=max_slots)

    def get_slots(self, spell_level: int) -> int:
        return self._current.get(spell_level, 0)

    def get_max_slots(self, spell_level: int) -> int:
        return self._maximum.get(spell_level, 0)

    def use_slot(self, spell_level: int) -> None:
        available = self._current.get(spell_level, 0)
        if available <= 0:
            raise ValueError(f"No level {spell_level} slots available")
        self._current[spell_level] = available - 1

    def restore_all(self) -> None:
        self._current = dict(self._maximum)


@dataclass
class SpellCastResult:
    spell_name: str
    slot_used: int
    damage: int = 0
    attack_roll: int | None = None
    hit: bool | None = None
    save_dc: int | None = None
    requires_concentration: bool = False


class SpellCaster:
    """Handles spell casting mechanics."""

    def __init__(self, dice_roller: DiceRoller):
        self._dice = dice_roller

    def cast(
        self,
        spell: Spell,
        slots: SpellSlots,
        caster_level: int,
        spell_save_dc: int,
        cast_at_level: int | None = None,
        spell_attack_bonus: int = 0,
        target_ac: int = 0,
    ) -> SpellCastResult:
        effective_level = cast_at_level if cast_at_level is not None else spell.level

        # Consume slot (cantrips don't use slots)
        if not spell.is_cantrip:
            slots.use_slot(effective_level)

        damage = 0
        attack_roll = None
        hit = None
        save_dc = None

        # Roll damage if spell has damage dice
        if spell.damage_dice:
            result = self._dice.roll(spell.damage_dice)
            damage = result.total

            # Add upcast damage
            if spell.upcast_dice and cast_at_level and cast_at_level > spell.level:
                levels_above = cast_at_level - spell.level
                for _ in range(levels_above):
                    upcast_result = self._dice.roll(spell.upcast_dice)
                    damage += upcast_result.total

        # Attack spell
        if spell.is_attack_spell:
            roll_result = self._dice.roll("1d20")
            attack_roll = roll_result.total + spell_attack_bonus
            hit = attack_roll >= target_ac or roll_result.is_critical
            if roll_result.is_fumble:
                hit = False

        # Save spell
        if spell.is_save_spell:
            save_dc = spell_save_dc

        return SpellCastResult(
            spell_name=spell.name,
            slot_used=effective_level,
            damage=damage,
            attack_roll=attack_roll,
            hit=hit,
            save_dc=save_dc,
            requires_concentration=spell.concentration,
        )

    @staticmethod
    def concentration_save_dc(damage: int) -> int:
        """Calculate concentration save DC from damage taken."""
        return max(10, damage // 2)
