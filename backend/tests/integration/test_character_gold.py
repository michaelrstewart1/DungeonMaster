"""Tests for per-character gold (Phase A of trade extensions)."""
import pytest
from httpx import AsyncClient


BASE_CHAR = {
    "name": "Goldie",
    "race": "human",
    "class_name": "fighter",
    "level": 1,
    "hp": 10,
    "ac": 10,
}


async def _create(client: AsyncClient, **overrides):
    body = {**BASE_CHAR, **overrides}
    resp = await client.post("/api/characters", json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestCharacterGoldField:
    async def test_default_gold_is_zero(self, client: AsyncClient):
        char = await _create(client)
        assert char["gold"] == 0

    async def test_gold_set_on_create(self, client: AsyncClient):
        char = await _create(client, gold=250)
        assert char["gold"] == 250

    async def test_gold_update_via_put(self, client: AsyncClient):
        char = await _create(client, gold=10)
        resp = await client.put(f"/api/characters/{char['id']}", json={"gold": 75})
        assert resp.status_code == 200
        assert resp.json()["gold"] == 75

    async def test_negative_gold_on_create_rejected(self, client: AsyncClient):
        resp = await client.post(
            "/api/characters",
            json={**BASE_CHAR, "gold": -5},
        )
        assert resp.status_code == 422


class TestCharacterGoldAdjust:
    async def test_add_gold(self, client: AsyncClient):
        char = await _create(client, gold=10)
        resp = await client.post(
            f"/api/characters/{char['id']}/gold",
            json={"amount": 50, "reason": "quest reward"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["gold"] == 60
        assert body["delta"] == 50
        assert body["reason"] == "quest reward"

    async def test_spend_gold(self, client: AsyncClient):
        char = await _create(client, gold=100)
        resp = await client.post(
            f"/api/characters/{char['id']}/gold",
            json={"amount": -30, "reason": "potion"},
        )
        assert resp.status_code == 200
        assert resp.json()["gold"] == 70

    async def test_spend_more_than_have_rejected(self, client: AsyncClient):
        char = await _create(client, gold=10)
        resp = await client.post(
            f"/api/characters/{char['id']}/gold",
            json={"amount": -50},
        )
        assert resp.status_code == 400
        # Character gold unchanged
        get_resp = await client.get(f"/api/characters/{char['id']}")
        assert get_resp.json()["gold"] == 10

    async def test_unknown_character_404(self, client: AsyncClient):
        resp = await client.post(
            "/api/characters/does-not-exist/gold",
            json={"amount": 1},
        )
        assert resp.status_code == 404
