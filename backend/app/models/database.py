"""
SQLAlchemy ORM models for the Dungeon Master application.
Proper typed columns for all persistent game state.
"""
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from uuid import uuid4

from sqlalchemy import (
    String,
    Integer,
    Float,
    DateTime,
    Text,
    JSON,
    Boolean,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


# ---------------------------------------------------------------------------
# Campaign
# ---------------------------------------------------------------------------

class CampaignDB(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    character_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    world_state: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    dm_settings: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, default=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, default=lambda: datetime.now(timezone.utc).isoformat())

    # Formerly separate stores keyed by campaign_id
    session_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    story_bible: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extra_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    _TYPED_FIELDS = frozenset({
        "id", "name", "description", "character_ids", "world_state", "dm_settings",
        "created_at", "updated_at", "session_summary", "story_bible", "extra_data",
    })

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "character_ids": self.character_ids or [],
            "world_state": self.world_state or {},
            "dm_settings": self.dm_settings or {},
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if self.extra_data:
            d.update(self.extra_data)
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "CampaignDB":
        extra = {k: v for k, v in data.items() if k not in cls._TYPED_FIELDS}
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            character_ids=data.get("character_ids", []),
            world_state=data.get("world_state", {}),
            dm_settings=data.get("dm_settings", {}),
            created_at=str(data.get("created_at", "")) or None,
            updated_at=str(data.get("updated_at", "")) or None,
            extra_data=extra,
        )


# ---------------------------------------------------------------------------
# Character
# ---------------------------------------------------------------------------

class CharacterDB(Base):
    __tablename__ = "characters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    race: Mapped[str] = mapped_column(String(50), nullable=False)
    class_name: Mapped[str] = mapped_column(String(50), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Ability scores
    strength: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    dexterity: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    constitution: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    intelligence: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    wisdom: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    charisma: Mapped[int] = mapped_column(Integer, nullable=False, default=10)

    # Core stats
    hp: Mapped[int] = mapped_column(Integer, nullable=False, default=8)
    max_hp: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ac: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    speed: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    experience_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Optional string fields
    subrace: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    subclass: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    background: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    alignment: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    hit_dice: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    portrait_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Personality
    personality_traits: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ideals: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bonds: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    flaws: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    backstory: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # JSON array columns (lists of strings)
    skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    saving_throws: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    languages: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    tool_proficiencies: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    armor_proficiencies: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    weapon_proficiencies: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    features: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    spells_known: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    cantrips_known: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    conditions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    inventory: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    equipment: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    extra_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    _TYPED_FIELDS = frozenset({
        "id", "name", "race", "class_name", "level",
        "strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma",
        "hp", "max_hp", "ac", "speed", "experience_points",
        "subrace", "subclass", "background", "alignment", "hit_dice", "portrait_url",
        "personality_traits", "ideals", "bonds", "flaws", "backstory",
        "skills", "saving_throws", "languages", "tool_proficiencies",
        "armor_proficiencies", "weapon_proficiencies", "features",
        "spells_known", "cantrips_known", "conditions", "inventory", "equipment",
        "extra_data", "created_at",
    })

    def to_dict(self) -> dict:
        d: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "race": self.race,
            "class_name": self.class_name,
            "level": self.level,
            "strength": self.strength,
            "dexterity": self.dexterity,
            "constitution": self.constitution,
            "intelligence": self.intelligence,
            "wisdom": self.wisdom,
            "charisma": self.charisma,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "ac": self.ac,
            "speed": self.speed,
            "experience_points": self.experience_points,
            "subrace": self.subrace,
            "subclass": self.subclass,
            "background": self.background,
            "alignment": self.alignment,
            "hit_dice": self.hit_dice,
            "portrait_url": self.portrait_url,
            "personality_traits": self.personality_traits,
            "ideals": self.ideals,
            "bonds": self.bonds,
            "flaws": self.flaws,
            "backstory": self.backstory,
            "skills": self.skills or [],
            "saving_throws": self.saving_throws or [],
            "languages": self.languages or [],
            "tool_proficiencies": self.tool_proficiencies or [],
            "armor_proficiencies": self.armor_proficiencies or [],
            "weapon_proficiencies": self.weapon_proficiencies or [],
            "features": self.features or [],
            "spells_known": self.spells_known or [],
            "cantrips_known": self.cantrips_known or [],
            "conditions": self.conditions or [],
            "inventory": self.inventory or [],
            "equipment": self.equipment or [],
        }
        if self.created_at is not None:
            d["created_at"] = self.created_at
        # Merge extra_data back into the dict
        if self.extra_data:
            d.update(self.extra_data)
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "CharacterDB":
        fields = {c.name for c in cls.__table__.columns}
        kwargs = {k: v for k, v in data.items() if k in fields}
        extra = {k: v for k, v in data.items() if k not in cls._TYPED_FIELDS}
        kwargs["extra_data"] = extra
        return cls(**kwargs)


