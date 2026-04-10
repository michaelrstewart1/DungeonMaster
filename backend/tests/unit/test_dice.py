"""
Comprehensive tests for D&D 5e dice rolling system using TDD.
RED phase: Tests first, then implementation.
"""
import pytest
from app.services.dice import DiceRoller, DiceResult


class TestBasicDiceRolling:
    """Test basic dice rolling for all standard dice types."""

    @pytest.mark.parametrize("die_type,min_val,max_val", [
        ("d4", 1, 4),
        ("d6", 1, 6),
        ("d8", 1, 8),
        ("d10", 1, 10),
        ("d12", 1, 12),
        ("d20", 1, 20),
        ("d100", 1, 100),
    ])
    def test_single_die_roll_within_range(self, die_type, min_val, max_val):
        """Each die roll should return a value within valid range."""
        roller = DiceRoller(seed=42)
        result = roller.roll(f"1{die_type}")
        
        assert min_val <= result.total <= max_val
        assert len(result.rolls) == 1
        assert result.rolls[0] == result.total

    @pytest.mark.parametrize("die_type", ["d4", "d6", "d8", "d10", "d12", "d20", "d100"])
    def test_deterministic_rolls_with_seed(self, die_type):
        """Same seed should produce same results."""
        roller1 = DiceRoller(seed=12345)
        result1 = roller1.roll(f"1{die_type}")
        
        roller2 = DiceRoller(seed=12345)
        result2 = roller2.roll(f"1{die_type}")
        
        assert result1.total == result2.total
        assert result1.rolls == result2.rolls


class TestDiceNotationParsing:
    """Test parsing of dice notation strings."""

    def test_parse_simple_notation(self):
        """Parse simple notation like '1d20'."""
        roller = DiceRoller(seed=42)
        result = roller.roll("1d20")
        
        assert result.notation == "1d20"
        assert len(result.rolls) == 1
        assert 1 <= result.total <= 20
        assert result.modifier == 0

    def test_parse_multiple_dice_notation(self):
        """Parse notation with multiple dice like '2d6'."""
        roller = DiceRoller(seed=42)
        result = roller.roll("2d6")
        
        assert result.notation == "2d6"
        assert len(result.rolls) == 2
        assert 2 <= result.total <= 12
        assert result.modifier == 0

    def test_parse_notation_with_positive_modifier(self):
        """Parse notation with positive modifier like '1d20+5'."""
        roller = DiceRoller(seed=42)
        result = roller.roll("1d20+5")
        
        assert result.notation == "1d20+5"
        assert result.modifier == 5
        assert 6 <= result.total <= 25  # 1-20 + 5

    def test_parse_notation_with_negative_modifier(self):
        """Parse notation with negative modifier like '2d6-2'."""
        roller = DiceRoller(seed=42)
        result = roller.roll("2d6-2")
        
        assert result.notation == "2d6-2"
        assert result.modifier == -2
        assert 0 <= result.total <= 10  # 2-12 - 2

    def test_parse_notation_with_spaces(self):
        """Parse notation with spaces."""
        roller = DiceRoller(seed=42)
        result = roller.roll("2d6 + 3")
        
        assert result.modifier == 3
        assert result.total == sum(result.rolls) + 3


class TestMultipleDice:
    """Test rolling multiple dice and summing them."""

    def test_roll_multiple_dice(self):
        """Roll multiple dice and return individual rolls and total."""
        roller = DiceRoller(seed=42)
        result = roller.roll("4d6")
        
        assert len(result.rolls) == 4
        assert all(1 <= roll <= 6 for roll in result.rolls)
        assert result.total == sum(result.rolls)
        assert 4 <= result.total <= 24

    def test_roll_3d8(self):
        """Roll 3d8."""
        roller = DiceRoller(seed=99)
        result = roller.roll("3d8")
        
        assert len(result.rolls) == 3
        assert all(1 <= roll <= 8 for roll in result.rolls)
        assert result.total == sum(result.rolls)
        assert 3 <= result.total <= 24

    def test_multiple_dice_with_modifier(self):
        """Roll multiple dice with modifier."""
        roller = DiceRoller(seed=42)
        result = roller.roll("3d6+2")
        
        assert len(result.rolls) == 3
        assert result.modifier == 2
        assert result.total == sum(result.rolls) + 2
        assert 5 <= result.total <= 20


