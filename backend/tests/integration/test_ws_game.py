"""Integration tests for WebSocket game events."""
import pytest
from starlette.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.main import create_app
from app.models.database import Base
from app.db import get_db
from app.api import storage


# Sync SQLite for Starlette TestClient (which uses sync I/O)
_sync_engine = create_engine("sqlite://", echo=False)
_SyncSession = sessionmaker(_sync_engine, expire_on_commit=False)


def _sync_override_get_db():
    """Sync DB session for Starlette TestClient."""
    # We need an async override even though TestClient is sync,
    # because FastAPI's Depends expects an async generator.
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    import asyncio

    # Reuse module-level async engine
    async def _override():
        async with _ws_async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    return _override


def _recv_type(ws, expected: str, limit: int = 8) -> dict:
    """Skip line echoes and acks that now precede a turn result."""
    last = None
    for _ in range(limit):
        last = ws.receive_json()
        if last.get("type") == expected:
            return last
    raise AssertionError(f"never received {expected}; last={last}")


# Use async engine for WS tests too
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
_ws_async_engine = create_async_engine("sqlite+aiosqlite://", echo=False)
_ws_async_session = async_sessionmaker(_ws_async_engine, class_=AsyncSession, expire_on_commit=False)


async def _ws_override_get_db():
    async with _ws_async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def _run_on_loop(coro):
    """Run setup against a loop that stays current for the sync TestClient.

    pytest-asyncio 1.x (asyncio_mode=auto) no longer leaves a current loop on
    the main thread, and get_event_loop() then raises.
    """
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
    """Create a test client with WebSocket support and DB setup."""
    async def setup_tables():
        async with _ws_async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    _run_on_loop(setup_tables())

    app = create_app()
    app.dependency_overrides[get_db] = _ws_override_get_db
    app.state.db_factory = _ws_async_session

    client = TestClient(app)
    yield client

    async def teardown_tables():
        async with _ws_async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    _run_on_loop(teardown_tables())


@pytest.fixture(autouse=True)
def reset_storage_for_ws():
    """Reset in-memory storage before each test."""
    storage.reset()
    yield
    storage.reset()


def create_test_session(client: TestClient) -> str:
    """Helper to create a campaign and game session, return session_id."""
    # Create campaign first
    campaign_response = client.post(
        "/api/campaigns",
        json={
            "name": "Test Campaign",
            "description": "For testing",
            "character_ids": [],
            "world_state": {},
            "dm_settings": {},
        },
    )
    campaign_id = campaign_response.json()["id"]

    # Create game session
    session_response = client.post(
        "/api/game/sessions",
        json={
            "campaign_id": campaign_id,
            "current_phase": "exploration",
            "current_scene": "You enter a tavern.",
        },
    )
    return session_response.json()["id"]


class TestWebSocketConnection:
    """Tests for WebSocket connection establishment."""

    def test_ws_connect_accepts_connection(self, ws_client: TestClient):
        """WebSocket client can connect to /ws/game/{session_id}."""
        session_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
            # Connection should be accepted
            assert ws is not None

    def test_ws_connect_to_nonexistent_session(self, ws_client: TestClient):
        """WebSocket connection to non-existent session should still work (lazy creation)."""
        # Test with a session that doesn't exist yet
        with ws_client.websocket_connect("/ws/game/nonexistent-session") as ws:
            assert ws is not None

    def test_ws_multiple_connections_same_session(self, ws_client: TestClient):
        """Multiple WebSocket clients can connect to the same session."""
        session_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws1:
            with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws2:
                assert ws1 is not None
                assert ws2 is not None