# ---------------------------------------------------------------------------
# Game Session
# ---------------------------------------------------------------------------

class GameSessionDB(Base):
    __tablename__ = "game_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(36), nullable=False)
    current_phase: Mapped[str] = mapped_column(String(50), nullable=False, default="exploration")
    current_scene: Mapped[str] = mapped_column(Text, nullable=False, default="")
    turn_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, default=lambda: datetime.now(timezone.utc).isoformat())

    # Complex nested data as JSON
    narrative_history: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    combat_state: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    active_effects: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    environment: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    npcs: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    extra_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Known typed column names (used to separate typed vs extra data)
    _TYPED_FIELDS = frozenset({
        "id", "campaign_id", "current_phase", "current_scene", "turn_count",
        "created_at", "narrative_history", "combat_state", "active_effects",
        "environment", "npcs", "extra_data",
    })

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "campaign_id": self.campaign_id,
            "current_phase": self.current_phase,
            "current_scene": self.current_scene,
            "turn_count": self.turn_count,
            "created_at": self.created_at,
            "narrative_history": self.narrative_history or [],
            "combat_state": self.combat_state,
            "active_effects": self.active_effects or [],
            "environment": self.environment or {},
            "npcs": self.npcs or [],
        }
        # Merge extra_data back into the dict
        if self.extra_data:
            d.update(self.extra_data)
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "GameSessionDB":
        fields = {c.name for c in cls.__table__.columns}
        kwargs = {k: v for k, v in data.items() if k in fields}
        # Capture everything else in extra_data
        extra = {k: v for k, v in data.items() if k not in cls._TYPED_FIELDS}
        kwargs["extra_data"] = extra
        return cls(**kwargs)


# ---------------------------------------------------------------------------
# Map (keyed by session_id)
# ---------------------------------------------------------------------------

class MapDB(Base):
    __tablename__ = "maps"

    session_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    terrain_grid: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    token_positions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    fog_of_war: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    def to_dict(self) -> dict:
        return {
            "id": self.session_id,
            "width": self.width,
            "height": self.height,
            "terrain_grid": self.terrain_grid or [],
            "token_positions": self.token_positions or [],
            "fog_of_war": self.fog_of_war or [],
        }

    @classmethod
    def from_dict(cls, session_id: str, data: dict) -> "MapDB":
        return cls(
            session_id=session_id,
            width=data["width"],
            height=data["height"],
            terrain_grid=data.get("terrain_grid", []),
            token_positions=[
                t if isinstance(t, dict) else {"entity_id": t.entity_id, "x": t.x, "y": t.y}
                for t in data.get("token_positions", [])
            ],
            fog_of_war=data.get("fog_of_war", []),
        )


# ---------------------------------------------------------------------------
# User (auth)
# ---------------------------------------------------------------------------

class UserDB(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