class TestModifiers:
    """Test that modifiers are applied correctly."""

    def test_positive_modifier_applied_to_total(self):
        """Positive modifier should be applied to total, not each die."""
        roller = DiceRoller(seed=42)
        result = roller.roll("1d20+7")
        
        assert result.rolls[0] >= 1
        assert result.rolls[0] <= 20
        assert result.total == result.rolls[0] + 7

    def test_negative_modifier_applied_to_total(self):
        """Negative modifier should be applied to total."""
        roller = DiceRoller(seed=42)
        result = roller.roll("1d20-3")
        
        assert result.rolls[0] >= 1
        assert result.rolls[0] <= 20
        assert result.total == result.rolls[0] - 3

    def test_large_positive_modifier(self):
        """Handle large positive modifiers."""
        roller = DiceRoller(seed=42)
        result = roller.roll("1d6+20")
        
        assert result.modifier == 20
        assert result.total == result.rolls[0] + 20
        assert 21 <= result.total <= 26

    def test_large_negative_modifier(self):
        """Handle large negative modifiers that could go negative."""
        roller = DiceRoller(seed=42)
        result = roller.roll("1d6-10")
        
        assert result.modifier == -10
        assert result.total == result.rolls[0] - 10
        # Total could be negative


class TestCriticalHits:
    """Test critical hit detection."""

    def test_natural_20_on_d20_is_critical(self):
        """Rolling a natural 20 on d20 should flag as critical."""
        roller = DiceRoller(seed=42)
        # Keep rolling until we get a 20 or seed different values
        result = roller.roll("1d20")
        
        if result.rolls[0] == 20:
            assert result.is_critical is True
        else:
            assert result.is_critical is False

    def test_critical_with_modifier(self):
        """Natural 20 with modifier should still be marked as critical."""
        roller = DiceRoller(seed=42)
        result = roller.roll("1d20+5")
        
        if result.rolls[0] == 20:
            assert result.is_critical is True
            assert result.total == 25

    def test_natural_20_on_non_d20_not_critical(self):
        """Natural 20 on d100 should still be flagged as critical."""
        roller = DiceRoller(seed=42)
        result = roller.roll("1d100")
        
        if result.rolls[0] == 20:
            # Only d20 rolls should be flagged as critical
            assert result.is_critical is False

    def test_natural_1_on_d20_is_fumble(self):
        """Rolling a natural 1 on d20 should flag as fumble."""
        roller = DiceRoller(seed=42)
        result = roller.roll("1d20")
        
        if result.rolls[0] == 1:
            assert result.is_fumble is True
        else:
            assert result.is_fumble is False

    def test_fumble_with_modifier(self):
        """Natural 1 with modifier should still be marked as fumble."""
        roller = DiceRoller(seed=42)
        result = roller.roll("1d20+3")
        
        if result.rolls[0] == 1:
            assert result.is_fumble is True
            assert result.total == 4


class TestAdvantageDisadvantage:
    """Test advantage and disadvantage rolls (roll 2d20, take highest/lowest)."""

    def test_roll_with_advantage(self):
        """Roll with advantage should roll 2d20 and take the highest."""
        roller = DiceRoller(seed=42)
        result = roller.roll_with_advantage()
        
        assert len(result.rolls) == 2
        assert all(1 <= roll <= 20 for roll in result.rolls)
        assert result.total == max(result.rolls)

    def test_roll_with_disadvantage(self):
        """Roll with disadvantage should roll 2d20 and take the lowest."""
        roller = DiceRoller(seed=42)
        result = roller.roll_with_disadvantage()
        
        assert len(result.rolls) == 2
        assert all(1 <= roll <= 20 for roll in result.rolls)
        assert result.total == min(result.rolls)

    def test_advantage_deterministic_with_seed(self):
        """Advantage rolls with same seed should produce same results."""
        roller1 = DiceRoller(seed=555)
        result1 = roller1.roll_with_advantage()
        
        roller2 = DiceRoller(seed=555)
        result2 = roller2.roll_with_advantage()
        
        assert result1.rolls == result2.rolls
        assert result1.total == result2.total

    def test_disadvantage_deterministic_with_seed(self):
        """Disadvantage rolls with same seed should produce same results."""
        roller1 = DiceRoller(seed=777)
        result1 = roller1.roll_with_disadvantage()
        
        roller2 = DiceRoller(seed=777)
        result2 = roller2.roll_with_disadvantage()
        
        assert result1.rolls == result2.rolls
        assert result1.total == result2.total

    def test_advantage_critical_on_natural_20(self):
        """If either roll is 20 with advantage, should be marked critical."""
        roller = DiceRoller(seed=42)
        # Test multiple times to potentially hit a 20
        for _ in range(10):
            result = roller.roll_with_advantage()
            if 20 in result.rolls:
                assert result.is_critical is True
                break