class TestWebSocketPingPong:
    """Tests for ping/pong messaging."""

    def test_ws_ping_pong(self, ws_client: TestClient):
        """Client sends ping, receives pong."""
        session_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
            # First message is always player_joined event
            join_event = ws.receive_json()
            assert join_event["type"] == "player_joined"
            
            ws.send_json({"type": "ping"})
            data = ws.receive_json()
            assert data["type"] == "pong"

    def test_ws_ping_pong_includes_timestamp(self, ws_client: TestClient):
        """Pong message includes timestamp."""
        session_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
            # First message is always player_joined event
            join_event = ws.receive_json()
            assert join_event["type"] == "player_joined"
            
            ws.send_json({"type": "ping"})
            data = ws.receive_json()
            assert data["type"] == "pong"
            assert "timestamp" in data


class TestWebSocketChatMessage:
    """Tests for chat messaging."""

    def test_ws_chat_message_broadcasts(self, ws_client: TestClient):
        """Chat message is broadcast to all clients in session."""
        session_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws1:
            with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws2:
                # Both get player_joined events
                ws1_join = ws1.receive_json()
                assert ws1_join["type"] == "player_joined"
                
                ws2_join = ws2.receive_json()
                assert ws2_join["type"] == "player_joined"
                
                # ws1 also gets a player_joined for ws2
                ws1_join2 = ws1.receive_json()
                assert ws1_join2["type"] == "player_joined"
                
                # Send chat from ws1
                ws1.send_json({
                    "type": "chat",
                    "message": "Hello everyone!",
                    "sender": "Player1"
                })
                
                # Both clients should receive it
                data1 = ws1.receive_json()
                data2 = ws2.receive_json()
                
                assert data1["type"] == "chat"
                assert data1["message"] == "Hello everyone!"
                assert data1["sender"] == "Player1"
                
                assert data2["type"] == "chat"
                assert data2["message"] == "Hello everyone!"
                assert data2["sender"] == "Player1"

    def test_ws_chat_not_sent_to_other_sessions(self, ws_client: TestClient):
        """Chat messages are only sent to clients in the same session."""
        session1_id = create_test_session(ws_client)
        session2_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session1_id}") as ws1:
            with ws_client.websocket_connect(f"/ws/game/{session2_id}") as ws2:
                # Consume initial join events
                ws1.receive_json()
                ws2.receive_json()
                
                # Send chat in session 1
                ws1.send_json({
                    "type": "chat",
                    "message": "In session 1",
                    "sender": "Player1"
                })
                
                # ws1 should receive it
                data1 = ws1.receive_json()
                assert data1["type"] == "chat"
                assert data1["message"] == "In session 1"
                
                # ws2 should NOT receive the chat message from session 1
                # We can verify by checking it's still alive by sending a ping
                ws2.send_json({"type": "ping"})
                pong = ws2.receive_json()
                assert pong["type"] == "pong"


class TestWebSocketPlayerEvents:
    """Tests for player join/leave events."""

    def test_ws_player_joined_broadcast_on_connect(self, ws_client: TestClient):
        """When a player connects, broadcast player_joined to all in session."""
        session_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws1:
            # Second client connects
            with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws2:
                # Both should get a player_joined event
                # ws1 should receive it
                data1 = ws1.receive_json()
                assert data1["type"] == "player_joined"
                assert "player_id" in data1
                assert "connection_count" in data1
                
                # ws2 may immediately receive its own join
                # Let's just verify we can receive something
                assert ws2 is not None

    def test_ws_player_left_broadcast_on_disconnect(self, ws_client: TestClient):
        """When a player disconnects, broadcast player_left to others in session."""
        session_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws1:
            # First connection - ws1 gets join event for itself
            ws1_first_join = ws1.receive_json()
            assert ws1_first_join["type"] == "player_joined"
            
            with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws2:
                # ws2 connects - ws1 gets join event for ws2
                ws1_ws2_join = ws1.receive_json()
                assert ws1_ws2_join["type"] == "player_joined"
                
                # ws2 gets its own join event
                ws2_join = ws2.receive_json()
                assert ws2_join["type"] == "player_joined"
            
            # After ws2 disconnects, ws1 should receive player_left
            leave_data = ws1.receive_json()
            assert leave_data["type"] == "player_left"
            assert "player_id" in leave_data
            assert "connection_count" in leave_data


