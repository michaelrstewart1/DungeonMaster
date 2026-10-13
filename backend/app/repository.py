"""
Repository layer — async CRUD operations backed by SQLAlchemy.

Every function accepts an AsyncSession and returns plain dicts so route code
stays unchanged.  The repository is the single boundary between the API
layer and the database.
"""
from typing import Any, Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import (
    CampaignDB,
    CharacterDB,
    GameSessionDB,
    MapDB,
    UserDB,
)


# ---------------------------------------------------------------------------
# Campaigns
# ---------------------------------------------------------------------------

async def get_campaign(db: AsyncSession, campaign_id: str) -> Optional[dict]:
    row = await db.get(CampaignDB, campaign_id)
    return row.to_dict() if row else None


async def list_campaigns(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(CampaignDB))
    return [r.to_dict() for r in result.scalars().all()]


async def save_campaign(db: AsyncSession, data: dict) -> dict:
    """Insert or update a campaign.  Returns the saved dict."""
    existing = await db.get(CampaignDB, data["id"])
    if existing:
        fields = {c.name for c in CampaignDB.__table__.columns}
        extra = dict(existing.extra_data or {})
        for key, val in data.items():
            if key != "id" and key in fields:
                setattr(existing, key, val)
            elif key not in CampaignDB._TYPED_FIELDS:
                extra[key] = val
        existing.extra_data = extra
        # Force JSON columns to be marked dirty
        existing.character_ids = list(existing.character_ids or [])
        existing.world_state = dict(existing.world_state or {})
        existing.dm_settings = dict(existing.dm_settings or {})
    else:
        existing = CampaignDB.from_dict(data)
        db.add(existing)
    await db.flush()
    return existing.to_dict()


async def delete_campaign(db: AsyncSession, campaign_id: str) -> bool:
    row = await db.get(CampaignDB, campaign_id)
    if not row:
        return False
    await db.delete(row)
    await db.flush()
    return True


async def campaign_exists(db: AsyncSession, campaign_id: str) -> bool:
    row = await db.get(CampaignDB, campaign_id)
    return row is not None


async def get_campaign_session_summary(db: AsyncSession, campaign_id: str) -> Optional[str]:
    row = await db.get(CampaignDB, campaign_id)
    return row.session_summary if row else None


async def set_campaign_session_summary(db: AsyncSession, campaign_id: str, summary: str) -> None:
    row = await db.get(CampaignDB, campaign_id)
    if row:
        row.session_summary = summary
        await db.flush()


async def get_campaign_story_bible(db: AsyncSession, campaign_id: str) -> Optional[str]:
    row = await db.get(CampaignDB, campaign_id)
    return row.story_bible if row else None


async def set_campaign_story_bible(db: AsyncSession, campaign_id: str, bible: str) -> None:
    row = await db.get(CampaignDB, campaign_id)
    if row:
        row.story_bible = bible
        await db.flush()


# ---------------------------------------------------------------------------
# Campaign Memory
# ---------------------------------------------------------------------------

async def get_campaign_memory(db: AsyncSession, campaign_id: str) -> dict:
    """Get structured campaign memory (events/quests/npcs/locations)."""
    from app.models.database import CampaignMemoryDB

    row = await db.get(CampaignMemoryDB, campaign_id)
    if row:
        return row.to_dict()
    return {
        "campaign_id": campaign_id,
        "events": [],
        "quests": [],
        "npcs": [],
        "locations": [],
        "updated_at": None,
    }


