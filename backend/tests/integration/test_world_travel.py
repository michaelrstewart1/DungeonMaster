"""Integration tests for world map travel (macro navigation)."""
from starlette.testclient import TestClient

from tests.integration.test_ws_game import (  # noqa: F401 (fixtures)
    ws_client,
    reset_storage_for_ws,
    create_test_session,
)


def _world(client: TestClient, sid: str) -> dict:
    res = client.get(f"/api/game/sessions/{sid}/world-map")
    assert res.status_code == 200
    return res.json()


class TestWorldMapSeeding:
    def test_session_gets_default_world_map(self, ws_client: TestClient):
        sid = create_test_session(ws_client)
        world = _world(ws_client, sid)
        assert world["current_location"] == "crossroads-village"
        ids = {loc["id"] for loc in world["locations"]}
        assert "forgotten-depths" in ids

    def test_start_visited_and_neighbors_discovered(self, ws_client: TestClient):
        sid = create_test_session(ws_client)
        locs = {l["id"]: l for l in _world(ws_client, sid)["locations"]}
        assert locs["crossroads-village"]["visited"] is True
        assert locs["darkwood-forest"]["discovered"] is True
        assert locs["mountain-pass"]["discovered"] is True
        # Two hops away stays hidden
        assert locs["forgotten-depths"]["discovered"] is False

    def test_campaign_locations_override_default(self, ws_client: TestClient):
        camp = ws_client.post("/api/campaigns", json={
            "name": "Custom World", "description": "x", "character_ids": [],
            "world_state": {"locations": [
                {"id": "a", "name": "Alpha", "description": "start", "scene_type": "village", "connections": ["b"]},
                {"id": "b", "name": "Beta", "description": "end", "scene_type": "dungeon", "connections": ["a"]},
            ]},
            "dm_settings": {},
        }).json()
        sid = ws_client.post("/api/game/sessions", json={
            "campaign_id": camp["id"], "current_phase": "exploration", "current_scene": "Start.",
        }).json()["id"]
        world = _world(ws_client, sid)
        assert world["current_location"] == "a"
        assert {l["id"] for l in world["locations"]} == {"a", "b"}


class TestTravel:
    def test_travel_to_connected_location(self, ws_client: TestClient):
        sid = create_test_session(ws_client)
        res = ws_client.post(f"/api/game/sessions/{sid}/travel", json={"destination_id": "darkwood-forest"})
        assert res.status_code == 200
        data = res.json()
        assert data["current_location"] == "darkwood-forest"
        assert data["narration"]
        assert data["detected_scene"] == "forest"
        # State persisted
        state = ws_client.get(f"/api/game/sessions/{sid}/state").json()
        assert state["current_location"] == "darkwood-forest"
        assert "Darkwood" in state["current_scene"] or state["current_scene"]

    def test_travel_reveals_new_neighbors(self, ws_client: TestClient):
        sid = create_test_session(ws_client)
        ws_client.post(f"/api/game/sessions/{sid}/travel", json={"destination_id": "darkwood-forest"})
        locs = {l["id"]: l for l in _world(ws_client, sid)["locations"]}
        assert locs["darkwood-forest"]["visited"] is True
        assert locs["hollow-cave"]["discovered"] is True

    def test_travel_to_unconnected_location_rejected(self, ws_client: TestClient):
        sid = create_test_session(ws_client)
        res = ws_client.post(f"/api/game/sessions/{sid}/travel", json={"destination_id": "forgotten-depths"})
        assert res.status_code == 409
        assert "not reachable" in res.json()["detail"]

    def test_travel_to_current_location_rejected(self, ws_client: TestClient):
        sid = create_test_session(ws_client)
        res = ws_client.post(f"/api/game/sessions/{sid}/travel", json={"destination_id": "crossroads-village"})
        assert res.status_code == 400

    def test_travel_to_unknown_location_404(self, ws_client: TestClient):
        sid = create_test_session(ws_client)
        res = ws_client.post(f"/api/game/sessions/{sid}/travel", json={"destination_id": "narnia"})
        assert res.status_code == 404

    def test_travel_blocked_during_combat(self, ws_client: TestClient):
        sid = create_test_session(ws_client)
        ws_client.post(f"/api/game/sessions/{sid}/start-combat", json={
            "monsters": [{"name": "Goblin", "hp": 7, "ac": 13, "dexterity": 14}],
        })
        res = ws_client.post(f"/api/game/sessions/{sid}/travel", json={"destination_id": "darkwood-forest"})
        assert res.status_code == 409
        assert "combat" in res.json()["detail"].lower()

    def test_travel_appends_narrative_history(self, ws_client: TestClient):
        sid = create_test_session(ws_client)
        ws_client.post(f"/api/game/sessions/{sid}/travel", json={"destination_id": "darkwood-forest"})
        state = ws_client.get(f"/api/game/sessions/{sid}/state").json()
        joined = " ".join(state["narrative_history"])
        assert "travels" in joined and "Darkwood" in joined

    def test_travel_broadcasts_scene_change(self, ws_client: TestClient):
        sid = create_test_session(ws_client)
        with ws_client.websocket_connect(f"/ws/game/{sid}?role=observer") as obs:
            obs.receive_json()  # observer_ack
            ws_client.post(f"/api/game/sessions/{sid}/travel", json={"destination_id": "darkwood-forest"})
            msg = obs.receive_json()
            assert msg["type"] == "scene_change"
            assert msg["current_location"] == "darkwood-forest"
            assert msg["narration"]
