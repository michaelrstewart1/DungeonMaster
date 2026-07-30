"""Session resume — a saved session must be recoverable after a restart."""
import pytest

from app.api import storage


async def _create_session(client) -> dict:
    campaign = await client.post("/api/campaigns", json={"name": "Resume Test", "description": "x"})
    assert campaign.status_code == 201
    campaign_id = campaign.json()["id"]
    resp = await client.post(
        "/api/game/sessions",
        json={"campaign_id": campaign_id, "current_scene": "A dark tavern."},
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.mark.asyncio
async def test_room_code_persisted_on_session(client):
    session = await _create_session(client)
    state = await client.get(f"/api/game/sessions/{session['id']}/state")
    assert state.status_code == 200
    # room_code must be stored on the session record, not only in memory
    assert state.json().get("room_code") == session["room_code"]


@pytest.mark.asyncio
async def test_resume_restores_room_code_after_restart(client):
    session = await _create_session(client)
    session_id = session["id"]
    room_code = session["room_code"]

    # Simulate a backend restart losing volatile state
    storage.room_codes.clear()
    storage.session_players.clear()

    resp = await client.get(f"/api/game/sessions/{session_id}/resume")
    assert resp.status_code == 200
    data = resp.json()
    assert data["room_code"] == room_code
    assert data["session"]["id"] == session_id
    assert data["players"] == []
    assert data["recent_narrative"] == ["A dark tavern."]

    # Players can now rejoin with the original code
    join = await client.post(
        "/api/game/join",
        json={"room_code": room_code, "player_name": "Aria"},
    )
    assert join.status_code == 200
    assert join.json()["session_id"] == session_id


@pytest.mark.asyncio
async def test_resume_unknown_session_404(client):
    resp = await client.get("/api/game/sessions/nope/resume")
    assert resp.status_code == 404
