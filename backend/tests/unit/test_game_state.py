"""Tests for game state machine — written FIRST (TDD RED phase)."""

import pytest
from app.services.game.state import GameStateMachine, GamePhase, InvalidTransitionError


class TestGamePhases:
    """Test that all game phases are defined."""

    def test_lobby_phase_exists(self):
        assert GamePhase.LOBBY is not None

    def test_exploration_phase_exists(self):
        assert GamePhase.EXPLORATION is not None

    def test_combat_phase_exists(self):
        assert GamePhase.COMBAT is not None

    def test_rest_phase_exists(self):
        assert GamePhase.REST is not None

    def test_shopping_phase_exists(self):
        assert GamePhase.SHOPPING is not None

    def test_dialogue_phase_exists(self):
        assert GamePhase.DIALOGUE is not None


class TestGameStateMachine:
    """Test state machine transitions."""

    def test_initial_state_is_lobby(self):
        sm = GameStateMachine()
        assert sm.current_phase == GamePhase.LOBBY

    def test_transition_lobby_to_exploration(self):
        sm = GameStateMachine()
        sm.transition_to(GamePhase.EXPLORATION)
        assert sm.current_phase == GamePhase.EXPLORATION

    def test_transition_exploration_to_combat(self):
        sm = GameStateMachine()
        sm.transition_to(GamePhase.EXPLORATION)
        sm.transition_to(GamePhase.COMBAT)
        assert sm.current_phase == GamePhase.COMBAT

    def test_transition_combat_to_exploration(self):
        sm = GameStateMachine()
        sm.transition_to(GamePhase.EXPLORATION)
        sm.transition_to(GamePhase.COMBAT)
        sm.transition_to(GamePhase.EXPLORATION)
        assert sm.current_phase == GamePhase.EXPLORATION

    def test_transition_exploration_to_rest(self):
        sm = GameStateMachine()
        sm.transition_to(GamePhase.EXPLORATION)
        sm.transition_to(GamePhase.REST)
        assert sm.current_phase == GamePhase.REST

    def test_transition_exploration_to_shopping(self):
        sm = GameStateMachine()
        sm.transition_to(GamePhase.EXPLORATION)
        sm.transition_to(GamePhase.SHOPPING)
        assert sm.current_phase == GamePhase.SHOPPING

    def test_transition_exploration_to_dialogue(self):
        sm = GameStateMachine()
        sm.transition_to(GamePhase.EXPLORATION)
        sm.transition_to(GamePhase.DIALOGUE)
        assert sm.current_phase == GamePhase.DIALOGUE

    def test_transition_rest_to_exploration(self):
        sm = GameStateMachine()
        sm.transition_to(GamePhase.EXPLORATION)
        sm.transition_to(GamePhase.REST)
        sm.transition_to(GamePhase.EXPLORATION)
        assert sm.current_phase == GamePhase.EXPLORATION

    def test_transition_shopping_to_exploration(self):
        sm = GameStateMachine()
        sm.transition_to(GamePhase.EXPLORATION)
        sm.transition_to(GamePhase.SHOPPING)
        sm.transition_to(GamePhase.EXPLORATION)
        assert sm.current_phase == GamePhase.EXPLORATION

    def test_transition_dialogue_to_exploration(self):
        sm = GameStateMachine()
        sm.transition_to(GamePhase.EXPLORATION)
        sm.transition_to(GamePhase.DIALOGUE)
        sm.transition_to(GamePhase.EXPLORATION)
        assert sm.current_phase == GamePhase.EXPLORATION

    def test_invalid_transition_lobby_to_combat_raises(self):
        """Can't go directly from lobby to combat."""
        sm = GameStateMachine()
        with pytest.raises(InvalidTransitionError):
            sm.transition_to(GamePhase.COMBAT)

    def test_invalid_transition_combat_to_rest_raises(self):
        """Can't rest during combat."""
        sm = GameStateMachine()
        sm.transition_to(GamePhase.EXPLORATION)
        sm.transition_to(GamePhase.COMBAT)
        with pytest.raises(InvalidTransitionError):
            sm.transition_to(GamePhase.REST)

    def test_invalid_transition_combat_to_shopping_raises(self):
        """Can't shop during combat."""
        sm = GameStateMachine()
        sm.transition_to(GamePhase.EXPLORATION)
        sm.transition_to(GamePhase.COMBAT)
        with pytest.raises(InvalidTransitionError):
            sm.transition_to(GamePhase.SHOPPING)

    def test_combat_can_go_to_dialogue(self):
        """Can negotiate during combat (parley)."""
        sm = GameStateMachine()
        sm.transition_to(GamePhase.EXPLORATION)
        sm.transition_to(GamePhase.COMBAT)
        sm.transition_to(GamePhase.DIALOGUE)
        assert sm.current_phase == GamePhase.DIALOGUE

    def test_dialogue_can_go_to_combat(self):
        """Dialogue can turn into combat."""
        sm = GameStateMachine()
        sm.transition_to(GamePhase.EXPLORATION)
        sm.transition_to(GamePhase.DIALOGUE)
        sm.transition_to(GamePhase.COMBAT)
        assert sm.current_phase == GamePhase.COMBAT


