"""
D&D 5e Condition Effects and Tracking.
"""

from dataclasses import dataclass, field
from typing import Optional
from app.models.enums import Condition


@dataclass
class ConditionEffect:
    """Effects applied by conditions."""
    attack_advantage: bool = False
    attack_disadvantage: bool = False
    ability_check_disadvantage: bool = False
    save_disadvantage_str: bool = False
    save_disadvantage_dex: bool = False
    auto_fail_str_saves: bool = False
    auto_fail_dex_saves: bool = False
    attackers_have_advantage: bool = False
    melee_attacks_auto_crit: bool = False
    grants_advantage_on_attacks: bool = False


class ConditionTracker:
    """Track and manage condition effects."""

    def get_effects(self, conditions: list[Condition]) -> ConditionEffect:
        """
        Determine combined effects of multiple conditions.
        
        Args:
            conditions: List of conditions affecting the creature
            
        Returns:
            ConditionEffect with combined effects
        """
        effect = ConditionEffect()
        
        for condition in conditions:
            if condition == Condition.BLINDED:
                # Blinded: disadvantage on attack rolls, attackers have advantage
                effect.attack_disadvantage = True
                effect.attackers_have_advantage = True
                
            elif condition == Condition.FRIGHTENED:
                # Frightened: disadvantage on ability checks and attack rolls
                effect.ability_check_disadvantage = True
                effect.attack_disadvantage = True
                
            elif condition == Condition.INVISIBLE:
                # Invisible: advantage on attack rolls, attackers have disadvantage
                effect.attack_advantage = True
                effect.grants_advantage_on_attacks = True
                
            elif condition == Condition.PARALYZED:
                # Paralyzed: auto-fail STR/DEX saves, attacks have advantage, melee crits within 5ft
                effect.auto_fail_str_saves = True
                effect.auto_fail_dex_saves = True
                effect.attackers_have_advantage = True
                effect.melee_attacks_auto_crit = True
                
            elif condition == Condition.PETRIFIED:
                # Petrified: auto-fail STR/DEX saves, attacks have advantage
                effect.auto_fail_str_saves = True
                effect.auto_fail_dex_saves = True
                effect.attackers_have_advantage = True
                
            elif condition == Condition.POISONED:
                # Poisoned: disadvantage on attack rolls and ability checks
                effect.attack_disadvantage = True
                effect.ability_check_disadvantage = True
                
            elif condition == Condition.PRONE:
                # Prone: disadvantage on attack rolls, melee attackers have advantage, ranged have disadvantage
                effect.attack_disadvantage = True
                
            elif condition == Condition.RESTRAINED:
                # Restrained: disadvantage on attack rolls, disadvantage on DEX saves, attackers have advantage
                effect.attack_disadvantage = True
                effect.save_disadvantage_dex = True
                effect.attackers_have_advantage = True
                
            elif condition == Condition.STUNNED:
                # Stunned: auto-fail STR/DEX saves, attacks have advantage
                effect.auto_fail_str_saves = True
                effect.auto_fail_dex_saves = True
                effect.attackers_have_advantage = True
                
            elif condition == Condition.UNCONSCIOUS:
                # Unconscious: auto-fail STR/DEX saves, attacks have advantage, melee auto-crit within 5ft
                effect.auto_fail_str_saves = True
                effect.auto_fail_dex_saves = True
                effect.attackers_have_advantage = True
                effect.melee_attacks_auto_crit = True
                
            elif condition == Condition.CHARMED:
                # Charmed: typically doesn't affect mechanics in combat
                pass
                
            elif condition == Condition.DEAFENED:
                # Deafened: typically doesn't affect mechanics in combat
                pass
                
            elif condition == Condition.GRAPPLED:
                # Grappled: affects movement but not combat mechanics we track
                pass
                
            elif condition == Condition.INCAPACITATED:
                # Incapacitated: can't take actions or reactions
                pass
                
            elif condition == Condition.EXHAUSTION:
                # Exhaustion: has level-based effects we may not track in combat
                pass
        
        return effect

    def get_attack_modifiers(
        self,
        attacker_conditions: list[Condition],
        target_conditions: list[Condition],
        is_melee: bool = True,
    ) -> dict:
        """
        Determine attack modifiers based on conditions.
        
        Args:
            attacker_conditions: Conditions affecting the attacker
            target_conditions: Conditions affecting the target
            is_melee: Whether this is a melee attack (vs ranged)
            
        Returns:
            Dictionary with attack modifiers
        """
        modifiers = {
            "attacker_advantage": False,
            "attacker_disadvantage": False,
            "target_advantage": False,
            "target_disadvantage": False,
        }
        
        # Get effects for both
        attacker_effect = self.get_effects(attacker_conditions)
        target_effect = self.get_effects(target_conditions)
        
        # Attacker effects
        if attacker_effect.attack_advantage:
            modifiers["attacker_advantage"] = True
        if attacker_effect.attack_disadvantage:
            modifiers["attacker_disadvantage"] = True
        
        # Target conditions that give advantage to attackers
        if target_effect.attackers_have_advantage:
            modifiers["target_advantage"] = True
        
        # Prone gives advantage to melee, disadvantage to ranged
        if Condition.PRONE in target_conditions:
            if is_melee:
                modifiers["target_advantage"] = True
            else:
                modifiers["target_disadvantage"] = True
        
        # Invisible gives advantage to attacker
        if Condition.INVISIBLE in attacker_conditions:
            modifiers["attacker_advantage"] = True
        
        return modifiers
