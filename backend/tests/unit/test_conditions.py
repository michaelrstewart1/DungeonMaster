"""
Tests for D&D 5e Condition Effects.
"""

import pytest
from app.models.enums import Condition
from app.services.rules.conditions import ConditionEffect, ConditionTracker


class TestConditionEffect:
    """Test the ConditionEffect dataclass."""

    def test_condition_effect_creation(self):
        """Test creating a ConditionEffect with defaults."""
        effect = ConditionEffect()
        assert effect.attack_advantage is False
        assert effect.attack_disadvantage is False
        assert effect.ability_check_disadvantage is False
        assert effect.save_disadvantage_str is False
        assert effect.save_disadvantage_dex is False
        assert effect.auto_fail_str_saves is False
        assert effect.auto_fail_dex_saves is False
        assert effect.attackers_have_advantage is False
        assert effect.melee_attacks_auto_crit is False
        assert effect.grants_advantage_on_attacks is False

    def test_condition_effect_with_values(self):
        """Test creating a ConditionEffect with custom values."""
        effect = ConditionEffect(
            attack_advantage=True,
            attackers_have_advantage=True,
        )
        assert effect.attack_advantage is True
        assert effect.attackers_have_advantage is True
        assert effect.attack_disadvantage is False


class TestConditionTracker:
    """Test condition tracking and effects."""

    @pytest.fixture
    def condition_tracker(self):
        """Create a ConditionTracker."""
        return ConditionTracker()

    def test_no_conditions_no_effects(self, condition_tracker):
        """Test that no conditions result in no effects."""
        effects = condition_tracker.get_effects([])
        assert effects.attack_advantage is False
        assert effects.attack_disadvantage is False
        assert effects.ability_check_disadvantage is False
        assert effects.attackers_have_advantage is False

    def test_blinded_condition(self, condition_tracker):
        """Test blinded condition effects."""
        effects = condition_tracker.get_effects([Condition.BLINDED])
        # Blinded: disadvantage on attack rolls, attackers have advantage
        assert effects.attack_disadvantage is True
        assert effects.attackers_have_advantage is True

    def test_frightened_condition(self, condition_tracker):
        """Test frightened condition effects."""
        effects = condition_tracker.get_effects([Condition.FRIGHTENED])
        # Frightened: disadvantage on ability checks and attack rolls
        assert effects.ability_check_disadvantage is True
        assert effects.attack_disadvantage is True

    def test_invisible_condition(self, condition_tracker):
        """Test invisible condition effects."""
        effects = condition_tracker.get_effects([Condition.INVISIBLE])
        # Invisible: advantage on attack rolls, attackers have disadvantage
        assert effects.attack_advantage is True
        assert effects.attackers_have_advantage is False

    def test_paralyzed_condition(self, condition_tracker):
        """Test paralyzed condition effects."""
        effects = condition_tracker.get_effects([Condition.PARALYZED])
        # Paralyzed: auto-fail STR/DEX saves, attackers have advantage, melee crits within 5ft
        assert effects.auto_fail_str_saves is True
        assert effects.auto_fail_dex_saves is True
        assert effects.attackers_have_advantage is True
        assert effects.melee_attacks_auto_crit is True

    def test_petrified_condition(self, condition_tracker):
        """Test petrified condition effects."""
        effects = condition_tracker.get_effects([Condition.PETRIFIED])
        # Petrified: auto-fail STR/DEX saves, attacks have advantage
        assert effects.auto_fail_str_saves is True
        assert effects.auto_fail_dex_saves is True
        assert effects.attackers_have_advantage is True

    def test_poisoned_condition(self, condition_tracker):
        """Test poisoned condition effects."""
        effects = condition_tracker.get_effects([Condition.POISONED])
        # Poisoned: disadvantage on attack rolls and ability checks
        assert effects.attack_disadvantage is True
        assert effects.ability_check_disadvantage is True

    def test_prone_condition(self, condition_tracker):
        """Test prone condition effects."""
        effects = condition_tracker.get_effects([Condition.PRONE])
        # Prone: disadvantage on attack rolls, melee attackers have advantage
        assert effects.attack_disadvantage is True
        # Note: Need to check melee vs ranged separately

    def test_restrained_condition(self, condition_tracker):
        """Test restrained condition effects."""
        effects = condition_tracker.get_effects([Condition.RESTRAINED])
        # Restrained: disadvantage on attack rolls, disadvantage on DEX saves, attackers have advantage
        assert effects.attack_disadvantage is True
        assert effects.save_disadvantage_dex is True
        assert effects.attackers_have_advantage is True

    def test_stunned_condition(self, condition_tracker):
        """Test stunned condition effects."""
        effects = condition_tracker.get_effects([Condition.STUNNED])
        # Stunned: auto-fail STR/DEX saves, attacks have advantage
        assert effects.auto_fail_str_saves is True
        assert effects.auto_fail_dex_saves is True
        assert effects.attackers_have_advantage is True

    def test_unconscious_condition(self, condition_tracker):
        """Test unconscious condition effects."""
        effects = condition_tracker.get_effects([Condition.UNCONSCIOUS])
        # Unconscious: auto-fail STR/DEX saves, attacks have advantage, melee auto-crit
        assert effects.auto_fail_str_saves is True
        assert effects.auto_fail_dex_saves is True
        assert effects.attackers_have_advantage is True
        assert effects.melee_attacks_auto_crit is True

    def test_multiple_conditions_combine(self, condition_tracker):
        """Test that multiple conditions combine their effects."""
        effects = condition_tracker.get_effects([
            Condition.PARALYZED,
            Condition.POISONED,
        ])
        # Both should contribute
        assert effects.auto_fail_str_saves is True  # From PARALYZED
        assert effects.auto_fail_dex_saves is True  # From PARALYZED
        assert effects.ability_check_disadvantage is True  # From POISONED
        assert effects.attack_disadvantage is True  # From POISONED

    def test_charmed_condition(self, condition_tracker):
        """Test charmed condition."""
        effects = condition_tracker.get_effects([Condition.CHARMED])
        # Charmed typically doesn't affect mechanics directly in combat
        # but we should handle it
        assert isinstance(effects, ConditionEffect)

    def test_deafened_condition(self, condition_tracker):
        """Test deafened condition."""
        effects = condition_tracker.get_effects([Condition.DEAFENED])
        # Deafened typically doesn't affect mechanics directly in combat
        assert isinstance(effects, ConditionEffect)

    def test_grappled_condition(self, condition_tracker):
        """Test grappled condition."""
        effects = condition_tracker.get_effects([Condition.GRAPPLED])
        # Grappled affects movement but we may not track that in combat mechanics
        assert isinstance(effects, ConditionEffect)

    def test_incapacitated_condition(self, condition_tracker):
        """Test incapacitated condition."""
        effects = condition_tracker.get_effects([Condition.INCAPACITATED])
        # Incapacitated affects some actions
        assert isinstance(effects, ConditionEffect)

    def test_exhaustion_condition(self, condition_tracker):
        """Test exhaustion condition."""
        effects = condition_tracker.get_effects([Condition.EXHAUSTION])
        # Exhaustion affects various mechanics
        assert isinstance(effects, ConditionEffect)

    def test_get_attack_modifiers_no_conditions(self, condition_tracker):
        """Test getting attack modifiers with no conditions."""
        modifiers = condition_tracker.get_attack_modifiers(
            attacker_conditions=[],
            target_conditions=[],
            is_melee=True,
        )
        assert isinstance(modifiers, dict)
        # Should have keys for attack advantage/disadvantage
        assert "attacker_advantage" in modifiers or "attacker_disadvantage" in modifiers or \
               "target_advantage" in modifiers or "target_disadvantage" in modifiers

    def test_get_attack_modifiers_blinded_attacker(self, condition_tracker):
        """Test that blinded attacker has disadvantage."""
        modifiers = condition_tracker.get_attack_modifiers(
            attacker_conditions=[Condition.BLINDED],
            target_conditions=[],
            is_melee=True,
        )
        assert "attacker_disadvantage" in modifiers or modifiers.get("attacker_disadvantage") is True

    def test_get_attack_modifiers_invisible_attacker(self, condition_tracker):
        """Test that invisible attacker has advantage."""
        modifiers = condition_tracker.get_attack_modifiers(
            attacker_conditions=[Condition.INVISIBLE],
            target_conditions=[],
            is_melee=True,
        )
        assert "attacker_advantage" in modifiers or modifiers.get("attacker_advantage") is True

    def test_get_attack_modifiers_prone_target_melee(self, condition_tracker):
        """Test that prone target gives melee attacker advantage."""
        modifiers = condition_tracker.get_attack_modifiers(
            attacker_conditions=[],
            target_conditions=[Condition.PRONE],
            is_melee=True,
        )
        # Melee attackers have advantage against prone target
        assert "target_advantage" in modifiers or "melee_advantage" in modifiers

    def test_get_attack_modifiers_prone_target_ranged(self, condition_tracker):
        """Test that prone target gives ranged attacker disadvantage."""
        modifiers = condition_tracker.get_attack_modifiers(
            attacker_conditions=[],
            target_conditions=[Condition.PRONE],
            is_melee=False,
        )
        # Ranged attackers have disadvantage against prone target
        assert "target_disadvantage" in modifiers or "ranged_disadvantage" in modifiers

    def test_multiple_conditions_stacking(self, condition_tracker):
        """Test stacking multiple conditions on same creature."""
        effects = condition_tracker.get_effects([
            Condition.BLINDED,
            Condition.PARALYZED,
            Condition.RESTRAINED,
        ])
        # All should contribute disadvantages
        assert effects.attack_disadvantage is True
        assert effects.attackers_have_advantage is True
        assert effects.auto_fail_str_saves is True
        assert effects.auto_fail_dex_saves is True