class TestDropLowest:
    """Test drop lowest dice (for ability score generation: 4d6 drop lowest)."""

    def test_roll_4d6_drop_lowest(self):
        """Roll 4d6 and drop the lowest die."""
        roller = DiceRoller(seed=42)
        result = roller.roll("4d6 drop lowest")
        
        # Should have 4 dice rolled
        assert len(result.rolls) == 4
        # Should have 1 die in dropped
        assert len(result.dropped) == 1
        # Dropped should be the minimum
        assert result.dropped[0] == min(result.rolls)
        # Total should be sum of 3 highest dice
        all_sorted = sorted(result.rolls)
        assert result.total == sum(all_sorted[1:])  # Skip the lowest
        # Total should be between 3 and 18 (1+2+3 to 6+6+6)
        assert 3 <= result.total <= 18

    def test_roll_ability_scores(self):
        """Roll all 6 ability scores using 4d6 drop lowest."""
        roller = DiceRoller(seed=42)
        scores = roller.roll_ability_scores()
        
        assert len(scores) == 6
        assert all(3 <= score <= 18 for score in scores)

    def test_drop_lowest_with_seed_deterministic(self):
        """4d6 drop lowest with same seed should produce same results."""
        roller1 = DiceRoller(seed=123)
        result1 = roller1.roll("4d6 drop lowest")
        
        roller2 = DiceRoller(seed=123)
        result2 = roller2.roll("4d6 drop lowest")
        
        assert result1.rolls == result2.rolls
        assert result1.dropped == result2.dropped
        assert result1.total == result2.total

    def test_ability_scores_deterministic(self):
        """Ability scores with same seed should produce same results."""
        roller1 = DiceRoller(seed=999)
        scores1 = roller1.roll_ability_scores()
        
        roller2 = DiceRoller(seed=999)
        scores2 = roller2.roll_ability_scores()
        
        assert scores1 == scores2


class TestDiceResultDataclass:
    """Test the DiceResult dataclass."""

    def test_dice_result_has_required_fields(self):
        """DiceResult should have all required fields."""
        roller = DiceRoller(seed=42)
        result = roller.roll("1d20+5")
        
        assert hasattr(result, 'notation')
        assert hasattr(result, 'rolls')
        assert hasattr(result, 'modifier')
        assert hasattr(result, 'total')
        assert hasattr(result, 'is_critical')
        assert hasattr(result, 'is_fumble')
        assert hasattr(result, 'dropped')

    def test_dice_result_no_dropped_for_normal_roll(self):
        """Normal rolls should have empty dropped list."""
        roller = DiceRoller(seed=42)
        result = roller.roll("1d20")
        
        assert result.dropped == []


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_large_number_of_dice(self):
        """Handle rolling many dice."""
        roller = DiceRoller(seed=42)
        result = roller.roll("20d6")
        
        assert len(result.rolls) == 20
        assert all(1 <= roll <= 6 for roll in result.rolls)
        assert 20 <= result.total <= 120

    def test_zero_modifier(self):
        """Explicitly testing zero modifier."""
        roller = DiceRoller(seed=42)
        result = roller.roll("1d20+0")
        
        assert result.modifier == 0
        assert result.total == result.rolls[0]

    def test_invalid_notation_raises_error(self):
        """Invalid notation should raise an error."""
        roller = DiceRoller(seed=42)
        
        with pytest.raises(ValueError):
            roller.roll("invalid")

    def test_invalid_dice_type_raises_error(self):
        """Invalid dice type should raise an error."""
        roller = DiceRoller(seed=42)
        
        with pytest.raises(ValueError):
            roller.roll("1d99")

    def test_multiple_modifiers_in_notation(self):
        """Should handle notation with multiple operators (first one wins or error)."""
        roller = DiceRoller(seed=42)
        
        # This should either error or use the first modifier
        # Implementation decision: error out on invalid notation
        with pytest.raises(ValueError):
            roller.roll("1d20+5-3")


class TestRollerIntegration:
    """Integration tests combining multiple features."""

    def test_complex_roll_sequence(self):
        """Test a sequence of different roll types."""
        roller = DiceRoller(seed=42)
        
        result1 = roller.roll("2d6+3")
        assert 5 <= result1.total <= 15
        
        result2 = roller.roll_with_advantage()
        assert len(result2.rolls) == 2
        
        result3 = roller.roll("4d6 drop lowest")
        assert 3 <= result3.total <= 18

    def test_attack_roll_scenario(self):
        """Simulate attack roll: 1d20 + modifier."""
        roller = DiceRoller(seed=42)
        attack_bonus = 5
        result = roller.roll(f"1d20+{attack_bonus}")
        
        assert result.rolls[0] >= 1
        assert result.total >= 1 + attack_bonus
        if result.rolls[0] == 20:
            assert result.is_critical is True

    def test_damage_roll_scenario(self):
        """Simulate damage roll: 2d6+2 (sword + strength modifier)."""
        roller = DiceRoller(seed=42)
        result = roller.roll("2d6+2")
        
        assert len(result.rolls) == 2
        assert 4 <= result.total <= 14

    def test_ability_score_array_generation(self):
        """Generate full ability score array for character creation."""
        roller = DiceRoller(seed=12345)
        scores = roller.roll_ability_scores()
        
        assert len(scores) == 6
        assert all(3 <= score <= 18 for score in scores)
        # Ability scores typically have a reasonable distribution
        assert min(scores) >= 3
        assert max(scores) <= 18
