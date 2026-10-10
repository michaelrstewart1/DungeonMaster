"""Combat turn recovery: ownership, rejoin rebind, and initiative rolls.

Playtest batch 2026-10-06:
- a typed attack or initiative roll on the current actor must get a reply
  without leaving the table waiting on the language model
- the typed path and the button path reject a seat that does not own the actor
- a new socket with the same name rebinds to the claimed character
"""
from starlette.testclient import TestClient

from tests.integration.test_ws_game import reset_storage_for_ws, ws_client  # noqa: F401


def _hero_session(client: TestClient) -> tuple[str, str]:
    char = client.post(
        "/api/characters",
        json={
            "name": "Kael Shadowstep",
            "race": "human",
            "class_name": "ranger",
            "level": 3,
            "strength": 12,
            "dexterity": 16,
            "constitution": 14,
            "intelligence": 10,
            "wisdom": 12,
            "charisma": 10,
            "max_hp": 24,
            "ac": 15,
        },
    )
    assert char.status_code == 201, char.text
    char_id = char.json()["id"]
    camp = client.post(
        "/api/campaigns",
        json={
            "name": "Playtest",
            "description": "ownership",
            "character_ids": [char_id],
            "world_state": {},
            "dm_settings": {},
        },
    )
    assert camp.status_code == 201, camp.text
    sess = client.post("/api/game/sessions", json={"campaign_id": camp.json()["id"]})
    assert sess.status_code == 201, sess.text
    return sess.json()["id"], char_id


def _recv_type(ws, expected: str, limit: int = 8) -> dict:
    last = None
    for _ in range(limit):
        last = ws.receive_json()
        if last.get("type") == expected:
            return last
    raise AssertionError(f"never received {expected}; last={last}")


def test_rejoin_socket_rebinds_same_name_to_character(ws_client: TestClient):
    session_id, char_id = _hero_session(ws_client)
    code = ws_client.get(f"/api/game/sessions/{session_id}/room-code").json()["room_code"]
    dain = ws_client.post("/api/game/join", json={"room_code": code, "player_name": "Dain"}).json()
    claim = ws_client.post(
        f"/api/game/sessions/{session_id}/select-character",
        json={"player_id": dain["player_id"], "character_id": char_id},
    )
    assert claim.status_code == 200, claim.text

    with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
        ws.receive_json()  # player_joined for this socket
        # New connection id, same name, character omitted — the seat must stick.
        ws.send_json({"type": "player_join", "name": "Dain", "player_id": "fresh-socket"})
        update = _recv_type(ws, "player_update")
        players = update["players"]
        assert len(players) == 1
        assert players[0]["id"] == dain["player_id"]
        assert players[0]["character_id"] == char_id


def test_typed_attack_resolves_for_owner_and_rejects_stranger(ws_client: TestClient):
    session_id, char_id = _hero_session(ws_client)
    started = ws_client.post(
        f"/api/game/sessions/{session_id}/start-combat",
        json={"enemies": [{"name": "Hostile Creature", "hp": 40, "ac": 10, "cr": 0.25, "count": 1}]},
    )
    assert started.status_code == 200, started.text
    before = started.json()["combat_state"]["current_turn_index"]

    code = ws_client.get(f"/api/game/sessions/{session_id}/room-code").json()["room_code"]
    dain = ws_client.post("/api/game/join", json={"room_code": code, "player_name": "Dain"}).json()
    lyra = ws_client.post("/api/game/join", json={"room_code": code, "player_name": "Lyra"}).json()
    assert ws_client.post(
        f"/api/game/sessions/{session_id}/select-character",
        json={"player_id": dain["player_id"], "character_id": char_id},
    ).status_code == 200

    with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
        ws.receive_json()
        ws.send_json({
            "type": "player_join",
            "name": "Lyra",
            "player_id": lyra["player_id"],
        })
        _recv_type(ws, "player_update")
        ws.send_json({
            "type": "action",
            "character_id": char_id,
            "player_id": lyra["player_id"],
            "action": "Lyra attacks the leader.",
        })
        denied = _recv_type(ws, "error")
        assert denied["message"] == "That isn't your character"

        state = ws_client.get(f"/api/game/sessions/{session_id}/state").json()
        assert state["combat_state"]["current_turn_index"] == before

    with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
        ws.receive_json()
        ws.send_json({
            "type": "player_join",
            "name": "Dain",
            "player_id": dain["player_id"],
            "character_id": char_id,
        })
        _recv_type(ws, "player_update")
        ws.send_json({
            "type": "action",
            "character_id": char_id,
            "player_id": dain["player_id"],
            "action": "Kael fires his shortbow at the tall robed leader.",
        })
        resolved = _recv_type(ws, "combat_update")
        assert resolved["events"]
        assert resolved.get("error") in (None, "")


def test_initiative_roll_gets_an_immediate_reply_and_does_not_change_order(ws_client: TestClient):
    session_id, char_id = _hero_session(ws_client)
    started = ws_client.post(
        f"/api/game/sessions/{session_id}/start-combat",
        json={"enemies": [{"name": "Hostile Creature", "hp": 40, "ac": 12, "cr": 0.25, "count": 1}]},
    )
    assert started.status_code == 200, started.text
    cs = started.json()["combat_state"]
    order = list(cs["initiative_order"])
    index = cs["current_turn_index"]
    totals = [c["initiative"] for c in cs["combatants"]]

    with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
        ws.receive_json()
        ws.send_json({
            "type": "action",
            "character_id": char_id,
            "action": "🎲 Kael Shadowstep rolls d20: 15",
        })
        reply = _recv_type(ws, "turn_result")
        narration = reply["narration"]
        assert "does not change the turn order" in narration
        assert "roll for initiative" not in narration.lower()
        for total in totals:
            assert str(total) in narration

    after = ws_client.get(f"/api/game/sessions/{session_id}/state").json()["combat_state"]
    assert after["initiative_order"] == order
    assert after["current_turn_index"] == index
    assert [c["initiative"] for c in after["combatants"]] == totals
