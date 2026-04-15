"""In-memory storage for API endpoints with PostgreSQL + JSON file persistence."""
import asyncio
import json
import logging
import os
import uuid
import random
import string
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import delete

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

# Async lock to prevent concurrent DB writes from racing
_save_lock = asyncio.Lock()


# ---------------------------------------------------------------------------
# PostgreSQL persistence (primary)
# ---------------------------------------------------------------------------

async def save_to_db() -> None:
    """Persist all important stores to PostgreSQL.

    Takes a snapshot of the in-memory dicts *before* any async I/O to avoid
    iterating live dicts across awaits.  Uses a full-replace strategy per
    store inside a single transaction so deleted entities don't resurrect.
    """
    try:
        from app.db import async_session
    except Exception:
        logger.debug("DB engine not available — skipping DB save")
        return

    # Snapshot everything synchronously first
    snapshot: dict[str, dict[str, Any]] = {}
    for store_name, store in _PERSISTENT_STORES.items():
        snapshot[store_name] = dict(store)

    async with _save_lock:
        try:
            from app.models.database import GameDataDB
            async with async_session() as session:
                async with session.begin():
                    for store_name, entities in snapshot.items():
                        # Delete all rows for this store
                        await session.execute(
                            delete(GameDataDB).where(
                                GameDataDB.store_name == store_name
                            )
                        )
                        # Bulk insert current entities
                        for eid, data in entities.items():
                            # Normalize data: ensure JSON-serializable
                            normalized = json.loads(json.dumps(data, default=str))
                            session.add(GameDataDB(
                                store_name=store_name,
                                entity_id=eid,
                                data=normalized,
                            ))
            logger.debug(
                "DB-saved game state (%d campaigns, %d characters, %d sessions)",
                len(snapshot.get("campaigns", {})),
                len(snapshot.get("characters", {})),
                len(snapshot.get("game_sessions", {})),
            )
        except Exception as exc:
            logger.warning("DB save failed: %s", exc)
            # Fall back to disk save
            save_to_disk()


async def load_from_db() -> bool:
    """Load stores from PostgreSQL. Returns True if data was loaded."""
    try:
        from app.db import async_session
        from app.models.database import GameDataDB
    except Exception:
        logger.debug("DB engine not available — skipping DB load")
        return False

    try:
        from sqlalchemy import select
        async with async_session() as session:
            result = await session.execute(select(GameDataDB))
            rows = result.scalars().all()

        if not rows:
            logger.info("DB game_data table is empty")
            return False

        # Group rows by store
        loaded: dict[str, dict[str, Any]] = {}
        for row in rows:
            loaded.setdefault(row.store_name, {})[row.entity_id] = row.data

        for name, store in _PERSISTENT_STORES.items():
            store.clear()
            store.update(loaded.get(name, {}))

        logger.info(
            "Loaded from DB: %d campaigns, %d characters, %d sessions",
            len(campaigns), len(characters), len(game_sessions),
        )
        return True
    except Exception as exc:
        logger.warning("Failed to load from DB: %s", exc)
        return False


async def import_json_to_db() -> bool:
    """One-time import: if DB is empty but save.json exists, seed DB from it."""
    if not _SAVE_FILE.exists():
        return False

    try:
        from app.db import async_session
        from app.models.database import GameDataDB
    except Exception:
        return False

    # Check if DB already has data
    try:
        from sqlalchemy import select, func
        async with async_session() as session:
            result = await session.execute(
                select(func.count()).select_from(GameDataDB)
            )
            count = result.scalar()
            if count and count > 0:
                return False
    except Exception:
        return False

    # Load JSON file into memory, then save to DB
    logger.info("Importing save.json → PostgreSQL (one-time migration)")
    if load_from_disk():
        await save_to_db()
        logger.info("Migration complete — JSON data imported to DB")
        return True
    return False


# ---------------------------------------------------------------------------
# JSON file persistence (fallback)
# ---------------------------------------------------------------------------

def save_to_disk() -> None:
    """Persist all important stores to disk as JSON (fallback)."""
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


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

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
