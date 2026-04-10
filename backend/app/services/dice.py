"""
D&D 5e Dice Rolling System.

Provides comprehensive dice rolling functionality for D&D 5e mechanics including:
- Standard dice notation (1d20, 2d6+3, etc.)
- Advantage/disadvantage rolls
- Critical hit/fumble detection
- Drop lowest (for ability score generation)
"""

from dataclasses import dataclass, field
import random
import re
from typing import Optional


@dataclass
class DiceResult:
    """Result of a dice roll."""
    notation: str
    rolls: list[int]
    modifier: int = 0
    total: int = 0
    is_critical: bool = False
    is_fumble: bool = False
    dropped: list[int] = field(default_factory=list)


class DiceRoller:
    """Roll dice using standard D&D notation."""

    # Valid dice types
    VALID_DICE = {4, 6, 8, 10, 12, 20, 100}

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the DiceRoller.
        
        Args:
            seed: Optional seed for deterministic random number generation.
        """
        self._rng = random.Random(seed)

    def roll(self, notation: str) -> DiceResult:
        """
        Roll dice using standard notation.
        
        Supports:
        - Simple notation: "1d20", "2d6"
        - With modifiers: "1d20+5", "2d6-2"
        - Drop lowest: "4d6 drop lowest"
        
        Args:
            notation: Dice notation string (e.g., "1d20+5")
            
        Returns:
            DiceResult containing rolls, total, and metadata
            
        Raises:
            ValueError: If notation is invalid
        """
        notation = notation.strip()
        original_notation = notation

        # Check for "drop lowest" modifier
        drop_lowest = False
        if "drop lowest" in notation.lower():
            drop_lowest = True
            notation = notation.lower().replace("drop lowest", "").strip()

        # Parse the dice notation
        num_dice, die_type, modifier = self._parse_notation(notation, original_notation)

        # Roll the dice
        rolls = [self._rng.randint(1, die_type) for _ in range(num_dice)]

        # Handle drop lowest
        dropped, total = self._calculate_total(rolls, modifier, drop_lowest)

        # Determine if critical/fumble
        is_critical, is_fumble = self._check_critical_fumble(rolls, die_type)

        return DiceResult(
            notation=original_notation,
            rolls=rolls,
            modifier=modifier,
            total=total,
            is_critical=is_critical,
            is_fumble=is_fumble,
            dropped=dropped,
        )

    def roll_with_advantage(self) -> DiceResult:
        """
        Roll with advantage (2d20, take highest).
        
        Returns:
            DiceResult with both rolls, highest as total
        """
        result = self.roll("2d20")
        highest = max(result.rolls)
        
        return DiceResult(
            notation="1d20 (advantage)",
            rolls=result.rolls,
            modifier=0,
            total=highest,
            is_critical=highest == 20,
            is_fumble=highest == 1,
            dropped=[],
        )

    def roll_with_disadvantage(self) -> DiceResult:
        """
        Roll with disadvantage (2d20, take lowest).
        
        Returns:
            DiceResult with both rolls, lowest as total
        """
        result = self.roll("2d20")
        lowest = min(result.rolls)
        
        return DiceResult(
            notation="1d20 (disadvantage)",
            rolls=result.rolls,
            modifier=0,
            total=lowest,
            is_critical=lowest == 20,
            is_fumble=lowest == 1,
            dropped=[],
        )

    def roll_ability_scores(self) -> list[int]:
        """
        Roll ability scores for character creation.
        
        Rolls 4d6 drop lowest, 6 times, returning the 6 ability scores.
        
        Returns:
            List of 6 ability scores (each between 3 and 18)
        """
        return [self.roll("4d6 drop lowest").total for _ in range(6)]

    def _parse_notation(self, notation: str, original_notation: str) -> tuple[int, int, int]:
        """
        Parse dice notation string into components.
        
        Args:
            notation: Parsed notation string without "drop lowest"
            original_notation: Original notation for error messages
            
        Returns:
            Tuple of (num_dice, die_type, modifier)
            
        Raises:
            ValueError: If notation is invalid or die type is unsupported
        """
        # Pattern: NdX or NdX+M or NdX-M (where N=num dice, X=die type, M=modifier)
        pattern = r"^(\d+)d(\d+)\s*([+-]\s*\d+)?$"
        match = re.match(pattern, notation)

        if not match:
            raise ValueError(f"Invalid dice notation: {original_notation}")

        num_dice = int(match.group(1))
        die_type = int(match.group(2))
        modifier_str = match.group(3) if match.group(3) else "0"

        # Validate die type
        if die_type not in self.VALID_DICE:
            raise ValueError(f"Invalid die type: d{die_type}. Valid types: {sorted(self.VALID_DICE)}")

        # Parse modifier (remove spaces for easier parsing)
        modifier = self._parse_modifier(modifier_str)
        
        return num_dice, die_type, modifier

    def _parse_modifier(self, modifier_str: str) -> int:
        """
        Parse modifier string into integer.
        
        Args:
            modifier_str: Modifier string (e.g., "+5", "-3", "0")
            
        Returns:
            Integer modifier value
        """
        modifier_str = modifier_str.replace(" ", "")
        if modifier_str.startswith("+"):
            return int(modifier_str[1:])
        elif modifier_str.startswith("-"):
            return -int(modifier_str[1:])
        else:
            return int(modifier_str)

    def _calculate_total(self, rolls: list[int], modifier: int, drop_lowest: bool) -> tuple[list[int], int]:
        """
        Calculate total from rolls, handling drop lowest if specified.
        
        Args:
            rolls: List of individual die rolls
            modifier: Modifier to apply to total
            drop_lowest: Whether to drop the lowest die
            
        Returns:
            Tuple of (dropped_dice, total)
            
        Raises:
            ValueError: If drop_lowest is True but rolls has fewer than 2 dice
        """
        dropped = []
        
        if drop_lowest:
            if len(rolls) < 2:
                raise ValueError("Cannot drop lowest with fewer than 2 dice")
            min_roll = min(rolls)
            dropped = [min_roll]
            rolls_copy = rolls.copy()
            rolls_copy.remove(min_roll)
            total = sum(rolls_copy) + modifier
        else:
            total = sum(rolls) + modifier
        
        return dropped, total

    def _check_critical_fumble(self, rolls: list[int], die_type: int) -> tuple[bool, bool]:
        """
        Check if any rolls are natural 20 (critical) or natural 1 (fumble).
        
        Only applies to d20 rolls.
        
        Args:
            rolls: List of individual die rolls
            die_type: The type of die being rolled
            
        Returns:
            Tuple of (is_critical, is_fumble)
        """
        is_critical = False
        is_fumble = False
        
        if die_type == 20:
            is_critical = any(roll == 20 for roll in rolls)
            is_fumble = any(roll == 1 for roll in rolls)
        
        return is_critical, is_fumble
