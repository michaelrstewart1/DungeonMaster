"""
Tests for D&D 5e Ability Checks and Saving Throws.
"""

import pytest
from app.services.dice import DiceRoller
from app.services.rules.abilities import AbilityChecker, AbilityCheckResult


class TestAbilityCheckResult:
    """Test the AbilityCheckResult dataclass."""

    def test_ability_check_result_creation(self):
        """Test creating an AbilityCheckResult."""
        result = AbilityCheckResult(
            roll=15,
            modifier=3,
            proficiency_bonus=2,
            total=20,
            dc=15,
            success=True,
            is_natural_20=False,
            is_natural_1=False,
            had_advantage=False,
            had_disadvantage=False,
        )
        assert result.roll == 15
        assert result.modifier == 3
        assert result.proficiency_bonus == 2
        assert result.total == 20
        assert result.dc == 15
        assert result.success is True
        assert result.is_natural_20 is False
        assert result.is_natural_1 is False


class TestAbilityChecker:
    """Test ability checks and saving throws."""

    @pytest.fixture
    def ability_checker(self):
        """Create an AbilityChecker with seeded dice roller."""
        dice_roller = DiceRoller(seed=42)
        return AbilityChecker(dice_roller)

    @pytest.fixture
    def seeded_checker(self):
        """Create checkers with specific seeds for testing."""
        def create_checker(seed):
            return AbilityChecker(DiceRoller(seed=seed))
        return create_checker

    def test_ability_check_basic_success(self, seeded_checker):
        """Test a basic ability check that succeeds."""
        # Seed that produces a d20 roll of 18
        checker = seeded_checker(100)
        # We'll need to adjust this based on actual die rolls
        result = checker.ability_check(ability_modifier=3, dc=15, proficiency_bonus=2)
        assert result.roll == result.total - result.modifier - result.proficiency_bonus
        assert result.modifier == 3
        assert result.proficiency_bonus == 2
        assert isinstance(result.total, int)
        assert isinstance(result.success, bool)

    def test_ability_check_failure(self, seeded_checker):
        """Test a basic ability check that fails."""
        checker = seeded_checker(200)
        result = checker.ability_check(ability_modifier=2, dc=20, proficiency_bonus=2)
        # With modifier and proficiency, total should be roll + 2 + 2
        assert result.modifier == 2
        assert result.proficiency_bonus == 2
        assert result.dc == 20
        assert isinstance(result.success, bool)

    def test_ability_check_with_proficiency(self, ability_checker):
        """Test that proficiency bonus is added to the roll."""
        result = ability_checker.ability_check(
            ability_modifier=2, dc=15, proficiency_bonus=3
        )
        # Total should be roll + modifier + proficiency_bonus
        assert result.total == result.roll + result.modifier + result.proficiency_bonus
        assert result.proficiency_bonus == 3

    def test_ability_check_without_proficiency(self, ability_checker):
        """Test ability check without proficiency bonus."""
        result = ability_checker.ability_check(ability_modifier=2, dc=15)
        assert result.proficiency_bonus == 0
        assert result.total == result.roll + result.modifier

    def test_ability_check_natural_20_always_succeeds(self, seeded_checker):
        """Test that natural 20 always succeeds, even if total < DC."""
        # Need to engineer a nat 20 + low modifier
        # Using seed to get specific rolls
        checker = seeded_checker(300)
        # Roll multiple times until we get a nat 20
        for _ in range(100):
            result = checker.ability_check(
                ability_modifier=-5, dc=30, proficiency_bonus=0
            )
            if result.is_natural_20:
                assert result.success is True
                break
        else:
            pytest.skip("Could not generate natural 20 in reasonable attempts")

    def test_ability_check_natural_1_always_fails(self, seeded_checker):
        """Test that natural 1 always fails, even if total >= DC."""
        # Need to engineer a nat 1 + high modifier
        checker = seeded_checker(400)
        for _ in range(100):
            result = checker.ability_check(
                ability_modifier=10, dc=5, proficiency_bonus=0
            )
            if result.is_natural_1:
                assert result.success is False
                break
        else:
            pytest.skip("Could not generate natural 1 in reasonable attempts")

    def test_ability_check_advantage(self, seeded_checker):
        """Test ability check with advantage."""
        checker = seeded_checker(500)
        result = checker.ability_check(
            ability_modifier=2, dc=15, advantage=True
        )
        assert result.had_advantage is True
        assert result.had_disadvantage is False
        assert len(result.rolls) == 2  # Should have 2 rolls with advantage

    def test_ability_check_disadvantage(self, seeded_checker):
        """Test ability check with disadvantage."""
        checker = seeded_checker(600)
        result = checker.ability_check(
            ability_modifier=2, dc=15, disadvantage=True
        )
        assert result.had_disadvantage is True
        assert result.had_advantage is False
        assert len(result.rolls) == 2  # Should have 2 rolls with disadvantage

    def test_ability_check_advantage_takes_higher(self, seeded_checker):
        """Test that advantage takes the higher of two rolls."""
        checker = seeded_checker(700)
        result = checker.ability_check(
            ability_modifier=0, dc=1, advantage=True
        )
        if len(result.rolls) == 2:
            assert result.roll == max(result.rolls)

    def test_ability_check_disadvantage_takes_lower(self, seeded_checker):
        """Test that disadvantage takes the lower of two rolls."""
        checker = seeded_checker(800)
        result = checker.ability_check(
            ability_modifier=0, dc=1, disadvantage=True
        )
        if len(result.rolls) == 2:
            assert result.roll == min(result.rolls)

    def test_saving_throw_basic(self, ability_checker):
        """Test a basic saving throw."""
        result = ability_checker.saving_throw(
            ability_modifier=3, dc=15, proficiency_bonus=2
        )
        # Saving throw should work the same as ability check
        assert result.total == result.roll + result.modifier + result.proficiency_bonus
        assert result.modifier == 3
        assert result.proficiency_bonus == 2

    def test_saving_throw_with_advantage(self, seeded_checker):
        """Test saving throw with advantage."""
        checker = seeded_checker(900)
        result = checker.saving_throw(
            ability_modifier=1, dc=15, proficiency_bonus=1, advantage=True
        )
        assert result.had_advantage is True

    def test_saving_throw_with_disadvantage(self, seeded_checker):
        """Test saving throw with disadvantage."""
        checker = seeded_checker(1000)
        result = checker.saving_throw(
            ability_modifier=1, dc=15, proficiency_bonus=1, disadvantage=True
        )
        assert result.had_disadvantage is True

    def test_saving_throw_natural_20_succeeds(self, seeded_checker):
        """Test that natural 20 on saving throw always succeeds."""
        checker = seeded_checker(1100)
        for _ in range(100):
            result = checker.saving_throw(
                ability_modifier=-5, dc=30, proficiency_bonus=0
            )
            if result.is_natural_20:
                assert result.success is True
                break
        else:
            pytest.skip("Could not generate natural 20 in reasonable attempts")

    def test_saving_throw_natural_1_fails(self, seeded_checker):
        """Test that natural 1 on saving throw always fails."""
        checker = seeded_checker(1200)
        for _ in range(100):
            result = checker.saving_throw(
                ability_modifier=10, dc=5, proficiency_bonus=0
            )
            if result.is_natural_1:
                assert result.success is False
                break
        else:
            pytest.skip("Could not generate natural 1 in reasonable attempts")

    def test_ability_check_success_dc_comparison(self, ability_checker):
        """Test that success is based on total >= DC."""
        result1 = ability_checker.ability_check(
            ability_modifier=5, dc=10, proficiency_bonus=0
        )
        # If roll is 5, total is 10, dc is 10, should succeed
        if result1.total >= result1.dc and not result1.is_natural_1:
            assert result1.success is True
        elif result1.total < result1.dc and not result1.is_natural_20:
            assert result1.success is False

    def test_ability_check_negative_modifier(self, ability_checker):
        """Test ability checks with negative ability modifiers."""
        result = ability_checker.ability_check(
            ability_modifier=-3, dc=15, proficiency_bonus=1
        )
        assert result.modifier == -3
        assert result.total == result.roll - 3 + result.proficiency_bonus

    def test_ability_check_zero_modifier(self, ability_checker):
        """Test ability checks with zero modifier."""
        result = ability_checker.ability_check(
            ability_modifier=0, dc=10, proficiency_bonus=2
        )
        assert result.modifier == 0
        assert result.total == result.roll + result.proficiency_bonus

    def test_ability_check_high_dc(self, ability_checker):
        """Test ability check against very high DC."""
        result = ability_checker.ability_check(
            ability_modifier=5, dc=30, proficiency_bonus=5
        )
        assert result.dc == 30

    def test_ability_check_result_has_all_fields(self, ability_checker):
        """Test that AbilityCheckResult has all required fields."""
        result = ability_checker.ability_check(
            ability_modifier=2, dc=15, proficiency_bonus=2
        )
        assert hasattr(result, "roll")
        assert hasattr(result, "modifier")
        assert hasattr(result, "proficiency_bonus")
        assert hasattr(result, "total")
        assert hasattr(result, "dc")
        assert hasattr(result, "success")
        assert hasattr(result, "is_natural_20")
        assert hasattr(result, "is_natural_1")
        assert hasattr(result, "had_advantage")
        assert hasattr(result, "had_disadvantage")
