"""In-memory storage for API endpoints (will be replaced by database later)."""
import uuid
from datetime import datetime, timezone
from typing import Any

# In-memory stores
campaigns: dict[str, dict[str, Any]] = {}
characters: dict[str, dict[str, Any]] = {}
game_sessions: dict[str, dict[str, Any]] = {}


def reset() -> None:
    """Reset all stores (for testing)."""
    campaigns.clear()
    characters.clear()
    game_sessions.clear()


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())