async def save_campaign_memory(db: AsyncSession, memory: dict) -> dict:
    """Insert or update campaign memory. Returns the saved dict."""
    from datetime import datetime, timezone

    from app.models.database import CampaignMemoryDB

    row = await db.get(CampaignMemoryDB, memory["campaign_id"])
    stamp = datetime.now(timezone.utc).isoformat()
    if row:
        row.events = list(memory.get("events", []))
        row.quests = list(memory.get("quests", []))
        row.npcs = list(memory.get("npcs", []))
        row.locations = list(memory.get("locations", []))
        row.updated_at = stamp
    else:
        row = CampaignMemoryDB(
            campaign_id=memory["campaign_id"],
            events=list(memory.get("events", [])),
            quests=list(memory.get("quests", [])),
            npcs=list(memory.get("npcs", [])),
            locations=list(memory.get("locations", [])),
            updated_at=stamp,
        )
        db.add(row)
    await db.flush()
    return row.to_dict()


# ---------------------------------------------------------------------------
# Characters
# ---------------------------------------------------------------------------

async def get_character(db: AsyncSession, character_id: str) -> Optional[dict]:
    row = await db.get(CharacterDB, character_id)
    return row.to_dict() if row else None


async def list_characters(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(CharacterDB))
    return [r.to_dict() for r in result.scalars().all()]


async def save_character(db: AsyncSession, data: dict) -> dict:
    existing = await db.get(CharacterDB, data["id"])
    if existing:
        fields = {c.name for c in CharacterDB.__table__.columns}
        extra = dict(existing.extra_data or {})
        for key, val in data.items():
            if key != "id" and key in fields:
                setattr(existing, key, val)
            elif key not in CharacterDB._TYPED_FIELDS:
                extra[key] = val
        existing.extra_data = extra
    else:
        existing = CharacterDB.from_dict(data)
        db.add(existing)
    await db.flush()
    return existing.to_dict()


async def update_character(db: AsyncSession, character_id: str, updates: dict) -> Optional[dict]:
    """Apply partial updates to a character.  Returns updated dict or None."""
    row = await db.get(CharacterDB, character_id)
    if not row:
        return None
    fields = {c.name for c in CharacterDB.__table__.columns}
    for key, val in updates.items():
        if key in fields:
            setattr(row, key, val)
    await db.flush()
    return row.to_dict()


async def delete_character(db: AsyncSession, character_id: str) -> bool:
    row = await db.get(CharacterDB, character_id)
    if not row:
        return False
    await db.delete(row)
    await db.flush()
    return True


async def character_exists(db: AsyncSession, character_id: str) -> bool:
    row = await db.get(CharacterDB, character_id)
    return row is not None


# ---------------------------------------------------------------------------
# Game Sessions
# ---------------------------------------------------------------------------

class SaveResult(dict):
    """Dict returned by ``save_game_session``.

    ``applied`` is False when the caller handed in a snapshot older than the
    row now stored — the current row is returned unchanged.
    """

    applied: bool

    def __init__(self, data: dict, applied: bool):
        super().__init__(data)
        self.applied = applied


def session_version(session: Optional[dict]) -> int:
    """Monotonic revision stored on a session dict. Missing means 0."""
    if not session:
        return 0
    raw = session.get("state_version")
    if isinstance(raw, bool) or raw is None:
        return 0
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


async def get_game_session(db: AsyncSession, session_id: str) -> Optional[dict]:
    row = await db.get(GameSessionDB, session_id)
    if row is None:
        return None
    # Reload so a second read in this request cannot return an identity-map
    # copy from before another transaction committed.
    await db.refresh(row)
    return row.to_dict()


async def list_game_sessions(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(GameSessionDB))
    return [r.to_dict() for r in result.scalars().all()]


