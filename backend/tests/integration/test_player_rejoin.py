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


@pytest.mark.asyncio
async def test_select_character_claims_exclusively(client):
    session = await _make_session(client)
    code = session["room_code"]
    sid = session["id"]

    a = (await client.post("/api/game/join", json={"room_code": code, "player_name": "Kit"})).json()
    b = (await client.post("/api/game/join", json={"room_code": code, "player_name": "Cohen"})).json()

    # Kit claims char-1
    first = await client.post(
        f"/api/game/sessions/{sid}/select-character",
        json={"player_id": a["player_id"], "character_id": "char-1"},
    )
    assert first.status_code == 200

    # Cohen cannot claim the same character
    conflict = await client.post(
        f"/api/game/sessions/{sid}/select-character",
        json={"player_id": b["player_id"], "character_id": "char-1"},
    )
    assert conflict.status_code == 409
    assert "Kit" in conflict.json()["detail"]

    # A different character is fine
    ok = await client.post(
        f"/api/game/sessions/{sid}/select-character",
        json={"player_id": b["player_id"], "character_id": "char-2"},
    )
    assert ok.status_code == 200

    players = (await client.get(f"/api/game/sessions/{sid}/players")).json()["players"]
    bound = {p["name"]: p["character_id"] for p in players}
    assert bound == {"Kit": "char-1", "Cohen": "char-2"}


@pytest.mark.asyncio
async def test_select_character_reclaim_own_is_idempotent(client):
    session = await _make_session(client)
    code = session["room_code"]
    sid = session["id"]

    a = (await client.post("/api/game/join", json={"room_code": code, "player_name": "Kit"})).json()

    for _ in range(2):
        res = await client.post(
            f"/api/game/sessions/{sid}/select-character",
            json={"player_id": a["player_id"], "character_id": "char-1"},
        )
        assert res.status_code == 200


@pytest.mark.asyncio
async def test_select_character_unknown_player_404(client):
    session = await _make_session(client)
    res = await client.post(
        f"/api/game/sessions/{session['id']}/select-character",
        json={"player_id": "nope", "character_id": "char-1"},
    )
    assert res.status_code == 404