class TestTransitionHistory:
    """Test that state machine records transition history."""

    def test_history_starts_with_lobby(self):
        sm = GameStateMachine()
        assert sm.history == [GamePhase.LOBBY]

    def test_history_records_transitions(self):
        sm = GameStateMachine()
        sm.transition_to(GamePhase.EXPLORATION)
        sm.transition_to(GamePhase.COMBAT)
        assert sm.history == [GamePhase.LOBBY, GamePhase.EXPLORATION, GamePhase.COMBAT]

    def test_previous_phase(self):
        sm = GameStateMachine()
        sm.transition_to(GamePhase.EXPLORATION)
        sm.transition_to(GamePhase.COMBAT)
        assert sm.previous_phase == GamePhase.EXPLORATION

    def test_previous_phase_when_at_start(self):
        sm = GameStateMachine()
        assert sm.previous_phase is None


class TestTransitionCallbacks:
    """Test that callbacks fire on transitions."""

    def test_on_enter_callback(self):
        sm = GameStateMachine()
        entered = []
        sm.on_enter(GamePhase.EXPLORATION, lambda: entered.append("exploration"))
        sm.transition_to(GamePhase.EXPLORATION)
        assert entered == ["exploration"]

    def test_on_exit_callback(self):
        sm = GameStateMachine()
        exited = []
        sm.on_exit(GamePhase.LOBBY, lambda: exited.append("lobby"))
        sm.transition_to(GamePhase.EXPLORATION)
        assert exited == ["lobby"]

    def test_callbacks_not_fired_on_invalid_transition(self):
        sm = GameStateMachine()
        entered = []
        sm.on_enter(GamePhase.COMBAT, lambda: entered.append("combat"))
        with pytest.raises(InvalidTransitionError):
            sm.transition_to(GamePhase.COMBAT)
        assert entered == []


class TestCanTransition:
    """Test checking if a transition is valid without performing it."""

    def test_can_transition_from_lobby_to_exploration(self):
        sm = GameStateMachine()
        assert sm.can_transition_to(GamePhase.EXPLORATION) is True

    def test_cannot_transition_from_lobby_to_combat(self):
        sm = GameStateMachine()
        assert sm.can_transition_to(GamePhase.COMBAT) is False

    def test_can_transition_does_not_change_state(self):
        sm = GameStateMachine()
        sm.can_transition_to(GamePhase.EXPLORATION)
        assert sm.current_phase == GamePhase.LOBBY

    def test_available_transitions_from_lobby(self):
        sm = GameStateMachine()
        available = sm.available_transitions()
        assert GamePhase.EXPLORATION in available
        assert GamePhase.COMBAT not in available

    def test_available_transitions_from_exploration(self):
        sm = GameStateMachine()
        sm.transition_to(GamePhase.EXPLORATION)
        available = sm.available_transitions()
        assert GamePhase.COMBAT in available
        assert GamePhase.REST in available
        assert GamePhase.SHOPPING in available
        assert GamePhase.DIALOGUE in available
