"""
Rules Engine Orchestrator for D&D 5e AI Dungeon Master.

Coordinates a full combat round by delegating to various combat services
including combat management, ability checks, conditions, and spells.
"""

from dataclasses import dataclass
from app.services.dice import DiceRoller
from app.services.rules.combat import CombatManager, Combatant
from app.services.rules.abilities import AbilityChecker
from app.services.rules.conditions import ConditionTracker
from app.services.rules.spells import SpellCaster, SpellSlots, Spell


@dataclass
class ActionResult:
    """Result of a rules-resolved action (attack, spell, ability check, etc)."""
    action_type: str  # "attack", "spell", "ability_check", "heal", "death_save"
    success: bool
    description: str
    damage_dealt: int = 0
    healing_done: int = 0
    attacker: str = ""
    target: str = ""


class RulesEngine:
    """Orchestrates combat mechanics and resolves game actions."""

    def __init__(self, dice_roller: DiceRoller):
        """
        Initialize the RulesEngine.
        
        Args:
            dice_roller: DiceRoller instance for all dice rolls
        """
        self.dice_roller = dice_roller
        self.combat_manager = CombatManager(dice_roller)
        self.ability_checker = AbilityChecker(dice_roller)
        self.condition_tracker = ConditionTracker()
        self.spell_caster = SpellCaster(dice_roller)

    def start_combat(self, combatants: list[dict]) -> list[Combatant]:
        """
        Roll initiative and return ordered combatants.
        
        Args:
            combatants: List of dicts with id, name, initiative_modifier, hp, max_hp, ac
            
        Returns:
            List of Combatant objects sorted by initiative (descending)
        """
        return self.combat_manager.roll_initiative(combatants)

    def resolve_attack(
        self,
        attacker: Combatant,
        target: Combatant,
        attack_bonus: int,
        damage_dice: str,
        damage_type: str = "slashing"
    ) -> ActionResult:
        """
        Resolve a full attack flow.
        
        Args:
            attacker: Attacking combatant
            target: Target combatant
            attack_bonus: Bonus to add to attack roll
            damage_dice: Damage dice notation (e.g., "1d8+2")
            damage_type: Type of damage (slashing, piercing, fire, etc)
            
        Returns:
            ActionResult with attack outcome and damage
        """
        attack_result = self.combat_manager.attack(
            attacker=attacker,
            target=target,
            attack_bonus=attack_bonus,
            damage_notation=damage_dice,
            damage_type=damage_type
        )
        
        action_result = ActionResult(
            action_type="attack",
            success=attack_result.hit,
            description=self._describe_attack(attack_result),
            damage_dealt=attack_result.damage if attack_result.hit else 0,
            attacker=attack_result.attacker,
            target=attack_result.target
        )
        
        return action_result

    def resolve_ability_check(
        self,
        ability_mod: int,
        dc: int,
        proficiency: int = 0,
        advantage: bool = False,
        disadvantage: bool = False
    ) -> ActionResult:
        """
        Resolve an ability check.
        
        Args:
            ability_mod: Ability modifier
            dc: Difficulty Class
            proficiency: Proficiency bonus
            advantage: Whether the check has advantage
            disadvantage: Whether the check has disadvantage
            
        Returns:
            ActionResult with check outcome
        """
        check_result = self.ability_checker.ability_check(
            ability_modifier=ability_mod,
            dc=dc,
            proficiency_bonus=proficiency,
            advantage=advantage,
            disadvantage=disadvantage
        )
        
        action_result = ActionResult(
            action_type="ability_check",
            success=check_result.success,
            description=self._describe_ability_check(check_result)
        )
        
        return action_result

    def resolve_spell(
        self,
        spell: Spell,
        slots: SpellSlots,
        caster_level: int,
        spell_save_dc: int
    ) -> ActionResult:
        """
        Resolve spell casting.
        
        Args:
            spell: Spell being cast
            slots: SpellSlots available to caster
            caster_level: Caster's character level
            spell_save_dc: DC for spell saves
            
        Returns:
            ActionResult with spell outcome
        """
        try:
            spell_result = self.spell_caster.cast(
                spell=spell,
                slots=slots,
                caster_level=caster_level,
                spell_save_dc=spell_save_dc
            )
            
            action_result = ActionResult(
                action_type="spell",
                success=True,
                description=self._describe_spell(spell_result),
                damage_dealt=spell_result.damage if hasattr(spell_result, 'damage') else 0
            )
        except ValueError as e:
            # Insufficient spell slots
            action_result = ActionResult(
                action_type="spell",
                success=False,
                description=str(e)
            )
        
        return action_result

    def apply_damage(
        self,
        target: Combatant,
        damage: int,
        damage_type: str = "slashing",
        resistances: list[str] = None,
        vulnerabilities: list[str] = None
    ) -> int:
        """
        Apply damage to a target, accounting for resistances/vulnerabilities.
        
        Args:
            target: Target combatant
            damage: Base damage amount
            damage_type: Type of damage
            resistances: List of damage types this creature resists
            vulnerabilities: List of damage types this creature is vulnerable to
            
        Returns:
            Total damage actually applied
        """
        resistances = resistances or []
        vulnerabilities = vulnerabilities or []
        
        # Store old HP to calculate actual damage dealt
        old_hp = target.hp
        
        # Apply damage (CombatManager handles resistance/vulnerability)
        new_hp = self.combat_manager.apply_damage(
            target=target,
            damage=damage,
            damage_type=damage_type,
            resistance=resistances,
            vulnerability=vulnerabilities
        )
        
        # Return the actual damage applied
        damage_applied = old_hp - new_hp
        return damage_applied

    def heal_target(self, target: Combatant, amount: int) -> int:
        """
        Heal a target.
        
        Args:
            target: Target combatant
            amount: Amount of healing
            
        Returns:
            Total healing applied
        """
        old_hp = target.hp
        new_hp = self.combat_manager.heal(target, amount)
        healing_applied = new_hp - old_hp
        return healing_applied

    def process_death_save(self, combatant: Combatant) -> ActionResult:
        """
        Process a death saving throw.
        
        Args:
            combatant: Unconscious combatant making the save
            
        Returns:
            ActionResult with save outcome
        """
        # Roll death save (DC 10)
        save_result = self.ability_checker.ability_check(
            ability_modifier=0,
            dc=10,
            proficiency_bonus=0,
            advantage=False,
            disadvantage=False
        )
        
        success = save_result.success
        
        if save_result.is_natural_20:
            # Natural 20 = regain 1 HP and wake up
            combatant.hp = 1
            combatant.is_alive = True
            description = "Natural 20 on death save! You regain consciousness with 1 HP."
        elif save_result.is_natural_1:
            # Natural 1 = count as 2 failures
            combatant.death_save_failures = min(3, combatant.death_save_failures + 2)
            if combatant.death_save_failures >= 3:
                combatant.is_alive = False
                description = "Natural 1! You accumulate death save failures..."
            else:
                description = "Natural 1 on death save! You accumulate failures..."
        else:
            # Success = +1 success, Failure = +1 failure
            if success:
                combatant.death_save_successes += 1
                description = f"Death save success ({combatant.death_save_successes}/3)"
            else:
                combatant.death_save_failures += 1
                description = f"Death save failure ({combatant.death_save_failures}/3)"
            
            # Check if stabilized or dead
            if combatant.death_save_successes >= 3:
                combatant.is_stable = True
                description = "You stabilize!"
            elif combatant.death_save_failures >= 3:
                combatant.is_alive = False
                description = "You succumb to your wounds..."
        
        action_result = ActionResult(
            action_type="death_save",
            success=success,
            description=description
        )
        
        return action_result

    def _describe_attack(self, attack_result) -> str:
        """Generate descriptive text for an attack."""
        if attack_result.is_critical:
            return f"Critical hit! {attack_result.attacker} hits {attack_result.target} for {attack_result.damage} {attack_result.damage_type} damage!"
        elif attack_result.is_fumble:
            return f"Critical miss! {attack_result.attacker} fumbles their attack against {attack_result.target}!"
        elif attack_result.hit:
            return f"Hit! {attack_result.attacker} hits {attack_result.target} with {attack_result.attack_roll + attack_result.attack_bonus} vs AC {attack_result.target_ac} for {attack_result.damage} {attack_result.damage_type} damage."
        else:
            return f"Miss! {attack_result.attacker} misses {attack_result.target}. Attack roll: {attack_result.attack_roll + attack_result.attack_bonus} vs AC {attack_result.target_ac}."

    def _describe_ability_check(self, check_result) -> str:
        """Generate descriptive text for an ability check."""
        if check_result.is_natural_20:
            return f"Natural 20! You succeed with a total of {check_result.total} vs DC {check_result.dc}!"
        elif check_result.is_natural_1:
            return f"Natural 1! You fail with a total of {check_result.total} vs DC {check_result.dc}."
        elif check_result.success:
            return f"Success! You roll {check_result.roll} + {check_result.modifier + check_result.proficiency_bonus} = {check_result.total} vs DC {check_result.dc}."
        else:
            return f"Failure! You roll {check_result.roll} + {check_result.modifier + check_result.proficiency_bonus} = {check_result.total} vs DC {check_result.dc}."

    def _describe_spell(self, spell_result) -> str:
        """Generate descriptive text for a spell."""
        # SpellCastResult doesn't have a 'success' attribute; we infer it from the cast
        damage_text = f" ({spell_result.damage} damage)" if hasattr(spell_result, 'damage') and spell_result.damage else ""
        return f"The spell '{spell_result.spell_name}' is cast successfully{damage_text}!"
