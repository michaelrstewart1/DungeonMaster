"""Avatar expression mapping — maps game context to DM facial expressions."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal
import re


class Expression(str, Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    ANGRY = "angry"
    SAD = "sad"
    SURPRISED = "surprised"
    THINKING = "thinking"
    MENACING = "menacing"
    EXCITED = "excited"


class GazeDirection(str, Enum):
    CENTER = "center"
    LEFT = "left"
    RIGHT = "right"
    UP = "up"
    DOWN = "down"


@dataclass
class AvatarState:
    expression: Expression = Expression.NEUTRAL
    is_speaking: bool = False
    mouth_amplitude: float = 0.0
    gaze: GazeDirection = GazeDirection.CENTER

    def to_dict(self) -> dict:
        return {
            "expression": self.expression.value,
            "is_speaking": self.is_speaking,
            "mouth_amplitude": self.mouth_amplitude,
            "gaze": self.gaze.value,
        }


# Keywords that signal specific emotions in narration text
_EXCITED_KEYWORDS = re.compile(
    r"\b(amazing|incredible|legendary|epic|triumphant|glorious|magnificent|wonderful|fantastic|brilliant)\b",
    re.IGNORECASE,
)
_DANGER_KEYWORDS = re.compile(
    r"\b(dragon|roar|flame|fire|death|destroy|crush|terror|horror|doom|darkness|shadow|demon|undead)\b",
    re.IGNORECASE,
)
_SAD_KEYWORDS = re.compile(
    r"\b(death|mourn|loss|grief|tears|weep|fallen|tragic|sorrow|farewell)\b",
    re.IGNORECASE,
)
_SURPRISE_KEYWORDS = re.compile(
    r"\b(suddenly|unexpected|shock|gasp|ambush|trap|reveal|twist)\b",
    re.IGNORECASE,
)


class ExpressionMapper:
    """Maps game context and text to avatar expressions."""

    # Phase + narration_type → Expression
    _CONTEXT_MAP: dict[tuple[str, str], Expression] = {
        ("combat", "attack"): Expression.EXCITED,
        ("combat", "danger"): Expression.MENACING,
        ("combat", "player_success"): Expression.HAPPY,
        ("combat", "player_fail"): Expression.MENACING,
        ("combat", "description"): Expression.MENACING,
        ("exploration", "description"): Expression.NEUTRAL,
        ("exploration", "surprise"): Expression.SURPRISED,
        ("exploration", "discovery"): Expression.EXCITED,
        ("dialogue", "friendly_npc"): Expression.HAPPY,
        ("dialogue", "hostile_npc"): Expression.ANGRY,
        ("dialogue", "sad"): Expression.SAD,
        ("dialogue", "mysterious"): Expression.THINKING,
        ("rest", "description"): Expression.NEUTRAL,
        ("rest", "dream"): Expression.THINKING,
        ("shopping", "description"): Expression.HAPPY,
    }

    def from_game_context(self, phase: str, narration_type: str) -> Expression:
        """Map game phase + narration type to an expression."""
        return self._CONTEXT_MAP.get((phase, narration_type), Expression.NEUTRAL)

    def from_text_sentiment(self, text: str) -> Expression:
        """Derive expression from narration text keywords."""
        if _EXCITED_KEYWORDS.search(text):
            return Expression.EXCITED
        if _DANGER_KEYWORDS.search(text):
            return Expression.MENACING
        if _SAD_KEYWORDS.search(text):
            return Expression.SAD
        if _SURPRISE_KEYWORDS.search(text):
            return Expression.SURPRISED
        return Expression.NEUTRAL
