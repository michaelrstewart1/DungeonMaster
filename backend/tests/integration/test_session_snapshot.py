"""A reconnect must read the live session, never an earlier combat snapshot."""
import copy

import pytest

import app.repository as repo
from app.api import storage
from app.models.database import GameSessionDB

BLACKWOOD = {
    "initiative_order": ["ashara", "lyra", "undead-1", "kael", "thorne"],
    "current_turn_index": 0,
    "round_number": 1,
    "combatants": [{"id": "ashara", "name": "Ashara"}],
    "log": [],
}


async def _session(client) -> dict:
    campaign = await client.post("/api/campaigns", json={"name": "Lighthouse", "description": "x"})
    assert campaign.status_code == 201
    created = await client.post(
        "/api/game/sessions",
        json={
            "campaign_id": campaign.json()["id"],
            "current_phase": "exploration",
            "current_scene": "Session starting...",
        },
    )
    assert created.status_code == 201
    return created.json()


@pytest.mark.asyncio
async def test_stale_snapshot_cannot_restore_earlier_combat(client, app):
    """The write that used to put one phone back on Blackwood is refused."""
    created = await _session(client)
    sid = created["id"]
    current = (await client.get(f"/api/game/sessions/{sid}/state")).json()

    stale = copy.deepcopy(current)
    stale["current_phase"] = "combat"
    stale["current_scene"] = "Blackwood"
    stale["combat_state"] = BLACKWOOD

    live = copy.deepcopy(current)
    live["current_phase"] = "exploration"
    live["current_scene"] = "The lighthouse antechamber"
    live["combat_state"] = None
    live["narrative_history"] = ["DM: You stand in the lighthouse antechamber."]

    async with app.state.db_factory() as db:
        saved = await repo.save_game_session(db, live)
        await db.commit()
    assert saved.applied is True

    async with app.state.db_factory() as db:
        refused = await repo.save_game_session(db, stale)
        await db.commit()
    assert refused.applied is False
    assert refused["current_scene"] == "The lighthouse antechamber"
    assert refused["combat_state"] is None

    got = await client.get(f"/api/game/sessions/{sid}/state")
    assert got.headers["cache-control"] == "no-store"
    body = got.json()
    assert body["current_scene"] == "The lighthouse antechamber"
    assert body["current_phase"] == "exploration"
    assert body["combat_state"] is None
    assert body["state_version"] == saved["state_version"]


@pytest.mark.asyncio
async def test_extra_data_cannot_mask_authoritative_scene(client, app):
    created = await _session(client)
    sid = created["id"]
    async with app.state.db_factory() as db:
        row = await db.get(GameSessionDB, sid)
        assert row is not None
        extra = dict(row.extra_data or {})
        extra["current_scene"] = "Blackwood"
        extra["current_phase"] = "combat"
        extra["combat_state"] = BLACKWOOD
        row.extra_data = extra
        await db.commit()

    got = await client.get(f"/api/game/sessions/{sid}/state")
    body = got.json()
    assert body["current_scene"] == "Session starting..."
    assert body["current_phase"] == "exploration"
    assert body["combat_state"] is None


@pytest.mark.asyncio
async def test_resume_does_not_steal_a_live_room_code(client):
    older = await _session(client)
    live = await _session(client)
    stolen = older["room_code"]
    storage.room_codes[stolen] = live["id"]

    resumed = await client.get(f"/api/game/sessions/{older['id']}/resume")
    assert resumed.status_code == 200
    new_code = resumed.json()["room_code"]
    assert new_code != stolen
    assert storage.room_codes[stolen] == live["id"]
    assert storage.room_codes[new_code] == older["id"]

    join = await client.post(
        "/api/game/join",
        json={"room_code": stolen, "player_name": "Aria"},
    )
    assert join.status_code == 200
    assert join.json()["session_id"] == live["id"]
