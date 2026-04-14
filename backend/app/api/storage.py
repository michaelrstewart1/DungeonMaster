"""In-memory storage for API endpoints (will be replaced by database later)."""
import uuid
import random
import string
from datetime import datetime, timezone
from typing import Any

# In-memory stores
campaigns: dict[str, dict[str, Any]] = {}
characters: dict[str, dict[str, Any]] = {}
game_sessions: dict[str, dict[str, Any]] = {}
maps: dict[str, dict[str, Any]] = {}
users: dict[str, dict[str, Any]] = {}
tokens: dict[str, str] = {}  # token -> user_id
vision_analyses: dict[str, dict[str, Any]] = {}
session_summaries: dict[str, str] = {}  # campaign_id -> last session summary text
story_bibles: dict[str, str] = {}  # campaign_id -> secret story bible

# Multiplayer
room_codes: dict[str, str] = {}  # room_code -> session_id
session_players: dict[str, list[dict[str, Any]]] = {}  # session_id -> [player_info]


def reset() -> None:
    """Reset all stores (for testing)."""
    campaigns.clear()
    characters.clear()
    game_sessions.clear()
    maps.clear()
    users.clear()
    tokens.clear()
    vision_analyses.clear()
    session_summaries.clear()
    story_bibles.clear()
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
