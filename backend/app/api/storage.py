"""Volatile in-memory stores (runtime-only) and utility functions."""
import random
import string
import uuid


# Volatile runtime stores (NOT persisted to DB)
tokens: dict[str, str] = {}  # token -> user_id
vision_analyses: dict[str, dict] = {}
room_codes: dict[str, str] = {}  # room_code -> session_id
session_players: dict[str, list[dict]] = {}  # session_id -> [player_info]


def reset() -> None:
    """Reset all volatile stores (for testing)."""
    tokens.clear()
    vision_analyses.clear()
    room_codes.clear()
    session_players.clear()


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())


def generate_room_code(length: int = 4) -> str:
    """Generate a unique uppercase room code."""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase, k=length))
        if code not in room_codes:
            return code
