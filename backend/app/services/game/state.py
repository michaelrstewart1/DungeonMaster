"""Game state machine for tracking game phases and transitions."""

from enum import Enum
from typing import Callable


class GamePhase(str, Enum):
    LOBBY = "lobby"
    EXPLORATION = "exploration"
    COMBAT = "combat"
    REST = "rest"
    SHOPPING = "shopping"
    DIALOGUE = "dialogue"


class InvalidTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""

    def __init__(self, from_phase: GamePhase, to_phase: GamePhase):
        self.from_phase = from_phase
        self.to_phase = to_phase
        super().__init__(
            f"Invalid transition from {from_phase.value} to {to_phase.value}"
        )


# Valid transitions: from_phase -> set of allowed target phases
_TRANSITIONS: dict[GamePhase, set[GamePhase]] = {
    GamePhase.LOBBY: {GamePhase.EXPLORATION},
    GamePhase.EXPLORATION: {
        GamePhase.COMBAT,
        GamePhase.REST,
        GamePhase.SHOPPING,
        GamePhase.DIALOGUE,
    },
    GamePhase.COMBAT: {
        GamePhase.EXPLORATION,
        GamePhase.DIALOGUE,
    },
    GamePhase.REST: {GamePhase.EXPLORATION},
    GamePhase.SHOPPING: {GamePhase.EXPLORATION},
    GamePhase.DIALOGUE: {
        GamePhase.EXPLORATION,
        GamePhase.COMBAT,
    },
}


class GameStateMachine:
    """Manages game phase transitions with validation and callbacks."""

    def __init__(self, initial_phase: GamePhase = GamePhase.LOBBY):
        self._current = initial_phase
        self._history: list[GamePhase] = [initial_phase]
        self._on_enter: dict[GamePhase, list[Callable]] = {}
        self._on_exit: dict[GamePhase, list[Callable]] = {}

    @property
    def current_phase(self) -> GamePhase:
        return self._current

    @property
    def history(self) -> list[GamePhase]:
        return list(self._history)

    @property
    def previous_phase(self) -> GamePhase | None:
        if len(self._history) < 2:
            return None
        return self._history[-2]

    def can_transition_to(self, phase: GamePhase) -> bool:
        allowed = _TRANSITIONS.get(self._current, set())
        return phase in allowed

    def available_transitions(self) -> list[GamePhase]:
        return sorted(_TRANSITIONS.get(self._current, set()), key=lambda p: p.value)

    def transition_to(self, phase: GamePhase) -> None:
        if not self.can_transition_to(phase):
            raise InvalidTransitionError(self._current, phase)

        old_phase = self._current

        # Fire exit callbacks
        for cb in self._on_exit.get(old_phase, []):
            cb()

        self._current = phase
        self._history.append(phase)

        # Fire enter callbacks
        for cb in self._on_enter.get(phase, []):
            cb()

    def on_enter(self, phase: GamePhase, callback: Callable) -> None:
        self._on_enter.setdefault(phase, []).append(callback)

    def on_exit(self, phase: GamePhase, callback: Callable) -> None:
        self._on_exit.setdefault(phase, []).append(callback)
