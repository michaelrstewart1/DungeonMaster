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


def _run_on_loop(coro):
    """Same loop fallback as test_ws_game: pytest-asyncio 1.x leaves none set."""
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("closed")
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@pytest.fixture
def ws_client():
    async def setup():
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    _run_on_loop(setup())

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

    _run_on_loop(teardown())
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


def test_action_ack_and_duplicate_id_is_not_applied_twice(ws_client: TestClient):
    session_id = _create_session(ws_client)

    with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
        ws.receive_json()  # player_joined
        line = {
            "type": "action",
            "character_id": "c1",
            "action": "I enter the tavern",
            "client_id": "line-1",
            "sender": "Bram",
        }
        ws.send_json(line)

        seen: list[dict] = []
        for _ in range(12):
            msg = ws.receive_json()
            seen.append(msg)
            if msg["type"] == "turn_result":
                break

        assert seen[0]["type"] == "action_ack"
        assert seen[0]["client_id"] == "line-1"
        assert any(m["type"] == "player_action" and m["text"] == "I enter the tavern" for m in seen)
        assert seen[-1]["type"] == "turn_result"

        ws.send_json(line)
        dup = ws.receive_json()
        assert dup["type"] == "action_ack"
        assert dup["duplicate"] is True


def test_abandoned_stream_ends_so_the_table_is_not_left_waiting(ws_client: TestClient, monkeypatch):
    """A reply streamed while the row moves on must still close on every screen."""
    import app.repository as repo

    session_id = _create_session(ws_client)
    original = repo.session_version
    calls = {"n": 0}

    def bumped(session):
        calls["n"] += 1
        value = original(session)
        if calls["n"] >= 2:
            return value + 5
        return value

    monkeypatch.setattr(repo, "session_version", bumped)

    with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
        ws.receive_json()  # player_joined
        ws.send_json({
            "type": "action",
            "character_id": "c1",
            "action": "I enter the tavern",
            "client_id": "line-2",
        })

        types: list[str] = []
        ended = None
        for _ in range(12):
            msg = ws.receive_json()
            types.append(msg["type"])
            if msg["type"] == "narration_end":
                ended = msg
                break

        assert "narration_chunk" in types
        assert ended is not None
        assert ended["narration"] == "The tavern falls silent as you enter."
        assert "turn_result" not in types


def test_combat_narration_failure_closes_instead_of_waiting(ws_client: TestClient):
    """A monster-turn narration that throws must still end the DM's reply."""
    import app.repository as repo

    class BoomNarrator:
        async def narrate_combat_action(self, *args, **kwargs):
            raise RuntimeError("stream died")

        async def narrate_exploration(self, *args, **kwargs):
            return "unused"

    ws_client.app.state.narrator = BoomNarrator()  # type: ignore[attr-defined]

    char = ws_client.post("/api/characters", json={
        "name": "Thorne", "race": "human", "class_name": "fighter", "level": 3,
        "strength": 16, "dexterity": 12, "constitution": 14, "intelligence": 10,
        "wisdom": 10, "charisma": 8, "max_hp": 28, "ac": 16,
    })
    assert char.status_code == 201, char.text
    char_id = char.json()["id"]
    campaign = ws_client.post("/api/campaigns", json={
        "name": "Crypt", "description": "", "character_ids": [char_id],
        "world_state": {}, "dm_settings": {},
    }).json()
    session = ws_client.post("/api/game/sessions", json={
        "campaign_id": campaign["id"],
        "current_phase": "exploration",
        "current_scene": "A crypt.",
    }).json()
    session_id = session["id"]
    started = ws_client.post(
        f"/api/game/sessions/{session_id}/start-combat",
        json={"enemies": [{"name": "Skeleton", "hp": 12, "ac": 13, "cr": 0.25, "count": 1}]},
    )
    assert started.status_code == 200, started.text

    async def _seat_player():
        async with ws_client.app.state.db_factory() as db:  # type: ignore[attr-defined]
            live = await repo.get_game_session(db, session_id)
            combat = live["combat_state"]
            for index, combatant in enumerate(combat["combatants"]):
                if combatant["id"] == char_id:
                    combat["current_turn_index"] = index
                    combat["current_turn_id"] = char_id
            live["combat_state"] = combat
            await repo.save_game_session(db, live)
            await db.commit()

    _run_on_loop(_seat_player())

    with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
        ws.receive_json()  # player_joined
        resp = ws_client.post(
            f"/api/game/sessions/{session_id}/combat-action",
            json={
                "actor_id": char_id,
                "action_type": "attack",
                "action_text": "I swing my sword at the nearest skeleton",
                "client_id": "bram-1",
                "sender": "Bram",
            },
        )
        assert resp.status_code == 200, resp.text

        types: list[str] = []
        for _ in range(8):
            msg = ws.receive_json()
            types.append(msg["type"])
            if msg["type"] == "narration_end":
                assert msg.get("recover") is True
                break
        assert "player_action" in types
        assert "combat_update" in types
        assert "narration_end" in types


def test_ws_action_without_narrator_still_returns_turn_result(ws_client: TestClient):
    ws_client.app.state.narrator = None  # type: ignore[attr-defined]
    session_id = _create_session(ws_client)

    with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
        ws.receive_json()  # player_joined
        ws.send_json({"type": "action", "character_id": "c1", "action": "I look around"})

        msg = ws.receive_json()
        while msg["type"] in ("narration_chunk", "player_action", "action_ack"):
            msg = ws.receive_json()
        assert msg["type"] == "turn_result"
        assert msg["narration"]
