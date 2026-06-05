"""Phase D trade-extension tests: counter-offers."""
import pytest
from starlette.testclient import TestClient

from tests.integration.test_ws_game import ws_client, reset_storage_for_ws, create_test_session  # noqa: F401
from tests.integration.test_trade import _make_character, _join_two_players


def _bootstrap(ws_client: TestClient, items_a: list, items_b: list):
    ca = _make_character(ws_client, "Alice", items_a)
    cb = _make_character(ws_client, "Bob", items_b)
    sid = create_test_session(ws_client)
    _, pid_a, pid_b = _join_two_players(ws_client, sid, ca, cb)
    return sid, pid_a, pid_b, ca, cb


def _create_offer(ws_client, sid, pid_a, ca, pid_b, cb, **extra):
    r = ws_client.post(
        f"/api/game/sessions/{sid}/trades",
        json={
            "from_player_id": pid_a, "from_character_id": ca,
            "to_player_id": pid_b, "to_character_id": cb,
            **extra,
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["trade"]


class TestTradeCounter:
    def test_counter_creates_new_trade_with_swapped_roles(self, ws_client: TestClient):
        sid, pid_a, pid_b, ca, cb = _bootstrap(
            ws_client,
            [{"id": "a1", "name": "Sword", "quantity": 1, "item_type": "weapon"}],
            [{"id": "b1", "name": "Bow", "quantity": 1, "item_type": "weapon"}],
        )
        original = _create_offer(
            ws_client, sid, pid_a, ca, pid_b, cb,
            offered_items=[{"item_id": "a1", "quantity": 1}],
            requested_items=[{"item_id": "b1", "quantity": 1}],
        )
        # Bob counters: offers his bow but requests sword + 5 gp later
        r = ws_client.post(
            f"/api/game/sessions/{sid}/trades/{original['id']}/counter",
            json={
                "player_id": pid_b,
                "offered_items": [{"item_id": "b1", "quantity": 1}],
                "requested_items": [{"item_id": "a1", "quantity": 1}],
                "note": "How about an even swap?",
            },
        )
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["original"]["status"] == "countered"
        new_t = body["trade"]
        assert new_t["from_player_id"] == pid_b
        assert new_t["to_player_id"] == pid_a
        assert new_t["counter_of"] == original["id"]
        assert new_t["status"] == "pending"

    def test_only_recipient_can_counter(self, ws_client: TestClient):
        sid, pid_a, pid_b, ca, cb = _bootstrap(
            ws_client,
            [{"id": "a1", "name": "X", "quantity": 1}],
            [],
        )
        original = _create_offer(
            ws_client, sid, pid_a, ca, pid_b, cb,
            offered_items=[{"item_id": "a1", "quantity": 1}],
        )
        r = ws_client.post(
            f"/api/game/sessions/{sid}/trades/{original['id']}/counter",
            json={"player_id": pid_a, "offered_items": [{"item_id": "a1", "quantity": 1}]},
        )
        assert r.status_code == 403

    def test_cannot_counter_resolved_trade(self, ws_client: TestClient):
        sid, pid_a, pid_b, ca, cb = _bootstrap(
            ws_client,
            [{"id": "a1", "name": "X", "quantity": 1}],
            [],
        )
        original = _create_offer(
            ws_client, sid, pid_a, ca, pid_b, cb,
            offered_items=[{"item_id": "a1", "quantity": 1}],
        )
        # Recipient declines first
        ws_client.post(
            f"/api/game/sessions/{sid}/trades/{original['id']}/respond",
            json={"action": "decline", "player_id": pid_b},
        )
        r = ws_client.post(
            f"/api/game/sessions/{sid}/trades/{original['id']}/counter",
            json={"player_id": pid_b, "offered_gold": 5},
        )
        assert r.status_code == 409

    def test_counter_chain_links(self, ws_client: TestClient):
        sid, pid_a, pid_b, ca, cb = _bootstrap(
            ws_client,
            [{"id": "a1", "name": "X", "quantity": 1}],
            [{"id": "b1", "name": "Y", "quantity": 1}],
        )
        first = _create_offer(
            ws_client, sid, pid_a, ca, pid_b, cb,
            offered_items=[{"item_id": "a1", "quantity": 1}],
        )
        # Bob counters
        r1 = ws_client.post(
            f"/api/game/sessions/{sid}/trades/{first['id']}/counter",
            json={"player_id": pid_b, "offered_items": [{"item_id": "b1", "quantity": 1}]},
        )
        assert r1.status_code == 201
        second = r1.json()["trade"]
        # Alice (now recipient) counters back
        r2 = ws_client.post(
            f"/api/game/sessions/{sid}/trades/{second['id']}/counter",
            json={"player_id": pid_a, "offered_items": [{"item_id": "a1", "quantity": 1}], "note": "fine"},
        )
        assert r2.status_code == 201
        third = r2.json()["trade"]
        assert third["counter_of"] == second["id"]
        # Whole chain resolvable: original countered, second countered, third pending
        listed = ws_client.get(f"/api/game/sessions/{sid}/trades").json()["trades"]
        by_id = {t["id"]: t for t in listed}
        assert by_id[first["id"]]["status"] == "countered"
        assert by_id[second["id"]]["status"] == "countered"
        assert by_id[third["id"]]["status"] == "pending"