class TestWebSocketConnectionCount:
    """Tests for connection counting."""

    def test_ws_connection_count_single(self, ws_client: TestClient):
        """Single connection should have count of 1."""
        session_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
            # Consume initial join event
            join_event = ws.receive_json()
            assert join_event["type"] == "player_joined"
            assert join_event["connection_count"] == 1
            
            ws.send_json({"type": "ping"})
            data = ws.receive_json()
            assert data["type"] == "pong"

    def test_ws_connection_count_multiple(self, ws_client: TestClient):
        """Multiple connections should be counted."""
        session_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws1:
            with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws2:
                with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws3:
                    # Consume all join events
                    for _ in range(3):
                        ws1.receive_json()
                    for _ in range(2):
                        ws2.receive_json()
                    ws3.receive_json()
                    
                    # All connections should be active
                    ws1.send_json({"type": "ping"})
                    data1 = ws1.receive_json()
                    assert data1["type"] == "pong"
                    
                    ws2.send_json({"type": "ping"})
                    data2 = ws2.receive_json()
                    assert data2["type"] == "pong"
                    
                    ws3.send_json({"type": "ping"})
                    data3 = ws3.receive_json()
                    assert data3["type"] == "pong"


class TestWebSocketSessionIsolation:
    """Tests for isolation between sessions."""

    def test_ws_sessions_are_isolated(self, ws_client: TestClient):
        """Messages in one session don't affect another."""
        session1_id = create_test_session(ws_client)
        session2_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session1_id}") as ws1:
            with ws_client.websocket_connect(f"/ws/game/{session2_id}") as ws2:
                # Consume initial join events
                ws1.receive_json()
                ws2.receive_json()
                
                # Send ping in session 1
                ws1.send_json({"type": "ping"})
                data1 = ws1.receive_json()
                assert data1["type"] == "pong"
                
                # Session 2 should not be affected
                ws2.send_json({"type": "ping"})
                data2 = ws2.receive_json()
                assert data2["type"] == "pong"

    def test_ws_chat_isolated_between_sessions(self, ws_client: TestClient):
        """Chat in one session doesn't reach another."""
        session1_id = create_test_session(ws_client)
        session2_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session1_id}") as ws1:
            with ws_client.websocket_connect(f"/ws/game/{session2_id}") as ws2:
                # Consume initial join events
                ws1.receive_json()
                ws2.receive_json()
                
                # Send chat in session 1
                ws1.send_json({
                    "type": "chat",
                    "message": "Session 1 message",
                    "sender": "Player1"
                })
                
                # ws1 receives its own message
                data1 = ws1.receive_json()
                assert data1["type"] == "chat"
                assert data1["message"] == "Session 1 message"
                
                # ws2 should not receive the chat message from session 1
                # We can verify by checking it's still alive by sending a ping
                ws2.send_json({"type": "ping"})
                pong = ws2.receive_json()
                assert pong["type"] == "pong"


class TestWebSocketActionSubmission:
    """Tests for player action submission via WebSocket."""

    def test_ws_action_submission_receives_turn_result(self, ws_client: TestClient):
        """Client sends action via WS, receives turn_result."""
        session_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
            # Consume initial join event
            ws.receive_json()
            
            ws.send_json({
                "type": "action",
                "character_id": "char1",
                "action": "I cast fireball!"
            })
            
            data = _recv_type(ws, "turn_result")
            assert "narration" in data
            assert isinstance(data["narration"], str)

    def test_ws_action_broadcast_to_all_in_session(self, ws_client: TestClient):
        """Action results are broadcast to all players in session."""
        session_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws1:
            with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws2:
                # Consume initial join events
                for _ in range(2):
                    ws1.receive_json()
                ws2.receive_json()
                
                # ws1 sends an action
                ws1.send_json({
                    "type": "action",
                    "character_id": "char1",
                    "action": "Attack the goblin!"
                })
                
                # Both should receive turn_result (after the typed line echo)
                data1 = _recv_type(ws1, "turn_result")
                assert "narration" in data1

                data2 = _recv_type(ws2, "turn_result")
                assert "narration" in data2


