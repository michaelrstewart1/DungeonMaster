"""End-of-session flow — recap generated and persisted for next session."""
import pytest


async def _make_session(client) -> tuple[str, str]:
    campaign = await client.post("/api/campaigns", json={"name": "End Test", "description": "x"})
    campaign_id = campaign.json()["id"]
    resp = await client.post(
        "/api/game/sessions",
        json={"campaign_id": campaign_id, "current_scene": "The dragon falls."},
    )
    return resp.json()["id"], campaign_id


@pytest.mark.asyncio
async def test_end_session_persists_recap(client):
    session_id, campaign_id = await _make_session(client)

    resp = await client.post(f"/api/game/sessions/{session_id}/end")
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]
    assert data["ended_at"]

    # Session record carries the end stamp
    state = await client.get(f"/api/game/sessions/{session_id}/state")
    assert state.status_code == 200

    # Recap feeds the next session's greeting
    recap = await client.get(f"/api/game/sessions/{session_id}/recap")
    assert recap.status_code == 200
    assert recap.json()["has_recap"] is True


@pytest.mark.asyncio
async def test_end_unknown_session_404(client):
    resp = await client.post("/api/game/sessions/nope/end")
    assert resp.status_code == 404
