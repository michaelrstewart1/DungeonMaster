"""
D&D 5e Ability Checks and Saving Throws.
"""

from dataclasses import dataclass, field
from app.services.dice import DiceRoller


@dataclass
class AbilityCheckResult:
    """Result of an ability check or saving throw."""
    roll: int
    modifier: int
    proficiency_bonus: int
    total: int
    dc: int
    success: bool
    is_natural_20: bool
    is_natural_1: bool
    had_advantage: bool
    had_disadvantage: bool
    rolls: list[int] = field(default_factory=list)


class AbilityChecker:
    """Handle ability checks and saving throws."""

    def __init__(self, dice_roller: DiceRoller):
        """
        Initialize the AbilityChecker.
        
        Args:
            dice_roller: DiceRoller instance for rolling dice
        """
        self._dice = dice_roller

    def ability_check(
        self,
        ability_modifier: int,
        dc: int,
        proficiency_bonus: int = 0,
        advantage: bool = False,
        disadvantage: bool = False,
    ) -> AbilityCheckResult:
        """
        Perform an ability check.
        
        Args:
            ability_modifier: Modifier from the ability score
            dc: Difficulty Class (DC) to meet or exceed
            proficiency_bonus: Proficiency bonus (if proficient)
            advantage: If True, roll with advantage (2d20, take higher)
            disadvantage: If True, roll with disadvantage (2d20, take lower)
            
        Returns:
            AbilityCheckResult with roll result and success determination
        """
        # Roll the d20
        if advantage:
            d20_result = self._dice.roll_with_advantage()
        elif disadvantage:
            d20_result = self._dice.roll_with_disadvantage()
        else:
            d20_result = self._dice.roll("1d20")
        
        roll = d20_result.total
        rolls = d20_result.rolls
        
        # Calculate total: roll + modifier + proficiency
        total = roll + ability_modifier + proficiency_bonus
        
        # Determine success
        is_natural_20 = d20_result.is_critical
        is_natural_1 = d20_result.is_fumble
        
        # Natural 20 always succeeds, natural 1 always fails
        if is_natural_20:
            success = True
        elif is_natural_1:
            success = False
        else:
            success = total >= dc
        
        return AbilityCheckResult(
            roll=roll,
            modifier=ability_modifier,
            proficiency_bonus=proficiency_bonus,
            total=total,
            dc=dc,
            success=success,
            is_natural_20=is_natural_20,
            is_natural_1=is_natural_1,
            had_advantage=advantage,
            had_disadvantage=disadvantage,
            rolls=rolls,
        )

    def saving_throw(
        self,
        ability_modifier: int,
        dc: int,
        proficiency_bonus: int = 0,
        advantage: bool = False,
        disadvantage: bool = False,
    ) -> AbilityCheckResult:
        """
        Perform a saving throw.
        
        Saving throws use the same mechanics as ability checks but represent
        a character's attempt to resist an effect.
        
        Args:
            ability_modifier: Modifier from the ability score
            dc: Difficulty Class (DC) to meet or exceed
            proficiency_bonus: Proficiency bonus (if proficient in this save)
            advantage: If True, roll with advantage (2d20, take higher)
            disadvantage: If True, roll with disadvantage (2d20, take lower)
            
        Returns:
            AbilityCheckResult with save result and success determination
        """
        # Saving throws use the same mechanics as ability checks
        return self.ability_check(
            ability_modifier=ability_modifier,
            dc=dc,
            proficiency_bonus=proficiency_bonus,
            advantage=advantage,
            disadvantage=disadvantage,
        )
