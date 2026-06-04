"""Integration tests for player-to-player trading."""
import asyncio

import pytest
from starlette.testclient import TestClient

from tests.integration.test_ws_game import ws_client, reset_storage_for_ws, create_test_session  # noqa: F401


def _make_character(client: TestClient, name: str, items: list[dict]) -> str:
    """Create a character with a pre-populated structured_inventory."""
    payload = {
        "name": name,
        "race": "human",
        "class_name": "fighter",
        "level": 1,
        "strength": 10,
        "dexterity": 10,
        "constitution": 10,
        "intelligence": 10,
        "wisdom": 10,
        "charisma": 10,
        "hp": 10,
        "max_hp": 10,
        "ac": 10,
        "speed": 30,
        "experience_points": 0,
        "structured_inventory": items,
    }
    r = client.post("/api/characters", json=payload)
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _join_two_players(client: TestClient, session_id: str, char_a: str, char_b: str):
    """Open two WS connections + perform player_join for two players. Returns
    (ws1, ws2, player_id_a, player_id_b)."""
    rc = client.get(f"/api/game/sessions/{session_id}/room-code").json()["room_code"]
    a = client.post("/api/game/join", json={"room_code": rc, "player_name": "Alice", "character_id": char_a}).json()
    b = client.post("/api/game/join", json={"room_code": rc, "player_name": "Bob", "character_id": char_b}).json()
    return rc, a["player_id"], b["player_id"]


class TestTradeCreate:
    def test_create_trade_delivers_offer_to_recipient_over_ws(self, ws_client: TestClient):
        session_id = create_test_session(ws_client)
        ca = _make_character(ws_client, "Alice-PC", [
            {"id": "i1", "name": "Healing Potion", "quantity": 2, "rarity": "common", "item_type": "potion", "description": ""},
        ])
        cb = _make_character(ws_client, "Bob-PC", [])
        _, pid_a, pid_b = _join_two_players(ws_client, session_id, ca, cb)

        with ws_client.websocket_connect(f"/ws/game/{session_id}") as wsA:
            wsA.receive_json()  # initial player_joined for A
            wsA.send_json({"type": "player_join", "name": "Alice", "player_id": pid_a, "character_id": ca})
            wsA.receive_json()  # player_update

            with ws_client.websocket_connect(f"/ws/game/{session_id}") as wsB:
                wsA.receive_json()  # B's connect player_joined arrives at A
                wsB.receive_json()  # B's own player_joined
                wsB.send_json({"type": "player_join", "name": "Bob", "player_id": pid_b, "character_id": cb})
                # both A and B receive player_update
                wsA.receive_json()
                wsB.receive_json()

                # A creates a trade offer to B
                resp = ws_client.post(
                    f"/api/game/sessions/{session_id}/trades",
                    json={
                        "from_player_id": pid_a,
                        "from_character_id": ca,
                        "to_player_id": pid_b,
                        "to_character_id": cb,
                        "offered_items": [{"item_id": "i1", "quantity": 1}],
                    },
                )
                assert resp.status_code == 201, resp.text
                body = resp.json()
                assert body["delivered"] is True
                trade = body["trade"]
                assert trade["status"] == "pending"
                assert trade["offered_items"][0]["name"] == "Healing Potion"

                # B should receive the trade_offer privately; A should not.
                msg = wsB.receive_json()
                assert msg["type"] == "trade_offer"
                assert msg["trade"]["id"] == trade["id"]
                # A should not have received it (drain with short timeout would be tricky
                # in TestClient; relying on private send semantics + the receive above
                # not blocking gives us reasonable confidence).

    def test_create_trade_rejects_self_trade(self, ws_client: TestClient):
        session_id = create_test_session(ws_client)
        ca = _make_character(ws_client, "Alice-PC", [
            {"id": "i1", "name": "Sword", "quantity": 1, "rarity": "common", "item_type": "weapon", "description": ""},
        ])
        _, pid_a, _ = _join_two_players(ws_client, session_id, ca, ca)
        r = ws_client.post(
            f"/api/game/sessions/{session_id}/trades",
            json={
                "from_player_id": pid_a,
                "from_character_id": ca,
                "to_player_id": pid_a,
                "offered_items": [{"item_id": "i1", "quantity": 1}],
            },
        )
        assert r.status_code == 400

    def test_create_trade_rejects_empty_offer(self, ws_client: TestClient):
        session_id = create_test_session(ws_client)
        ca = _make_character(ws_client, "Alice-PC", [])
        cb = _make_character(ws_client, "Bob-PC", [])
        _, pid_a, pid_b = _join_two_players(ws_client, session_id, ca, cb)
        r = ws_client.post(
            f"/api/game/sessions/{session_id}/trades",
            json={
                "from_player_id": pid_a,
                "from_character_id": ca,
                "to_player_id": pid_b,
                "to_character_id": cb,
            },
        )
        assert r.status_code == 400

    def test_create_trade_rejects_missing_item(self, ws_client: TestClient):
        session_id = create_test_session(ws_client)
        ca = _make_character(ws_client, "Alice-PC", [])
        cb = _make_character(ws_client, "Bob-PC", [])
        _, pid_a, pid_b = _join_two_players(ws_client, session_id, ca, cb)
        r = ws_client.post(
            f"/api/game/sessions/{session_id}/trades",
            json={
                "from_player_id": pid_a,
                "from_character_id": ca,
                "to_player_id": pid_b,
                "to_character_id": cb,
                "offered_items": [{"item_id": "ghost", "quantity": 1}],
            },
        )
        assert r.status_code == 400


