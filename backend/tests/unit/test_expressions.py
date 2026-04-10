"""Tests for avatar expression mapping — TDD: write tests first."""
import pytest
from app.services.avatar.expressions import (
    Expression,
    ExpressionMapper,
    AvatarState,
    GazeDirection,
)


class TestExpression:
    """Test the Expression enum."""

    def test_has_standard_expressions(self):
        assert Expression.NEUTRAL
        assert Expression.HAPPY
        assert Expression.ANGRY
        assert Expression.SAD
        assert Expression.SURPRISED
        assert Expression.THINKING
        assert Expression.MENACING
        assert Expression.EXCITED

    def test_expression_values_are_strings(self):
        assert isinstance(Expression.NEUTRAL.value, str)


class TestGazeDirection:
    """Test gaze direction enum."""

    def test_has_directions(self):
        assert GazeDirection.CENTER
        assert GazeDirection.LEFT
        assert GazeDirection.RIGHT
        assert GazeDirection.UP
        assert GazeDirection.DOWN


class TestAvatarState:
    """Test the avatar state dataclass."""

    def test_default_state(self):
        state = AvatarState()
        assert state.expression == Expression.NEUTRAL
        assert state.is_speaking is False
        assert state.mouth_amplitude == 0.0
        assert state.gaze == GazeDirection.CENTER

    def test_speaking_state(self):
        state = AvatarState(
            expression=Expression.EXCITED,
            is_speaking=True,
            mouth_amplitude=0.7,
            gaze=GazeDirection.LEFT,
        )
        assert state.expression == Expression.EXCITED
        assert state.is_speaking is True
        assert state.mouth_amplitude == 0.7

    def test_to_dict(self):
        state = AvatarState(expression=Expression.HAPPY)
        d = state.to_dict()
        assert d["expression"] == "happy"
        assert d["is_speaking"] is False
        assert "mouth_amplitude" in d
        assert "gaze" in d


class TestExpressionMapper:
    """Test mapping game context to expressions."""

    def test_combat_maps_to_menacing_or_excited(self):
        mapper = ExpressionMapper()
        expr = mapper.from_game_context(phase="combat", narration_type="attack")
        assert expr in (Expression.MENACING, Expression.EXCITED, Expression.ANGRY)

    def test_exploration_maps_to_neutral_or_thinking(self):
        mapper = ExpressionMapper()
        expr = mapper.from_game_context(phase="exploration", narration_type="description")
        assert expr in (Expression.NEUTRAL, Expression.THINKING)

    def test_tavern_dialogue_maps_to_happy(self):
        mapper = ExpressionMapper()
        expr = mapper.from_game_context(phase="dialogue", narration_type="friendly_npc")
        assert expr in (Expression.HAPPY, Expression.NEUTRAL)

    def test_danger_maps_to_menacing(self):
        mapper = ExpressionMapper()
        expr = mapper.from_game_context(phase="combat", narration_type="danger")
        assert expr == Expression.MENACING

    def test_surprise_maps_correctly(self):
        mapper = ExpressionMapper()
        expr = mapper.from_game_context(phase="exploration", narration_type="surprise")
        assert expr == Expression.SURPRISED

    def test_sad_moment(self):
        mapper = ExpressionMapper()
        expr = mapper.from_game_context(phase="dialogue", narration_type="sad")
        assert expr == Expression.SAD

    def test_player_success_maps_to_happy(self):
        mapper = ExpressionMapper()
        expr = mapper.from_game_context(phase="combat", narration_type="player_success")
        assert expr in (Expression.HAPPY, Expression.EXCITED)

    def test_unknown_context_defaults_to_neutral(self):
        mapper = ExpressionMapper()
        expr = mapper.from_game_context(phase="unknown", narration_type="unknown")
        assert expr == Expression.NEUTRAL

    def test_from_text_sentiment_excited(self):
        mapper = ExpressionMapper()
        expr = mapper.from_text_sentiment("You found a legendary sword! Amazing!")
        assert expr in (Expression.EXCITED, Expression.SURPRISED, Expression.HAPPY)

    def test_from_text_sentiment_danger(self):
        mapper = ExpressionMapper()
        expr = mapper.from_text_sentiment("The dragon roars and flames engulf the corridor!")
        assert expr in (Expression.MENACING, Expression.ANGRY, Expression.SURPRISED)

    def test_from_text_sentiment_neutral(self):
        mapper = ExpressionMapper()
        expr = mapper.from_text_sentiment("You walk down the road.")
        assert expr == Expression.NEUTRAL
