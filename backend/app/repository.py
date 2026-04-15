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

async def get_game_session(db: AsyncSession, session_id: str) -> Optional[dict]:
    row = await db.get(GameSessionDB, session_id)
    return row.to_dict() if row else None


async def list_game_sessions(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(GameSessionDB))
    return [r.to_dict() for r in result.scalars().all()]


async def save_game_session(db: AsyncSession, data: dict) -> dict:
    existing = await db.get(GameSessionDB, data["id"])
    if existing:
        fields = {c.name for c in GameSessionDB.__table__.columns}
        extra = dict(existing.extra_data or {})
        for key, val in data.items():
            if key != "id" and key in fields:
                setattr(existing, key, val)
            elif key not in GameSessionDB._TYPED_FIELDS:
                extra[key] = val
        existing.extra_data = extra
        # Mark JSON columns dirty
        existing.narrative_history = list(existing.narrative_history or [])
        existing.active_effects = list(existing.active_effects or [])
        existing.environment = dict(existing.environment or {})
        existing.npcs = list(existing.npcs or [])
    else:
        existing = GameSessionDB.from_dict(data)
        db.add(existing)
    await db.flush()
    return existing.to_dict()


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
