"""Runtime store persistence — state must survive a backend restart."""
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.api import storage
from app.models.database import Base


@pytest.fixture
async def db_factory():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield factory
    await engine.dispose()


@pytest.mark.asyncio
async def test_persist_and_load_round_trip(db_factory):
    storage.reset()
    storage.configure(db_factory)

    storage.room_codes["ABCD"] = "session-1"
    storage.session_players["session-1"] = [{"id": "p1", "name": "Aria"}]
    storage.trades["t1"] = {"id": "t1", "session_id": "session-1", "status": "pending"}
    storage.tokens["tok"] = "user-1"
    storage.vision_analyses["session-1"] = {"tokens": []}

    await storage.persist()

    # Simulate restart: clear in-memory state, then reload from DB
    for store in (storage.room_codes, storage.session_players, storage.trades,
                  storage.tokens, storage.vision_analyses):
        store.clear()
    storage.configure(db_factory)
    await storage.load_from_db()

    assert storage.room_codes["ABCD"] == "session-1"
    assert storage.session_players["session-1"][0]["name"] == "Aria"
    assert storage.trades["t1"]["status"] == "pending"
    assert storage.tokens["tok"] == "user-1"
    assert storage.vision_analyses["session-1"] == {"tokens": []}

    storage.reset()


@pytest.mark.asyncio
async def test_persist_named_store_only(db_factory):
    storage.reset()
    storage.configure(db_factory)

    storage.room_codes["WXYZ"] = "session-2"
    storage.trades["t2"] = {"id": "t2", "status": "pending"}
    await storage.persist("room_codes")

    storage.room_codes.clear()
    storage.trades.clear()
    storage.configure(db_factory)
    await storage.load_from_db()

    assert storage.room_codes.get("WXYZ") == "session-2"
    assert "t2" not in storage.trades  # not persisted

    storage.reset()


@pytest.mark.asyncio
async def test_flush_noop_without_factory():
    storage.reset()
    storage.room_codes["QRST"] = "session-3"
    # Must not raise when no DB factory is configured (unit tests, scripts)
    storage.flush("room_codes")
    await storage.persist()
    storage.reset()
