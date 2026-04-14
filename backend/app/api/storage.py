"""In-memory storage for API endpoints with JSON file persistence."""
import json
import logging
import os
import uuid
import random
import string
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

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

# Persistence path (relative to backend dir or absolute via env)
_SAVE_DIR = Path(os.environ.get("DM_SAVE_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")))
_SAVE_FILE = _SAVE_DIR / "save.json"

# Stores to persist (volatile runtime data like tokens/room_codes excluded)
_PERSISTENT_STORES = {
    "campaigns": campaigns,
    "characters": characters,
    "game_sessions": game_sessions,
    "maps": maps,
    "session_summaries": session_summaries,
    "story_bibles": story_bibles,
}


def save_to_disk() -> None:
    """Persist all important stores to disk as JSON."""
    try:
        _SAVE_DIR.mkdir(parents=True, exist_ok=True)
        snapshot = {name: dict(store) for name, store in _PERSISTENT_STORES.items()}
        tmp = _SAVE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(snapshot, default=str, indent=2), encoding="utf-8")
        tmp.replace(_SAVE_FILE)
        logger.debug("Auto-saved game state (%d campaigns, %d characters, %d sessions)",
                      len(campaigns), len(characters), len(game_sessions))
    except Exception as exc:
        logger.warning("Auto-save failed: %s", exc)


def load_from_disk() -> bool:
    """Load stores from disk. Returns True if data was loaded."""
    if not _SAVE_FILE.exists():
        logger.info("No save file found at %s — starting fresh", _SAVE_FILE)
        return False
    try:
        snapshot = json.loads(_SAVE_FILE.read_text(encoding="utf-8"))
        for name, store in _PERSISTENT_STORES.items():
            store.clear()
            store.update(snapshot.get(name, {}))
        logger.info("Loaded save: %d campaigns, %d characters, %d sessions",
                     len(campaigns), len(characters), len(game_sessions))
        return True
    except Exception as exc:
        logger.warning("Failed to load save file: %s", exc)
        return False


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
