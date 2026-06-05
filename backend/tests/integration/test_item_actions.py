"""Phase C trade-extension tests: item use / equip / unequip."""
import pytest
from starlette.testclient import TestClient

from tests.integration.test_ws_game import ws_client, reset_storage_for_ws, create_test_session  # noqa: F401
from tests.integration.test_trade import _make_character, _join_two_players


def _make_char_full(client: TestClient, name: str, items: list, hp: int = 5, max_hp: int = 20) -> str:
    payload = {
        "name": name,
        "race": "human", "class_name": "fighter", "level": 1,
        "strength": 10, "dexterity": 10, "constitution": 10,
        "intelligence": 10, "wisdom": 10, "charisma": 10,
        "hp": hp, "max_hp": max_hp, "ac": 10, "speed": 30,
        "experience_points": 0,
        "structured_inventory": items,
    }
    r = client.post("/api/characters", json=payload)
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _session_with(ws_client, items_a=None, items_b=None, hp_a=5, max_hp_a=20):
    ca = _make_char_full(ws_client, "Alice", items_a or [], hp=hp_a, max_hp=max_hp_a)
    cb = _make_char_full(ws_client, "Bob", items_b or [])
    session_id = create_test_session(ws_client)
    _, pid_a, pid_b = _join_two_players(ws_client, session_id, ca, cb)
    return session_id, pid_a, pid_b, ca, cb


class TestItemUse:
    def test_use_healing_potion_heals_and_consumes_stack_of_one(self, ws_client: TestClient):
        sid, pid_a, _, ca, _ = _session_with(ws_client, items_a=[
            {"id": "p1", "name": "Healing Potion", "quantity": 1, "rarity": "common", "item_type": "potion",
             "effect": {"type": "heal", "value": 10}},
        ], hp_a=3, max_hp_a=20)
        r = ws_client.post(
            f"/api/game/sessions/{sid}/characters/{ca}/items/p1/use",
            json={"player_id": pid_a},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["consumed"] is True
        assert body["hp_after"] == 13
        char = ws_client.get(f"/api/characters/{ca}").json()
        assert char["hp"] == 13
        assert all(i.get("id") != "p1" for i in char["structured_inventory"])

    def test_use_heals_cap_at_max_hp(self, ws_client: TestClient):
        sid, pid_a, _, ca, _ = _session_with(ws_client, items_a=[
            {"id": "p1", "name": "Greater Healing", "quantity": 1, "item_type": "potion",
             "effect": {"type": "heal", "value": 500}},
        ], hp_a=10, max_hp_a=15)
        r = ws_client.post(
            f"/api/game/sessions/{sid}/characters/{ca}/items/p1/use",
            json={"player_id": pid_a},
        )
        assert r.status_code == 200
        assert r.json()["hp_after"] == 15

    def test_use_decrements_stack(self, ws_client: TestClient):
        sid, pid_a, _, ca, _ = _session_with(ws_client, items_a=[
            {"id": "p1", "name": "Healing Potion", "quantity": 3, "item_type": "potion",
             "effect": {"type": "heal", "value": 5}},
        ])
        r = ws_client.post(
            f"/api/game/sessions/{sid}/characters/{ca}/items/p1/use",
            json={"player_id": pid_a},
        )
        assert r.status_code == 200
        assert r.json()["consumed"] is False
        char = ws_client.get(f"/api/characters/{ca}").json()
        p = next(i for i in char["structured_inventory"] if i["id"] == "p1")
        assert p["quantity"] == 2

    def test_use_item_without_effect_just_decrements(self, ws_client: TestClient):
        sid, pid_a, _, ca, _ = _session_with(ws_client, items_a=[
            {"id": "x1", "name": "Trinket", "quantity": 2, "item_type": "misc"},
        ])
        r = ws_client.post(
            f"/api/game/sessions/{sid}/characters/{ca}/items/x1/use",
            json={"player_id": pid_a},
        )
        assert r.status_code == 200
        assert r.json()["effect_summary"] is None

    def test_use_other_players_character_403(self, ws_client: TestClient):
        sid, _, pid_b, ca, _ = _session_with(ws_client, items_a=[
            {"id": "p1", "name": "Potion", "quantity": 1, "item_type": "potion"},
        ])
        r = ws_client.post(
            f"/api/game/sessions/{sid}/characters/{ca}/items/p1/use",
            json={"player_id": pid_b},
        )
        assert r.status_code == 403

    def test_use_missing_item_404(self, ws_client: TestClient):
        sid, pid_a, _, ca, _ = _session_with(ws_client, items_a=[])
        r = ws_client.post(
            f"/api/game/sessions/{sid}/characters/{ca}/items/none/use",
            json={"player_id": pid_a},
        )
        assert r.status_code == 404


class TestItemEquip:
    def test_equip_weapon_then_unequip(self, ws_client: TestClient):
        sid, pid_a, _, ca, _ = _session_with(ws_client, items_a=[
            {"id": "s1", "name": "Longsword", "quantity": 1, "item_type": "weapon"},
        ])
        r = ws_client.post(
            f"/api/game/sessions/{sid}/characters/{ca}/items/s1/equip",
            json={"player_id": pid_a},
        )
        assert r.status_code == 200
        char = ws_client.get(f"/api/characters/{ca}").json()
        assert next(i for i in char["structured_inventory"] if i["id"] == "s1")["equipped"] is True

        r2 = ws_client.post(
            f"/api/game/sessions/{sid}/characters/{ca}/items/s1/unequip",
            json={"player_id": pid_a},
        )
        assert r2.status_code == 200
        char = ws_client.get(f"/api/characters/{ca}").json()
        assert next(i for i in char["structured_inventory"] if i["id"] == "s1")["equipped"] is False

    def test_cannot_equip_potion(self, ws_client: TestClient):
        sid, pid_a, _, ca, _ = _session_with(ws_client, items_a=[
            {"id": "p1", "name": "Potion", "quantity": 1, "item_type": "potion"},
        ])
        r = ws_client.post(
            f"/api/game/sessions/{sid}/characters/{ca}/items/p1/equip",
            json={"player_id": pid_a},
        )
        assert r.status_code == 400


class TestItemUseBroadcast:
    def test_item_used_event_broadcast_to_session(self, ws_client: TestClient):
        sid, pid_a, pid_b, ca, cb = _session_with(ws_client, items_a=[
            {"id": "p1", "name": "Healing Potion", "quantity": 1, "item_type": "potion",
             "effect": {"type": "heal", "value": 4}},
        ])
        with ws_client.websocket_connect(f"/ws/game/{sid}") as wsA:
            wsA.receive_json()
            wsA.send_json({"type": "player_join", "name": "Alice", "player_id": pid_a, "character_id": ca})
            wsA.receive_json()
            with ws_client.websocket_connect(f"/ws/game/{sid}") as wsB:
                wsA.receive_json()  # B joined notice
                wsB.receive_json()
                wsB.send_json({"type": "player_join", "name": "Bob", "player_id": pid_b, "character_id": cb})
                wsA.receive_json()
                wsB.receive_json()

                r = ws_client.post(
                    f"/api/game/sessions/{sid}/characters/{ca}/items/p1/use",
                    json={"player_id": pid_a},
                )
                assert r.status_code == 200
                # Both connections should receive item_used
                msgA = wsA.receive_json()
                msgB = wsB.receive_json()
                assert msgA["type"] == "item_used"
                assert msgB["type"] == "item_used"
                assert msgB["character_name"] == "Alice"
                assert msgB["item_name"] == "Healing Potion"
