"""
D&D 5e Combat System.
"""

from dataclasses import dataclass, field
from typing import Optional
from app.services.dice import DiceRoller
from app.models.enums import Condition
from app.services.rules.conditions import ConditionTracker


@dataclass
class Combatant:
    """A creature participating in combat."""
    id: str
    name: str
    initiative: int
    initiative_modifier: int
    hp: int
    max_hp: int
    ac: int
    temp_hp: int = 0
    conditions: list[Condition] = field(default_factory=list)
    death_save_successes: int = 0
    death_save_failures: int = 0
    is_alive: bool = True
    is_stable: bool = False


@dataclass
class AttackResult:
    """Result of an attack roll."""
    attacker: str
    target: str
    attack_roll: int
    attack_bonus: int
    total_attack: int
    target_ac: int
    hit: bool
    is_critical: bool
    is_fumble: bool
    damage: int = 0
    damage_type: str = ""


class CombatManager:
    """Manage combat encounters and mechanics."""

    def __init__(self, dice_roller: DiceRoller):
        """
        Initialize the CombatManager.
        
        Args:
            dice_roller: DiceRoller instance for rolling dice
        """
        self._dice = dice_roller
        self._condition_tracker = ConditionTracker()

    def roll_initiative(self, combatants: list[dict]) -> list[Combatant]:
        """
        Roll initiative for all combatants and sort them.
        
        Args:
            combatants: List of dicts with at least id, name, initiative_modifier, hp, max_hp, ac
            
        Returns:
            List of Combatant objects sorted by initiative (descending)
        """
        initiative_order = []
        
        for combatant_data in combatants:
            # Roll d20 + modifier
            init_roll = self._dice.roll("1d20").total
            initiative = init_roll + combatant_data.get("initiative_modifier", 0)
            
            combatant = Combatant(
                id=combatant_data["id"],
                name=combatant_data["name"],
                initiative=initiative,
                initiative_modifier=combatant_data.get("initiative_modifier", 0),
                hp=combatant_data["hp"],
                max_hp=combatant_data["max_hp"],
                ac=combatant_data["ac"],
            )
            initiative_order.append(combatant)
        
        # Sort by initiative (descending), then by initiative modifier (tiebreaker)
        initiative_order.sort(
            key=lambda c: (c.initiative, c.initiative_modifier),
            reverse=True
        )
        
        return initiative_order

    def attack(
        self,
        attacker: Combatant,
        target: Combatant,
        attack_bonus: int,
        damage_notation: str,
        damage_type: str = "slashing",
    ) -> AttackResult:
        """
        Perform an attack roll and calculate damage if it hits.
        
        Args:
            attacker: Attacking combatant
            target: Target combatant
            attack_bonus: Bonus to attack roll
            damage_notation: Damage dice notation (e.g., "1d8+2")
            damage_type: Type of damage (slashing, piercing, bludgeoning, etc.)
            
        Returns:
            AttackResult with hit/miss and damage (if hit)
        """
        # Get condition effects
        attack_modifiers = self._condition_tracker.get_attack_modifiers(
            attacker.conditions,
            target.conditions,
            is_melee=True,  # Simplified: we could determine this from attack bonus
        )
        
        # Determine advantage/disadvantage
        advantage = attack_modifiers.get("attacker_advantage", False) or \
                   attack_modifiers.get("target_advantage", False)
        disadvantage = attack_modifiers.get("attacker_disadvantage", False) or \
                      attack_modifiers.get("target_disadvantage", False)
        
        # Roll attack
        if advantage:
            attack_result = self._dice.roll_with_advantage()
        elif disadvantage:
            attack_result = self._dice.roll_with_disadvantage()
        else:
            attack_result = self._dice.roll("1d20")
        
        attack_roll = attack_result.total
        total_attack = attack_roll + attack_bonus
        
        # Determine hit/miss/critical/fumble
        is_critical = attack_result.is_critical
        is_fumble = attack_result.is_fumble
        
        hit = False
        damage = 0
        
        if is_fumble:
            hit = False
        elif is_critical:
            hit = True
            # Critical hit: roll damage twice
            damage_result = self._dice.roll(damage_notation)
            damage = damage_result.total * 2
        elif total_attack >= target.ac:
            hit = True
            # Normal hit: roll damage
            damage_result = self._dice.roll(damage_notation)
            damage = damage_result.total
        
        # Apply resistance/vulnerability
        if hit and not is_fumble:
            if damage_type in ["piercing", "slashing", "bludgeoning"]:
                # Could add resistance logic here
                pass
        
        return AttackResult(
            attacker=attacker.id,
            target=target.id,
            attack_roll=attack_roll,
            attack_bonus=attack_bonus,
            total_attack=total_attack,
            target_ac=target.ac,
            hit=hit,
            is_critical=is_critical,
            is_fumble=is_fumble,
            damage=damage,
            damage_type=damage_type,
        )

    def apply_damage(
        self,
        target: Combatant,
        damage: int,
        damage_type: str = "",
        resistance: list[str] = None,
        vulnerability: list[str] = None,
    ) -> int:
        """
        Apply damage to a target, accounting for temp HP, resistance, and vulnerability.
        
        Args:
            target: Combatant taking damage
            damage: Amount of damage to apply
            damage_type: Type of damage
            resistance: List of damage types the target resists (takes half)
            vulnerability: List of damage types the target is vulnerable to (takes double)
            
        Returns:
            Remaining HP after damage
        """
        # Apply vulnerability (double damage)
        if vulnerability and damage_type in vulnerability:
            damage = damage * 2
        
        # Apply resistance (half damage, rounded down)
        if resistance and damage_type in resistance:
            damage = damage // 2
        
        # Apply temp HP first
        if target.temp_hp >= damage:
            target.temp_hp -= damage
            return target.hp
        
        # Remaining damage after temp HP
        remaining_damage = damage - target.temp_hp
        target.temp_hp = 0
        
        # Apply to actual HP
        target.hp = max(0, target.hp - remaining_damage)
        
        return target.hp

    def heal(self, target: Combatant, amount: int) -> int:
        """
        Restore HP to a target (cannot exceed max HP).
        
        Args:
            target: Combatant to heal
            amount: Amount of HP to restore
            
        Returns:
            New HP total
        """
        target.hp = min(target.max_hp, target.hp + amount)
        return target.hp

    def death_save(self, combatant: Combatant) -> dict:
        """
        Perform a death save for an unconscious combatant at 0 HP.
        
        Rules:
        - Roll d20 (no modifiers)
        - 10+ = success, <10 = failure
        - 3 successes = stable
        - 3 failures = death
        - Natural 20 = regain 1 HP and regain consciousness
        - Natural 1 = counts as 2 failures
        
        Args:
            combatant: Combatant making the death save
            
        Returns:
            Dict with roll result and status
        """
        save_roll = self._dice.roll("1d20").total
        
        if save_roll == 20:
            # Natural 20: regain 1 HP
            combatant.hp = 1
            combatant.is_stable = True
            return {
                "roll": save_roll,
                "result": "natural_20",
                "hp": combatant.hp,
                "successes": combatant.death_save_successes,
                "failures": combatant.death_save_failures,
            }
        elif save_roll == 1:
            # Natural 1: counts as 2 failures
            combatant.death_save_failures += 2
            if combatant.death_save_failures >= 3:
                combatant.is_alive = False
            return {
                "roll": save_roll,
                "result": "natural_1",
                "failures": combatant.death_save_failures,
                "dead": combatant.death_save_failures >= 3,
            }
        elif save_roll >= 10:
            # Success
            combatant.death_save_successes += 1
            if combatant.death_save_successes >= 3:
                combatant.is_stable = True
            return {
                "roll": save_roll,
                "result": "success",
                "successes": combatant.death_save_successes,
                "stable": combatant.is_stable,
            }
        else:
            # Failure
            combatant.death_save_failures += 1
            if combatant.death_save_failures >= 3:
                combatant.is_alive = False
            return {
                "roll": save_roll,
                "result": "failure",
                "failures": combatant.death_save_failures,
                "dead": combatant.death_save_failures >= 3,
            }
