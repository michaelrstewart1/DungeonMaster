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
async def test_rejoin_keeps_the_claimed_character(client):
    """A phone that still holds another session's hero id must not replace its seat."""
    session = await _make_session(client)
    code = session["room_code"]

    first = await client.post(
        "/api/game/join",
        json={"room_code": code, "player_name": "Bram", "character_id": "char-thorne"},
    )
    player_id = first.json()["player_id"]

    second = await client.post(
        "/api/game/join",
        json={
            "room_code": code,
            "player_name": "Bram",
            "player_id": player_id,
            "character_id": "char-from-blackwood",
        },
    )
    assert second.status_code == 200
    assert second.json()["rejoined"] is True
    assert second.json()["character_id"] == "char-thorne"

    players = (await client.get(f"/api/game/sessions/{session['id']}/players")).json()["players"]
    assert players[0]["character_id"] == "char-thorne"


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
async def test_resume_collapses_duplicate_seats_and_releases_heroes(client):
    """A new night must not keep two Cyras, or leave Lyra stuck on a stale seat."""
    from app.api import storage

    session = await _make_session(client)
    sid = session["id"]
    code = session["room_code"]
    storage.session_players[sid] = [
        {"id": "p-old", "name": "Cyra", "character_id": "char-lyra", "present": True},
        {"id": "p-dup", "name": " cyra ", "character_id": None, "present": True},
        {"id": "p-dain", "name": "Dain", "character_id": "char-kael", "device_id": "phone-dain", "present": True},
    ]

    resumed = await client.get(f"/api/game/sessions/{sid}/resume")
    assert resumed.status_code == 200
    # Nobody is connected, so the lobby list is empty until they rejoin.
    assert resumed.json()["players"] == []

    rows = storage.session_players[sid]
    assert [row["name"] for row in rows].count("Cyra") == 1
    cyra = next(row for row in rows if row["name"] == "Cyra")
    assert cyra["id"] == "p-old"  # the row that actually held the hero
    assert cyra["character_id"] is None
    assert cyra["previous_character_id"] == "char-lyra"
    assert cyra["present"] is False
    dain = next(row for row in rows if row["id"] == "p-dain")
    assert dain["character_id"] is None
    assert dain["previous_character_id"] == "char-kael"

    again = await client.post("/api/game/join", json={"room_code": code, "player_name": "Cyra"})
    assert again.status_code == 200
    assert again.json()["rejoined"] is True
    assert again.json()["player_id"] == "p-old"
    assert again.json()["character_id"] is None
    assert again.json()["previous_character_id"] == "char-lyra"

    listed = (await client.get(f"/api/game/sessions/{sid}/players")).json()["players"]
    assert [player["name"] for player in listed] == ["Cyra"]
    claim = await client.post(
        f"/api/game/sessions/{sid}/select-character",
        json={"player_id": again.json()["player_id"], "character_id": "char-lyra"},
    )
    assert claim.status_code == 200


@pytest.mark.asyncio
async def test_rejoin_by_device_reclaims_and_renames_stale_seat(client):
    """The same phone reclaims its seat even when the typed name differs."""
    session = await _make_session(client)
    code = session["room_code"]
    sid = session["id"]

    first = await client.post(
        "/api/game/join",
        json={"room_code": code, "player_name": "Dai", "device_id": "phone-dain", "character_id": "char-kael"},
    )
    assert first.status_code == 200
    await client.get(f"/api/game/sessions/{sid}/resume")

    second = await client.post(
        "/api/game/join",
        json={"room_code": code, "player_name": "Dain", "device_id": "phone-dain"},
    )
    assert second.status_code == 200
    assert second.json()["rejoined"] is True
    assert second.json()["player_id"] == first.json()["player_id"]
    assert second.json()["character_id"] is None
    assert second.json()["previous_character_id"] == "char-kael"

    listed = (await client.get(f"/api/game/sessions/{sid}/players")).json()["players"]
    assert len(listed) == 1
    assert listed[0]["name"] == "Dain"
    assert listed[0]["character_id"] is None


@pytest.mark.asyncio
async def test_select_character_unknown_player_404(client):
    session = await _make_session(client)
    res = await client.post(
        f"/api/game/sessions/{session['id']}/select-character",
        json={"player_id": "nope", "character_id": "char-1"},
    )
    assert res.status_code == 404
