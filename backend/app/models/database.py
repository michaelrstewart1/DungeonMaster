"""
SQLAlchemy ORM models for the Dungeon Master application.
Mirrors Pydantic schemas with database persistence.
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import uuid4

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""

    pass


class CampaignDB(Base):
    """Campaign model for storing campaign data."""

    __tablename__ = "campaign"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(1024), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.utcnow(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow(), nullable=False
    )

    # Relationships
    characters: Mapped[List["CharacterDB"]] = relationship(
        "CharacterDB", back_populates="campaign", cascade="all, delete-orphan"
    )
    game_sessions: Mapped[List["GameSessionDB"]] = relationship(
        "GameSessionDB", back_populates="campaign", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Campaign(id={self.id}, name={self.name})>"


class CharacterDB(Base):
    """Character model for storing character data."""

    __tablename__ = "character"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    campaign_id: Mapped[str] = mapped_column(String(36), ForeignKey("campaign.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    race: Mapped[str] = mapped_column(String(50), nullable=False)
    character_class: Mapped[str] = mapped_column(String(50), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    hp: Mapped[int] = mapped_column(Integer, nullable=False)
    max_hp: Mapped[int] = mapped_column(Integer, nullable=False)
    ac: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    abilities: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    skills: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    inventory: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    campaign: Mapped[CampaignDB] = relationship("CampaignDB", back_populates="characters")

    def __repr__(self) -> str:
        return f"<Character(id={self.id}, name={self.name}, class={self.character_class})>"


class GameSessionDB(Base):
    """Game session model for storing game session data."""

    __tablename__ = "game_session"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    campaign_id: Mapped[str] = mapped_column(String(36), ForeignKey("campaign.id"), nullable=False)
    phase: Mapped[str] = mapped_column(String(50), nullable=False)
    turn_number: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active_character_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.utcnow(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow(), nullable=False
    )

    # Relationships
    campaign: Mapped[CampaignDB] = relationship("CampaignDB", back_populates="game_sessions")
    maps: Mapped[List["MapDB"]] = relationship(
        "MapDB", back_populates="game_session", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<GameSession(id={self.id}, phase={self.phase}, turn={self.turn_number})>"


class MapDB(Base):
    """Map model for storing game map data."""

    __tablename__ = "map"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("game_session.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    grid: Mapped[List[List[str]]] = mapped_column(JSON, default=list, nullable=False)
    tokens: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    fog_revealed: Mapped[List[List[bool]]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.utcnow(), nullable=False
    )

    # Relationships
    game_session: Mapped[GameSessionDB] = relationship("GameSessionDB", back_populates="maps")

    def __repr__(self) -> str:
        return f"<Map(id={self.id}, name={self.name}, size={self.width}x{self.height})>"


class UserDB(Base):
    """User model for storing user authentication data."""

    __tablename__ = "user"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.utcnow(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"
