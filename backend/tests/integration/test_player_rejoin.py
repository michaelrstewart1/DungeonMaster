"""Player rejoin — refreshing a phone must not duplicate roster entries."""
import pytest


async def _make_session(client) -> dict:
    campaign = await client.post("/api/campaigns", json={"name": "Rejoin Test", "description": "x"})
    campaign_id = campaign.json()["id"]
    resp = await client.post(
        "/api/game/sessions",
        json={"campaign_id": campaign_id, "current_scene": "Camp."},
    )
    return resp.json()


@pytest.mark.asyncio
async def test_rejoin_with_player_id_reuses_entry(client):
    session = await _make_session(client)
    code = session["room_code"]

    first = await client.post("/api/game/join", json={"room_code": code, "player_name": "Kit"})
    player_id = first.json()["player_id"]
    assert first.json()["rejoined"] is False

    second = await client.post(
        "/api/game/join",
        json={"room_code": code, "player_name": "Kit", "player_id": player_id},
    )
    assert second.json()["player_id"] == player_id
    assert second.json()["rejoined"] is True

    players = await client.get(f"/api/game/sessions/{session['id']}/players")
    assert len(players.json()["players"]) == 1


@pytest.mark.asyncio
async def test_rejoin_by_name_after_identity_loss(client):
    session = await _make_session(client)
    code = session["room_code"]

    first = await client.post(
        "/api/game/join",
        json={"room_code": code, "player_name": "Brody", "character_id": "char-1"},
    )
    player_id = first.json()["player_id"]

    # Phone lost its identity entirely — same name should reclaim the seat
    second = await client.post("/api/game/join", json={"room_code": code, "player_name": "brody"})
    assert second.json()["player_id"] == player_id
    assert second.json()["rejoined"] is True
    assert second.json()["character_id"] == "char-1"  # character binding restored

    players = await client.get(f"/api/game/sessions/{session['id']}/players")
    assert len(players.json()["players"]) == 1


@pytest.mark.asyncio
async def test_distinct_names_get_distinct_entries(client):
    session = await _make_session(client)
    code = session["room_code"]

    a = await client.post("/api/game/join", json={"room_code": code, "player_name": "Aria"})
    b = await client.post("/api/game/join", json={"room_code": code, "player_name": "Cohen"})
    assert a.json()["player_id"] != b.json()["player_id"]

    players = await client.get(f"/api/game/sessions/{session['id']}/players")
    assert len(players.json()["players"]) == 2