async def save_game_session(db: AsyncSession, data: dict) -> SaveResult:
    """Insert or update a session.

    A snapshot that carries a ``state_version`` other than the row's current
    revision is refused. That is the write that used to put one phone back
    on an earlier combat while everyone still connected kept the live scene.
    Callers that build a brand-new dict (no version) still overwrite — tests
    and session creation do that. Anything loaded via ``get_game_session``
    has a version and must match.
    """
    existing = await db.get(GameSessionDB, data["id"])
    if existing:
        await db.refresh(existing)
        current = session_version(existing.to_dict())
        raw_incoming = data.get("state_version")
        incoming = session_version(data) if raw_incoming is not None else None
        if incoming is not None and incoming != current:
            return SaveResult(existing.to_dict(), applied=False)

        fields = {c.name for c in GameSessionDB.__table__.columns}
        extra = dict(existing.extra_data or {})
        for key, val in data.items():
            if key != "id" and key in fields:
                setattr(existing, key, val)
            elif key not in GameSessionDB._TYPED_FIELDS and key != "state_version":
                extra[key] = val
        for key in GameSessionDB._AUTHORITATIVE:
            extra.pop(key, None)
        extra["state_version"] = current + 1
        existing.extra_data = extra
        # Mark JSON columns dirty. Reassign copies so in-place mutations of
        # the caller's dict cannot alias the ORM object's previous value.
        existing.narrative_history = list(existing.narrative_history or [])
        existing.active_effects = list(existing.active_effects or [])
        existing.environment = dict(existing.environment or {})
        existing.npcs = list(existing.npcs or [])
        if existing.combat_state is not None:
            existing.combat_state = dict(existing.combat_state)
        data["state_version"] = current + 1
    else:
        payload = dict(data)
        payload["state_version"] = session_version(data) + 1
        existing = GameSessionDB.from_dict(payload)
        db.add(existing)
        data["state_version"] = payload["state_version"]
    await db.flush()
    return SaveResult(existing.to_dict(), applied=True)


async def delete_game_session(db: AsyncSession, session_id: str) -> bool:
    row = await db.get(GameSessionDB, session_id)
    if not row:
        return False
    await db.delete(row)
    await db.flush()
    return True


async def game_session_exists(db: AsyncSession, session_id: str) -> bool:
    row = await db.get(GameSessionDB, session_id)
    return row is not None


# ---------------------------------------------------------------------------
# Maps
# ---------------------------------------------------------------------------

async def get_map(db: AsyncSession, session_id: str) -> Optional[dict]:
    row = await db.get(MapDB, session_id)
    return row.to_dict() if row else None


async def save_map(db: AsyncSession, session_id: str, data: dict) -> dict:
    existing = await db.get(MapDB, session_id)
    if existing:
        existing.width = data["width"]
        existing.height = data["height"]
        existing.terrain_grid = data.get("terrain_grid", [])
        existing.token_positions = [
            t if isinstance(t, dict) else {"entity_id": t.entity_id, "x": t.x, "y": t.y}
            for t in data.get("token_positions", [])
        ]
        existing.fog_of_war = data.get("fog_of_war", [])
    else:
        existing = MapDB.from_dict(session_id, data)
        db.add(existing)
    await db.flush()
    return existing.to_dict()


async def map_exists(db: AsyncSession, session_id: str) -> bool:
    row = await db.get(MapDB, session_id)
    return row is not None


async def delete_map(db: AsyncSession, session_id: str) -> bool:
    row = await db.get(MapDB, session_id)
    if not row:
        return False
    await db.delete(row)
    await db.flush()
    return True


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

async def get_user(db: AsyncSession, user_id: str) -> Optional[dict]:
    row = await db.get(UserDB, user_id)
    if not row:
        return None
    return {"id": row.id, "username": row.username, "password_hash": row.password_hash}


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[dict]:
    result = await db.execute(
        select(UserDB).where(UserDB.username == username)
    )
    row = result.scalar_one_or_none()
    if not row:
        return None
    return {"id": row.id, "username": row.username, "password_hash": row.password_hash}


async def list_users(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(UserDB))
    return [{"id": r.id, "username": r.username, "password_hash": r.password_hash}
            for r in result.scalars().all()]


async def save_user(db: AsyncSession, data: dict) -> dict:
    existing = await db.get(UserDB, data["id"])
    if existing:
        existing.username = data["username"]
        existing.password_hash = data["password_hash"]
    else:
        db.add(UserDB(
            id=data["id"],
            username=data["username"],
            password_hash=data["password_hash"],
        ))
    await db.flush()
    return data