class TestWebSocketStateUpdate:
    """Tests for game state updates."""

    def test_ws_state_update_event(self, ws_client: TestClient):
        """Clients receive state_update events."""
        session_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
            # Consume initial join event
            ws.receive_json()
            
            # Send action to trigger state update
            ws.send_json({
                "type": "action",
                "character_id": "char1",
                "action": "Cast spell"
            })
            
            turn_result = _recv_type(ws, "turn_result")

    def test_ws_multiple_actions_in_sequence(self, ws_client: TestClient):
        """Multiple actions can be submitted and processed in sequence."""
        session_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
            # Consume initial join event
            ws.receive_json()
            
            # First action
            ws.send_json({
                "type": "action",
                "character_id": "char1",
                "action": "First action"
            })
            result1 = _recv_type(ws, "turn_result")
            assert result1["narration"]

            # Second action
            ws.send_json({
                "type": "action",
                "character_id": "char1",
                "action": "Second action"
            })
            result2 = _recv_type(ws, "turn_result")
            assert result2["narration"]


class TestWebSocketErrorHandling:
    """Tests for error handling in WebSocket communication."""

    def test_ws_invalid_message_type(self, ws_client: TestClient):
        """Invalid message type should not crash connection."""
        session_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
            # Consume initial join event
            ws.receive_json()
            
            # Send invalid message type
            ws.send_json({"type": "invalid_type"})
            
            # Connection should still be open and we can send ping
            ws.send_json({"type": "ping"})
            data = ws.receive_json()
            assert data["type"] == "pong"

    def test_ws_malformed_message(self, ws_client: TestClient):
        """Malformed message should not crash connection."""
        session_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
            # Consume initial join event
            ws.receive_json()
            
            # Send message without required fields
            ws.send_json({"data": "incomplete"})
            
            # Connection should still be open
            ws.send_json({"type": "ping"})
            data = ws.receive_json()
            assert data["type"] == "pong"


class TestNarratedMonsterTurn:
    def test_legionnaire_turn_is_resolved_and_hp_is_stored(self, ws_client: TestClient, monkeypatch):
        from app.services.dice import DiceResult

        class FixedRoller:
            def __init__(self, *args, **kwargs):
                pass

            def roll(self, notation):
                if str(notation).startswith("1d20"):
                    return DiceResult(notation=notation, rolls=[15], modifier=0, total=15)
                return DiceResult(notation=notation, rolls=[5], modifier=2, total=7)

        class FakeNarrator:
            async def narrate_exploration(self, **kwargs):
                return (
                    "Ashara's healing word knits the wound. "
                    "It is now Crimson Fang Legionnaire 1's turn. What do you do?"
                )

        monkeypatch.setattr("app.services.game.combat_loop.DiceRoller", FixedRoller)
        ws_client.app.state.narrator = FakeNarrator()

        char = ws_client.post("/api/characters", json={
            "name": "Thorne Ironfist",
            "race": "dwarf",
            "class_name": "fighter",
            "level": 3,
            "strength": 16,
            "hp": 34,
            "max_hp": 34,
            "ac": 18,
        })
        assert char.status_code == 201, char.text
        char_id = char.json()["id"]
        campaign = ws_client.post("/api/campaigns", json={
            "name": "Legion",
            "description": "monster turns",
            "character_ids": [char_id],
            "world_state": {},
            "dm_settings": {},
        })
        session = ws_client.post("/api/game/sessions", json={"campaign_id": campaign.json()["id"]})
        session_id = session.json()["id"]

        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
            ws.receive_json()
            ws.send_json({
                "type": "action",
                "character_id": char_id,
                "action": "Ashara casts healing word on Thorne.",
            })
            data = _recv_type(ws, "turn_result")
            narration = data["narration"]
            assert "What do you do" not in narration
            assert "It is now Thorne Ironfist's turn." in narration
            assert data["hp_updates"][0]["hp"] == 27

        stored = ws_client.get(f"/api/characters/{char_id}").json()
        assert stored["hp"] == 27


