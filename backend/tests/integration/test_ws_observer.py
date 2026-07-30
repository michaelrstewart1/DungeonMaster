"""Integration tests for read-only observer WebSocket connections.

Observers connect with `?role=observer` and must be able to watch the
game without impacting it in any way:
- no player_joined / player_left broadcasts for them
- excluded from connection_count
- server-enforced read-only (mutating messages ignored)
- still receive all game broadcasts
"""
import pytest
from starlette.testclient import TestClient

from tests.integration.test_ws_game import (  # noqa: F401 (fixtures)
    ws_client,
    reset_storage_for_ws,
    create_test_session,
)


def _drain_until(ws, wanted_type: str, limit: int = 10):
    """Receive messages until one of the wanted type arrives."""
    for _ in range(limit):
        msg = ws.receive_json()
        if msg.get("type") == wanted_type:
            return msg
    raise AssertionError(f"never received message of type {wanted_type!r}")


class TestObserverConnection:
    """Observer connections are invisible and side-effect free."""

    def test_observer_gets_private_ack(self, ws_client: TestClient):
        session_id = create_test_session(ws_client)
        with ws_client.websocket_connect(f"/ws/game/{session_id}?role=observer") as ws:
            msg = ws.receive_json()
            assert msg["type"] == "observer_ack"
            assert msg["observer_count"] == 1

    def test_observer_join_is_invisible_to_players(self, ws_client: TestClient):
        session_id = create_test_session(ws_client)
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as player:
            _drain_until(player, "player_joined")
            with ws_client.websocket_connect(f"/ws/game/{session_id}?role=observer") as obs:
                obs.receive_json()  # observer_ack
                # Observer join must broadcast NOTHING; prove the pipe works
                # by chatting and asserting chat is the next player frame.
                player.send_json({"type": "chat", "message": "hi", "sender": "P1"})
                msg = player.receive_json()
                assert msg["type"] == "chat"

    def test_observer_excluded_from_connection_count(self, ws_client: TestClient):
        session_id = create_test_session(ws_client)
        with ws_client.websocket_connect(f"/ws/game/{session_id}?role=observer"):
            with ws_client.websocket_connect(f"/ws/game/{session_id}") as player:
                msg = _drain_until(player, "player_joined")
                # The observer must not inflate the player count.
                assert msg["connection_count"] == 1

    def test_observer_leave_is_invisible_to_players(self, ws_client: TestClient):
        session_id = create_test_session(ws_client)
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as player:
            _drain_until(player, "player_joined")
            with ws_client.websocket_connect(f"/ws/game/{session_id}?role=observer") as obs:
                obs.receive_json()  # observer_ack
            # Observer just disconnected — no player_left may be broadcast.
            player.send_json({"type": "chat", "message": "still here", "sender": "P1"})
            msg = player.receive_json()
            assert msg["type"] == "chat"


class TestObserverReadOnly:
    """The server enforces read-only regardless of what the client sends."""

    @pytest.mark.parametrize("payload", [
        {"type": "chat", "message": "sneaky", "sender": "Obs"},
        {"type": "action", "character_id": "c1", "action": "attack"},
        {"type": "player_join", "name": "Obs"},
        {"type": "player_ready", "ready": True},
        {"type": "dice_roll", "notation": "1d20", "result": 20},
        {"type": "token_move", "token_id": "t1", "x": 1, "y": 2},
        {"type": "fog_update", "revealed": [[0, 0]]},
        {"type": "map_sync", "map_data": {}},
    ])
    def test_mutating_messages_rejected(self, ws_client: TestClient, payload: dict):
        session_id = create_test_session(ws_client)
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as player:
            _drain_until(player, "player_joined")
            with ws_client.websocket_connect(f"/ws/game/{session_id}?role=observer") as obs:
                obs.receive_json()  # observer_ack
                obs.send_json(payload)
                err = obs.receive_json()
                assert err["type"] == "error"
                assert "read-only" in err["message"]
                # Nothing may reach the players.
                player.send_json({"type": "chat", "message": "probe", "sender": "P1"})
                msg = player.receive_json()
                assert msg["type"] == "chat"
                assert msg["message"] == "probe"

    def test_observer_ping_still_works(self, ws_client: TestClient):
        session_id = create_test_session(ws_client)
        with ws_client.websocket_connect(f"/ws/game/{session_id}?role=observer") as obs:
            obs.receive_json()  # observer_ack
            obs.send_json({"type": "ping"})
            msg = obs.receive_json()
            assert msg["type"] == "pong"

    def test_observer_never_appears_in_roster(self, ws_client: TestClient):
        session_id = create_test_session(ws_client)
        with ws_client.websocket_connect(f"/ws/game/{session_id}?role=observer") as obs:
            obs.receive_json()
            obs.send_json({"type": "player_join", "name": "Sneaky Observer"})
            obs.receive_json()  # read-only error
        res = ws_client.get(f"/api/game/sessions/{session_id}/players")
        assert res.status_code == 200
        names = [p["name"] for p in res.json()["players"]]
        assert "Sneaky Observer" not in names


class TestObserverReceivesBroadcasts:
    """Observers still see everything that happens in the game."""

    def test_observer_receives_chat(self, ws_client: TestClient):
        session_id = create_test_session(ws_client)
        with ws_client.websocket_connect(f"/ws/game/{session_id}?role=observer") as obs:
            obs.receive_json()  # observer_ack
            with ws_client.websocket_connect(f"/ws/game/{session_id}") as player:
                player.send_json({"type": "chat", "message": "hello table", "sender": "P1"})
                msg = _drain_until(obs, "chat")
                assert msg["message"] == "hello table"

    def test_observer_sees_player_roster_updates(self, ws_client: TestClient):
        session_id = create_test_session(ws_client)
        with ws_client.websocket_connect(f"/ws/game/{session_id}?role=observer") as obs:
            obs.receive_json()
            with ws_client.websocket_connect(f"/ws/game/{session_id}") as player:
                player.send_json({"type": "player_join", "name": "Alice"})
                msg = _drain_until(obs, "player_update")
                assert any(p["name"] == "Alice" for p in msg["players"])


class TestResolveRoomCode:
    """GET /api/game/resolve-code/{code} resolves without joining."""

    def test_resolve_code_no_roster_side_effect(self, ws_client: TestClient):
        session_id = create_test_session(ws_client)
        code = ws_client.get(f"/api/game/sessions/{session_id}/room-code").json()["room_code"]

        res = ws_client.get(f"/api/game/resolve-code/{code.lower()}")
        assert res.status_code == 200
        assert res.json()["session_id"] == session_id

        players = ws_client.get(f"/api/game/sessions/{session_id}/players").json()["players"]
        assert players == []

    def test_resolve_invalid_code_404(self, ws_client: TestClient):
        res = ws_client.get("/api/game/resolve-code/ZZZZ")
        assert res.status_code == 404
