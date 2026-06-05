"""Phase E trade-extension tests: DM arbitration (veto + observability)."""
import pytest
from starlette.testclient import TestClient

from tests.integration.test_ws_game import ws_client, reset_storage_for_ws, create_test_session  # noqa: F401
from tests.integration.test_trade import _make_character, _join_two_players


def _bootstrap(ws_client, items_a=None, items_b=None):
    ca = _make_character(ws_client, "Alice", items_a or [])
    cb = _make_character(ws_client, "Bob", items_b or [])
    sid = create_test_session(ws_client)
    _, pid_a, pid_b = _join_two_players(ws_client, sid, ca, cb)
    return sid, pid_a, pid_b, ca, cb


class TestTradeVeto:
    def test_veto_marks_trade_vetoed(self, ws_client: TestClient):
        sid, pid_a, pid_b, ca, cb = _bootstrap(
            ws_client, [{"id": "a1", "name": "Sword", "quantity": 1, "item_type": "weapon"}], [],
        )
        offer = ws_client.post(
            f"/api/game/sessions/{sid}/trades",
            json={
                "from_player_id": pid_a, "from_character_id": ca,
                "to_player_id": pid_b, "to_character_id": cb,
                "offered_items": [{"item_id": "a1", "quantity": 1}],
            },
        ).json()["trade"]
        r = ws_client.post(
            f"/api/game/sessions/{sid}/trades/{offer['id']}/veto",
            json={"reason": "That breaks the encounter balance"},
        )
        assert r.status_code == 200
        body = r.json()["trade"]
        assert body["status"] == "vetoed"
        assert "balance" in body["note"]

    def test_cannot_veto_resolved_trade(self, ws_client: TestClient):
        sid, pid_a, pid_b, ca, cb = _bootstrap(
            ws_client, [{"id": "a1", "name": "X", "quantity": 1}], [],
        )
        offer = ws_client.post(
            f"/api/game/sessions/{sid}/trades",
            json={
                "from_player_id": pid_a, "from_character_id": ca,
                "to_player_id": pid_b, "to_character_id": cb,
                "offered_items": [{"item_id": "a1", "quantity": 1}],
            },
        ).json()["trade"]
        ws_client.post(
            f"/api/game/sessions/{sid}/trades/{offer['id']}/respond",
            json={"action": "decline", "player_id": pid_b},
        )
        r = ws_client.post(
            f"/api/game/sessions/{sid}/trades/{offer['id']}/veto",
            json={"reason": "too late"},
        )
        assert r.status_code == 409

    def test_veto_broadcasts_trade_resolved(self, ws_client: TestClient):
        sid, pid_a, pid_b, ca, cb = _bootstrap(
            ws_client, [{"id": "a1", "name": "X", "quantity": 1}], [],
        )
        with ws_client.websocket_connect(f"/ws/game/{sid}") as wsA:
            wsA.receive_json()
            wsA.send_json({"type": "player_join", "name": "Alice", "player_id": pid_a, "character_id": ca})
            wsA.receive_json()
            with ws_client.websocket_connect(f"/ws/game/{sid}") as wsB:
                wsA.receive_json()
                wsB.receive_json()
                wsB.send_json({"type": "player_join", "name": "Bob", "player_id": pid_b, "character_id": cb})
                wsA.receive_json()
                wsB.receive_json()

                offer = ws_client.post(
                    f"/api/game/sessions/{sid}/trades",
                    json={
                        "from_player_id": pid_a, "from_character_id": ca,
                        "to_player_id": pid_b, "to_character_id": cb,
                        "offered_items": [{"item_id": "a1", "quantity": 1}],
                    },
                ).json()["trade"]
                # Alice (sender) sees only the broadcast; Bob (recipient) gets both private + broadcast
                a1 = wsA.receive_json()
                assert a1["type"] == "trade_offer_observed"
                msgs_b = [wsB.receive_json(), wsB.receive_json()]
                types_b = {m["type"] for m in msgs_b}
                assert "trade_offer" in types_b
                assert "trade_offer_observed" in types_b

                r = ws_client.post(
                    f"/api/game/sessions/{sid}/trades/{offer['id']}/veto",
                    json={"reason": "Too OP"},
                )
                assert r.status_code == 200
                a_msg = wsA.receive_json()
                b_msg = wsB.receive_json()
                assert a_msg["type"] == "trade_resolved"
                assert a_msg["trade"]["status"] == "vetoed"
                assert b_msg["type"] == "trade_resolved"


class TestTradeObservability:
    def test_trade_offer_observed_broadcasts_to_third_party(self, ws_client: TestClient):
        """The DM (or any other connection) gets `trade_offer_observed` for
        every offer in the session."""
        sid, pid_a, pid_b, ca, cb = _bootstrap(
            ws_client, [{"id": "a1", "name": "X", "quantity": 1}], [],
        )
        with ws_client.websocket_connect(f"/ws/game/{sid}") as wsDM:
            wsDM.receive_json()  # initial player_joined
            offer_resp = ws_client.post(
                f"/api/game/sessions/{sid}/trades",
                json={
                    "from_player_id": pid_a, "from_character_id": ca,
                    "to_player_id": pid_b, "to_character_id": cb,
                    "offered_items": [{"item_id": "a1", "quantity": 1}],
                },
            )
            assert offer_resp.status_code == 201
            # DM is not a participant — should still see the broadcast event.
            msg = wsDM.receive_json()
            assert msg["type"] == "trade_offer_observed"
            assert msg["trade"]["from_player_name"] == "Alice"
            assert msg["trade"]["to_player_name"] == "Bob"
