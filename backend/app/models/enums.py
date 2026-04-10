"""
Enums for D&D 5e data models.
"""
from enum import Enum


class Race(str, Enum):
    """Valid D&D 5e races."""
    HUMAN = "human"
    ELF = "elf"
    DWARF = "dwarf"
    HALFLING = "halfling"
    GNOME = "gnome"
    HALF_ELF = "half-elf"
    HALF_ORC = "half-orc"
    TIEFLING = "tiefling"
    DRAGONBORN = "dragonborn"


class CharacterClass(str, Enum):
    """Valid D&D 5e classes."""
    BARBARIAN = "barbarian"
    BARD = "bard"
    CLERIC = "cleric"
    DRUID = "druid"
    FIGHTER = "fighter"
    MONK = "monk"
    PALADIN = "paladin"
    RANGER = "ranger"
    ROGUE = "rogue"
    SORCERER = "sorcerer"
    WARLOCK = "warlock"
    WIZARD = "wizard"


class GamePhase(str, Enum):
    """Possible game phases."""
    LOBBY = "lobby"
    EXPLORATION = "exploration"
    COMBAT = "combat"
    REST = "rest"
    SHOPPING = "shopping"


class TerrainType(str, Enum):
    """Types of terrain on a map."""
    EMPTY = "empty"
    WALL = "wall"
    WATER = "water"
    DIFFICULT = "difficult"
    PIT = "pit"


class Condition(str, Enum):
    """D&D 5e conditions that can affect characters."""
    BLINDED = "blinded"
    CHARMED = "charmed"
    DEAFENED = "deafened"
    EXHAUSTION = "exhaustion"
    FRIGHTENED = "frightened"
    GRAPPLED = "grappled"
    INCAPACITATED = "incapacitated"
    INVISIBLE = "invisible"
    PARALYZED = "paralyzed"
    PETRIFIED = "petrified"
    POISONED = "poisoned"
    PRONE = "prone"
    RESTRAINED = "restrained"
    STUNNED = "stunned"
    UNCONSCIOUS = "unconscious"