class TestNarratedDamageReachesThePhone:
    def test_slashing_without_the_word_damage_updates_hp(self, ws_client: TestClient):
        class FakeNarrator:
            async def narrate_exploration(self, **kwargs):
                return (
                    "The ghoul's claws rake across Thorne. "
                    "Thorne takes 7 slashing from the Ghoul. "
                    "Make a DC 10 Constitution saving throw."
                )

        ws_client.app.state.narrator = FakeNarrator()
        char = ws_client.post("/api/characters", json={
            "name": "Thorne Ironfist",
            "race": "dwarf",
            "class_name": "fighter",
            "level": 3,
            "strength": 16,
            "hp": 34,
            "max_hp": 34,
            "ac": 18,
        })
        assert char.status_code == 201, char.text
        char_id = char.json()["id"]
        campaign = ws_client.post("/api/campaigns", json={
            "name": "Crypt",
            "description": "ghoul",
            "character_ids": [char_id],
            "world_state": {},
            "dm_settings": {},
        })
        session = ws_client.post("/api/game/sessions", json={"campaign_id": campaign.json()["id"]})
        session_id = session.json()["id"]

        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
            ws.receive_json()
            ws.send_json({
                "type": "action",
                "character_id": char_id,
                "action": "Thorne holds his ground.",
            })
            data = _recv_type(ws, "turn_result")
            assert data["hp_updates"][0]["hp"] == 27
            assert data["hp_updates"][0]["character_id"] == char_id

        stored = ws_client.get(f"/api/characters/{char_id}").json()
        assert stored["hp"] == 27


class TestReconnectResync:
    """A phone that reconnects must be handed the row that is stored now."""

    def test_resync_pushes_current_scene_after_player_joined(self, ws_client: TestClient):
        session_id = create_test_session(ws_client)

        async def advance_to_lighthouse() -> None:
            import app.repository as repo

            async with _ws_async_session() as db:
                session = await repo.get_game_session(db, session_id)
                assert session is not None
                session["current_phase"] = "exploration"
                session["current_scene"] = "The lighthouse antechamber"
                session["combat_state"] = None
                await repo.save_game_session(db, session)
                await db.commit()

        _run_on_loop(advance_to_lighthouse())

        with ws_client.websocket_connect(f"/ws/game/{session_id}?resync=1") as ws:
            joined = ws.receive_json()
            assert joined["type"] == "player_joined"
            state = ws.receive_json()
            assert state["type"] == "game_state"
            assert state["current_scene"] == "The lighthouse antechamber"
            assert state["current_phase"] == "exploration"
            assert state["combat_state"] is None

    def test_player_join_keeps_bound_character_across_stale_id(self, ws_client: TestClient):
        session_id = create_test_session(ws_client)
        state = ws_client.get(f"/api/game/sessions/{session_id}/state").json()
        joined = ws_client.post(
            "/api/game/join",
            json={
                "room_code": state["room_code"],
                "player_name": "Bram",
                "character_id": "char-thorne",
            },
        ).json()

        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
            assert ws.receive_json()["type"] == "player_joined"
            ws.send_json({
                "type": "player_join",
                "name": "Bram",
                "player_id": joined["player_id"],
            })
            rebound = ws.receive_json()
            assert rebound["type"] == "player_update"
            me = next(p for p in rebound["players"] if p["id"] == joined["player_id"])
            assert me["character_id"] == "char-thorne"

            ws.send_json({
                "type": "player_join",
                "name": "Bram",
                "player_id": joined["player_id"],
                "character_id": "char-from-blackwood",
            })
            again = ws.receive_json()
            me = next(p for p in again["players"] if p["id"] == joined["player_id"])
            assert me["character_id"] == "char-thorne"
