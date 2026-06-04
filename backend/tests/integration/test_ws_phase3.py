"""Phase 3 additive WS behavior: player_id reconciliation + dice_roll broadcast.

These extend test_ws_game.py and reuse its fixtures.
"""
import pytest
from starlette.testclient import TestClient

from tests.integration.test_ws_game import ws_client, reset_storage_for_ws, create_test_session  # noqa: F401


class TestPlayerIdReconciliation:
    """`player_join` with a player_id matching an HTTP-join row adopts it."""

    def test_ws_player_join_with_known_id_reuses_it(self, ws_client: TestClient):
        session_id = create_test_session(ws_client)

        # First obtain a room code and HTTP-join, which registers a player_id.
        rc = ws_client.get(f"/api/game/sessions/{session_id}/room-code").json()["room_code"]
        joined = ws_client.post(
            "/api/game/join",
            json={"room_code": rc, "player_name": "Alice"},
        ).json()
        http_pid = joined["player_id"]

        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
            ws.receive_json()  # player_joined
            ws.send_json({
                "type": "player_join",
                "name": "Alice",
                "character_id": None,
                "player_id": http_pid,
            })
            update = ws.receive_json()
            assert update["type"] == "player_update"
            ids = [p["id"] for p in update["players"]]
            # The HTTP player_id should appear exactly once and not be
            # duplicated with a new WS-generated id.
            assert ids.count(http_pid) == 1, ids
            assert len(ids) == 1, f"expected single reconciled player, got {ids}"

    def test_ws_player_join_with_unknown_id_falls_back_to_generated(self, ws_client: TestClient):
        session_id = create_test_session(ws_client)
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
            ws.receive_json()  # player_joined
            ws.send_json({
                "type": "player_join",
                "name": "Bob",
                "character_id": None,
                "player_id": "00000000-not-a-real-id-0000",
            })
            update = ws.receive_json()
            assert update["type"] == "player_update"
            ids = [p["id"] for p in update["players"]]
            assert "00000000-not-a-real-id-0000" not in ids
            assert len(ids) == 1

    def test_ws_player_join_without_id_still_works(self, ws_client: TestClient):
        """Existing clients that don't send player_id keep working."""
        session_id = create_test_session(ws_client)
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
            ws.receive_json()
            ws.send_json({
                "type": "player_join",
                "name": "Cara",
                "character_id": None,
            })
            update = ws.receive_json()
            assert update["type"] == "player_update"
            assert update["players"][0]["name"] == "Cara"


class TestDiceRoll:
    """`dice_roll` is broadcast to all connections in the session."""

    def test_ws_dice_roll_broadcasts(self, ws_client: TestClient):
        session_id = create_test_session(ws_client)
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws1:
            ws1.receive_json()  # player_joined
            with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws2:
                ws1.receive_json()  # second connection's player_joined
                ws2.receive_json()  # ws2's own player_joined

                ws1.send_json({
                    "type": "dice_roll",
                    "character_id": "char1",
                    "notation": "1d20+3",
                    "result": 17,
                    "breakdown": "14 + 3",
                    "purpose": "perception",
                })

                msg1 = ws1.receive_json()
                msg2 = ws2.receive_json()

                for msg in (msg1, msg2):
                    assert msg["type"] == "dice_roll"
                    assert msg["notation"] == "1d20+3"
                    assert msg["result"] == 17
                    assert msg["breakdown"] == "14 + 3"
                    assert msg["purpose"] == "perception"
                    assert msg["character_id"] == "char1"
                    assert "timestamp" in msg

    def test_ws_dice_roll_tolerates_missing_optional_fields(self, ws_client: TestClient):
        session_id = create_test_session(ws_client)
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
            ws.receive_json()
            ws.send_json({"type": "dice_roll", "notation": "1d6"})
            msg = ws.receive_json()
            assert msg["type"] == "dice_roll"
            assert msg["notation"] == "1d6"
            assert msg.get("result") is None
