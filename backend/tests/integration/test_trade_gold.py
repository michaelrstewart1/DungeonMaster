"""Phase B trade-extension tests: gold transfer in trades."""
import pytest
from starlette.testclient import TestClient

from tests.integration.test_ws_game import ws_client, reset_storage_for_ws, create_test_session  # noqa: F401
from tests.integration.test_trade import _make_character, _join_two_players


def _make_character_with_gold(client: TestClient, name: str, items: list, gold: int) -> str:
    payload = {
        "name": name,
        "race": "human",
        "class_name": "fighter",
        "level": 1,
        "strength": 10, "dexterity": 10, "constitution": 10,
        "intelligence": 10, "wisdom": 10, "charisma": 10,
        "hp": 10, "max_hp": 10, "ac": 10, "speed": 30,
        "experience_points": 0,
        "gold": gold,
        "structured_inventory": items,
    }
    r = client.post("/api/characters", json=payload)
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _open_session_with_two_players(ws_client: TestClient, ca: str, cb: str):
    session_id = create_test_session(ws_client)
    _, pid_a, pid_b = _join_two_players(ws_client, session_id, ca, cb)
    return session_id, pid_a, pid_b


def _create_and_accept(ws_client, session_id, pid_a, ca, pid_b, cb, body_extra):
    """Helper: create trade and immediately accept it."""
    resp = ws_client.post(
        f"/api/game/sessions/{session_id}/trades",
        json={
            "from_player_id": pid_a, "from_character_id": ca,
            "to_player_id": pid_b, "to_character_id": cb,
            **body_extra,
        },
    )
    assert resp.status_code == 201, resp.text
    tid = resp.json()["trade"]["id"]
    accept = ws_client.post(
        f"/api/game/sessions/{session_id}/trades/{tid}/respond",
        json={"action": "accept", "player_id": pid_b},
    )
    return accept


class TestTradeGold:
    def test_gold_only_trade_transfers(self, ws_client: TestClient):
        ca = _make_character_with_gold(ws_client, "Alice", [], 100)
        cb = _make_character_with_gold(ws_client, "Bob", [], 0)
        session_id, pid_a, pid_b = _open_session_with_two_players(ws_client, ca, cb)
        r = _create_and_accept(ws_client, session_id, pid_a, ca, pid_b, cb, {"offered_gold": 40})
        assert r.status_code == 200, r.text
        assert ws_client.get(f"/api/characters/{ca}").json()["gold"] == 60
        assert ws_client.get(f"/api/characters/{cb}").json()["gold"] == 40

    def test_mutual_gold_swap(self, ws_client: TestClient):
        ca = _make_character_with_gold(ws_client, "Alice", [], 50)
        cb = _make_character_with_gold(ws_client, "Bob", [], 30)
        session_id, pid_a, pid_b = _open_session_with_two_players(ws_client, ca, cb)
        r = _create_and_accept(
            ws_client, session_id, pid_a, ca, pid_b, cb,
            {"offered_gold": 20, "requested_gold": 10},
        )
        assert r.status_code == 200
        assert ws_client.get(f"/api/characters/{ca}").json()["gold"] == 40  # -20 +10
        assert ws_client.get(f"/api/characters/{cb}").json()["gold"] == 40  # -10 +20

    def test_items_plus_gold_trade(self, ws_client: TestClient):
        ca = _make_character_with_gold(ws_client, "Alice", [
            {"id": "p1", "name": "Healing Potion", "quantity": 2, "rarity": "common", "item_type": "potion"},
        ], 10)
        cb = _make_character_with_gold(ws_client, "Bob", [], 50)
        session_id, pid_a, pid_b = _open_session_with_two_players(ws_client, ca, cb)
        r = _create_and_accept(
            ws_client, session_id, pid_a, ca, pid_b, cb,
            {"offered_items": [{"item_id": "p1", "quantity": 1}], "requested_gold": 30},
        )
        assert r.status_code == 200, r.text
        alice = ws_client.get(f"/api/characters/{ca}").json()
        bob = ws_client.get(f"/api/characters/{cb}").json()
        assert alice["gold"] == 40
        assert bob["gold"] == 20
        # Alice has 1 potion left, Bob now has 1 potion
        a_potions = [i for i in alice["structured_inventory"] if i["name"] == "Healing Potion"]
        b_potions = [i for i in bob["structured_inventory"] if i["name"] == "Healing Potion"]
        assert sum(i["quantity"] for i in a_potions) == 1
        assert sum(i["quantity"] for i in b_potions) == 1

    def test_insufficient_sender_gold_rejected_at_create(self, ws_client: TestClient):
        ca = _make_character_with_gold(ws_client, "Alice", [], 5)
        cb = _make_character_with_gold(ws_client, "Bob", [], 0)
        session_id, pid_a, pid_b = _open_session_with_two_players(ws_client, ca, cb)
        resp = ws_client.post(
            f"/api/game/sessions/{session_id}/trades",
            json={
                "from_player_id": pid_a, "from_character_id": ca,
                "to_player_id": pid_b, "to_character_id": cb,
                "offered_gold": 50,
            },
        )
        assert resp.status_code == 400
        assert "5 gp" in resp.json()["detail"]

    def test_insufficient_recipient_gold_rejected_at_create(self, ws_client: TestClient):
        ca = _make_character_with_gold(ws_client, "Alice", [], 0)
        cb = _make_character_with_gold(ws_client, "Bob", [], 5)
        session_id, pid_a, pid_b = _open_session_with_two_players(ws_client, ca, cb)
        resp = ws_client.post(
            f"/api/game/sessions/{session_id}/trades",
            json={
                "from_player_id": pid_a, "from_character_id": ca,
                "to_player_id": pid_b, "to_character_id": cb,
                "requested_gold": 100,
            },
        )
        assert resp.status_code == 400
        assert "5 gp" in resp.json()["detail"]

    def test_recipient_spent_gold_before_accept_409(self, ws_client: TestClient):
        ca = _make_character_with_gold(ws_client, "Alice", [], 0)
        cb = _make_character_with_gold(ws_client, "Bob", [], 50)
        session_id, pid_a, pid_b = _open_session_with_two_players(ws_client, ca, cb)
        # Create offer requesting 40 gp from Bob
        resp = ws_client.post(
            f"/api/game/sessions/{session_id}/trades",
            json={
                "from_player_id": pid_a, "from_character_id": ca,
                "to_player_id": pid_b, "to_character_id": cb,
                "requested_gold": 40,
            },
        )
        assert resp.status_code == 201
        tid = resp.json()["trade"]["id"]
        # Bob spends gold elsewhere before accepting
        ws_client.post(f"/api/characters/{cb}/gold", json={"amount": -45})
        accept = ws_client.post(
            f"/api/game/sessions/{session_id}/trades/{tid}/respond",
            json={"action": "accept", "player_id": pid_b},
        )
        assert accept.status_code == 409
        # Trade still pending so Bob could decline / cancel; gold unchanged
        assert ws_client.get(f"/api/characters/{cb}").json()["gold"] == 5
        assert ws_client.get(f"/api/characters/{ca}").json()["gold"] == 0
