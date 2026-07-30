"""Streaming narration — WS action must broadcast narration_chunk frames
before the final turn_result when the narrator's LLM supports streaming."""
import pytest
from starlette.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import create_app
from app.models.database import Base
from app.db import get_db
from app.api import storage
from app.services.llm.base import FakeLLM
from app.services.llm.narrator import DMNarrator

_engine = create_async_engine("sqlite+aiosqlite://", echo=False)
_session_factory = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)


async def _override_get_db():
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest.fixture
def ws_client():
    import asyncio

    async def setup():
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.get_event_loop().run_until_complete(setup())

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db
    app.state.db_factory = _session_factory
    # Streaming-capable fake narrator
    llm = FakeLLM(
        default_response="The tavern falls silent as you enter.",
        default_chunks=["The tavern ", "falls silent ", "as you enter."],
    )
    app.state.narrator = DMNarrator(llm=llm, max_history=30)

    storage.reset()
    client = TestClient(app)
    yield client

    async def teardown():
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    asyncio.get_event_loop().run_until_complete(teardown())
    storage.reset()


def _create_session(client: TestClient) -> str:
    campaign = client.post("/api/campaigns", json={
        "name": "Stream Test", "description": "", "character_ids": [],
        "world_state": {}, "dm_settings": {},
    }).json()
    session = client.post("/api/game/sessions", json={
        "campaign_id": campaign["id"],
        "current_phase": "exploration",
        "current_scene": "You enter a tavern.",
    }).json()
    return session["id"]


def test_ws_action_streams_chunks_then_turn_result(ws_client: TestClient):
    session_id = _create_session(ws_client)

    with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
        ws.receive_json()  # player_joined

        ws.send_json({"type": "action", "character_id": "c1", "action": "I enter the tavern"})

        chunks: list[str] = []
        turn_result = None
        for _ in range(10):
            msg = ws.receive_json()
            if msg["type"] == "narration_chunk":
                chunks.append(msg["chunk"])
            elif msg["type"] == "turn_result":
                turn_result = msg
                break

        assert chunks == ["The tavern ", "falls silent ", "as you enter."]
        assert turn_result is not None
        assert turn_result["narration"] == "The tavern falls silent as you enter."
        # Chunks carry ordering info for clients
        assert [i + 1 for i in range(len(chunks))] == [1, 2, 3]


def test_ws_action_without_narrator_still_returns_turn_result(ws_client: TestClient):
    ws_client.app.state.narrator = None  # type: ignore[attr-defined]
    session_id = _create_session(ws_client)

    with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
        ws.receive_json()  # player_joined
        ws.send_json({"type": "action", "character_id": "c1", "action": "I look around"})

        msg = ws.receive_json()
        while msg["type"] == "narration_chunk":
            msg = ws.receive_json()
        assert msg["type"] == "turn_result"
        assert msg["narration"]