class TestTradeRespond:
    def _create_and_open(self, ws_client: TestClient):
        session_id = create_test_session(ws_client)
        ca = _make_character(ws_client, "Alice-PC", [
            {"id": "i1", "name": "Healing Potion", "quantity": 2, "rarity": "common", "item_type": "potion", "description": ""},
        ])
        cb = _make_character(ws_client, "Bob-PC", [
            {"id": "i2", "name": "Rope", "quantity": 1, "rarity": "common", "item_type": "misc", "description": ""},
        ])
        _, pid_a, pid_b = _join_two_players(ws_client, session_id, ca, cb)
        return session_id, ca, cb, pid_a, pid_b

    def test_accept_moves_items_between_inventories(self, ws_client: TestClient):
        session_id, ca, cb, pid_a, pid_b = self._create_and_open(ws_client)
        # No WS open — backend should still process accept and broadcast (no-op delivery).
        trade = ws_client.post(
            f"/api/game/sessions/{session_id}/trades",
            json={
                "from_player_id": pid_a,
                "from_character_id": ca,
                "to_player_id": pid_b,
                "to_character_id": cb,
                "offered_items": [{"item_id": "i1", "quantity": 1}],
                "requested_items": [{"item_id": "i2", "quantity": 1}],
            },
        ).json()["trade"]

        r = ws_client.post(
            f"/api/game/sessions/{session_id}/trades/{trade['id']}/respond",
            json={"action": "accept", "player_id": pid_b},
        )
        assert r.status_code == 200, r.text
        assert r.json()["trade"]["status"] == "accepted"

        # Verify inventories changed
        ca_after = ws_client.get(f"/api/characters/{ca}").json()
        cb_after = ws_client.get(f"/api/characters/{cb}").json()
        names_a = [i["name"] for i in ca_after.get("structured_inventory", [])]
        names_b = [i["name"] for i in cb_after.get("structured_inventory", [])]
        assert "Rope" in names_a
        assert "Healing Potion" in names_b
        # Alice had 2 potions, gave 1, kept 1
        potions_a = [i for i in ca_after["structured_inventory"] if i["name"] == "Healing Potion"]
        assert sum(int(i["quantity"]) for i in potions_a) == 1

    def test_decline_does_not_change_inventories(self, ws_client: TestClient):
        session_id, ca, cb, pid_a, pid_b = self._create_and_open(ws_client)
        trade = ws_client.post(
            f"/api/game/sessions/{session_id}/trades",
            json={
                "from_player_id": pid_a,
                "from_character_id": ca,
                "to_player_id": pid_b,
                "to_character_id": cb,
                "offered_items": [{"item_id": "i1", "quantity": 1}],
            },
        ).json()["trade"]

        ws_client.post(
            f"/api/game/sessions/{session_id}/trades/{trade['id']}/respond",
            json={"action": "decline", "player_id": pid_b},
        )
        ca_after = ws_client.get(f"/api/characters/{ca}").json()
        # Alice still has 2 potions
        potions = sum(int(i["quantity"]) for i in ca_after.get("structured_inventory", []) if i["name"] == "Healing Potion")
        assert potions == 2

    def test_only_recipient_can_accept(self, ws_client: TestClient):
        session_id, ca, cb, pid_a, pid_b = self._create_and_open(ws_client)
        trade = ws_client.post(
            f"/api/game/sessions/{session_id}/trades",
            json={
                "from_player_id": pid_a,
                "from_character_id": ca,
                "to_player_id": pid_b,
                "to_character_id": cb,
                "offered_items": [{"item_id": "i1", "quantity": 1}],
            },
        ).json()["trade"]
        r = ws_client.post(
            f"/api/game/sessions/{session_id}/trades/{trade['id']}/respond",
            json={"action": "accept", "player_id": pid_a},
        )
        assert r.status_code == 403

    def test_double_accept_returns_409(self, ws_client: TestClient):
        session_id, ca, cb, pid_a, pid_b = self._create_and_open(ws_client)
        trade = ws_client.post(
            f"/api/game/sessions/{session_id}/trades",
            json={
                "from_player_id": pid_a,
                "from_character_id": ca,
                "to_player_id": pid_b,
                "to_character_id": cb,
                "offered_items": [{"item_id": "i1", "quantity": 1}],
            },
        ).json()["trade"]
        ws_client.post(
            f"/api/game/sessions/{session_id}/trades/{trade['id']}/respond",
            json={"action": "accept", "player_id": pid_b},
        )
        r = ws_client.post(
            f"/api/game/sessions/{session_id}/trades/{trade['id']}/respond",
            json={"action": "accept", "player_id": pid_b},
        )
        assert r.status_code == 409

    def test_cancel_by_initiator_works(self, ws_client: TestClient):
        session_id, ca, cb, pid_a, pid_b = self._create_and_open(ws_client)
        trade = ws_client.post(
            f"/api/game/sessions/{session_id}/trades",
            json={
                "from_player_id": pid_a,
                "from_character_id": ca,
                "to_player_id": pid_b,
                "to_character_id": cb,
                "offered_items": [{"item_id": "i1", "quantity": 1}],
            },
        ).json()["trade"]
        r = ws_client.post(
            f"/api/game/sessions/{session_id}/trades/{trade['id']}/cancel",
            json={"player_id": pid_a},
        )
        assert r.status_code == 200
        assert r.json()["trade"]["status"] == "cancelled"

    def test_list_trades_filters_by_player(self, ws_client: TestClient):
        session_id, ca, cb, pid_a, pid_b = self._create_and_open(ws_client)
        ws_client.post(
            f"/api/game/sessions/{session_id}/trades",
            json={
                "from_player_id": pid_a,
                "from_character_id": ca,
                "to_player_id": pid_b,
                "to_character_id": cb,
                "offered_items": [{"item_id": "i1", "quantity": 1}],
            },
        )
        r = ws_client.get(f"/api/game/sessions/{session_id}/trades?player_id={pid_b}")
        assert r.status_code == 200
        assert len(r.json()["trades"]) == 1
