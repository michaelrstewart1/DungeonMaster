"""
Database connection and session management for the Dungeon Master application.
"""
import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from sqlalchemy import text

# Use DM_DATABASE_URL (matching pydantic settings env_prefix) with fallback
DATABASE_URL = os.getenv("DM_DATABASE_URL", os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./dungeon_master.db"))

# Create async engine
connect_args = {}
if "sqlite" in DATABASE_URL:
    connect_args = {"timeout": 30}  # 30s busy timeout for SQLite

engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    poolclass=NullPool if "sqlite" in DATABASE_URL else None,
    connect_args=connect_args,
)

# Create async session factory
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields a session that auto-commits on success."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Initialize database tables from Base metadata."""
    from app.models.database import Base

    async with engine.begin() as conn:
        # Enable WAL mode for SQLite (better concurrent access)
        if "sqlite" in DATABASE_URL:
            await conn.execute(text("PRAGMA journal_mode=WAL"))
            await conn.execute(text("PRAGMA busy_timeout=30000"))
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    """Drop all database tables. USE WITH CAUTION."""
    from app.models.database import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def close_db() -> None:
    """Close database connection pool."""
    await engine.dispose()
