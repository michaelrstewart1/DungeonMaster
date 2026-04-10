"""In-memory storage for API endpoints (will be replaced by database later)."""
import uuid
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


def reset() -> None:
    """Reset all stores (for testing)."""
    campaigns.clear()
    characters.clear()
    game_sessions.clear()
    maps.clear()
    users.clear()
    tokens.clear()
    vision_analyses.clear()


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())
