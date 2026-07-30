"""Runtime stores with DB-backed persistence.

The dicts below are the live source of truth during a session (fast, no
awaits in hot paths). Each mutation site calls ``flush(<store>)`` which
schedules an async snapshot of the store into the ``runtime_stores`` table,
so room codes, players, trades, auth tokens, and vision analyses survive
backend restarts. ``load_from_db()`` restores them at startup.
"""
import asyncio
import logging
import random
import string
import uuid

logger = logging.getLogger(__name__)

# Runtime stores (persisted via flush()/load_from_db())
tokens: dict[str, str] = {}  # token -> user_id
vision_analyses: dict[str, dict] = {}
room_codes: dict[str, str] = {}  # room_code -> session_id
session_players: dict[str, list[dict]] = {}  # session_id -> [player_info]
trades: dict[str, dict] = {}  # trade_id -> trade dict

_STORES: dict[str, dict] = {
    "tokens": tokens,
    "vision_analyses": vision_analyses,
    "room_codes": room_codes,
    "session_players": session_players,
    "trades": trades,
}

# Async session factory (set during app lifespan). When None (unit tests,
# scripts), flush() is a no-op and stores are memory-only.
_db_factory = None


def configure(db_factory) -> None:
    """Attach an async session factory used to persist stores."""
    global _db_factory
    _db_factory = db_factory


async def load_from_db() -> None:
    """Restore all runtime stores from the runtime_stores table."""
    if _db_factory is None:
        return
    from sqlalchemy import select

    from app.models.database import RuntimeStoreDB

    async with _db_factory() as db:
        result = await db.execute(select(RuntimeStoreDB))
        for row in result.scalars():
            store = _STORES.get(row.name)
            if store is not None and isinstance(row.data, dict):
                store.clear()
                store.update(row.data)
    logger.info(
        "Runtime stores restored: %s",
        {name: len(store) for name, store in _STORES.items()},
    )


async def persist(*names: str) -> None:
    """Write the named stores (or all) to the runtime_stores table."""
    if _db_factory is None:
        return
    from app.models.database import RuntimeStoreDB

    targets = names or tuple(_STORES)
    async with _db_factory() as db:
        for name in targets:
            store = _STORES.get(name)
            if store is None:
                continue
            row = await db.get(RuntimeStoreDB, name)
            if row is None:
                db.add(RuntimeStoreDB(name=name, data=dict(store)))
            else:
                row.data = dict(store)
        await db.commit()


def flush(*names: str) -> None:
    """Schedule persistence of the named stores. Safe to call from sync code."""
    if _db_factory is None:
        return
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return  # no loop (unit tests) -- skip persistence

    async def _do() -> None:
        try:
            await persist(*names)
        except Exception:  # pragma: no cover - persistence must never break play
            logger.exception("Failed to persist runtime stores %s", names)

    loop.create_task(_do())


def reset() -> None:
    """Reset all runtime stores (for testing)."""
    global _db_factory
    _db_factory = None
    for store in _STORES.values():
        store.clear()


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())


def generate_room_code(length: int = 4) -> str:
    """Generate a unique uppercase room code."""
    while True:
        code = "".join(random.choices(string.ascii_uppercase, k=length))
        if code not in room_codes:
            return code
