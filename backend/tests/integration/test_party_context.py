"""The live DM context is the heroes whose players are connected."""
import pytest

from app.api.routes.game import _generate_dm_response
from app.api.websockets.game_ws import manager


async def _hero(client, name: str) -> str:
    created = await client.post(
        "/api/characters",
        json={"name": name, "race": "human", "class_name": "fighter", "level": 3, "hp": 20, "ac": 14},
    )
    assert created.status_code == 201, created.text
    return created.json()["id"]


@pytest.mark.asyncio
async def test_dm_context_omits_heroes_nobody_is_playing(client, app):
    lyra_id = await _hero(client, "Lyra Moonwhisper")
    ashara_id = await _hero(client, "Ashara Brightscale")
    campaign = await client.post(
        "/api/campaigns",
        json={
            "name": "Night 7",
            "description": "ward",
            "character_ids": [lyra_id, ashara_id],
        },
    )
    assert campaign.status_code == 201, campaign.text
    session = await client.post(
        "/api/game/sessions",
        json={"campaign_id": campaign.json()["id"], "current_scene": "The ward."},
    )
    assert session.status_code == 201, session.text
    session_id = session.json()["id"]
    code = session.json()["room_code"]

    joined = await client.post(
        "/api/game/join",
        json={"room_code": code, "player_name": "Aria"},
    )
    player_id = joined.json()["player_id"]
    claim = await client.post(
        f"/api/game/sessions/{session_id}/select-character",
        json={"player_id": player_id, "character_id": ashara_id},
    )
    assert claim.status_code == 200, claim.text

    seen: dict = {}

    class FakeNarrator:
        async def narrate_exploration(self, **kwargs):
            seen.update(kwargs)
            return (
                "Ashara, observing Lyra's findings, steps forward. "
                "The abjuration magic Lyra detected earlier still hums."
            )

    manager.register_player(session_id, player_id, object())
    try:
        async with app.state.db_factory() as db:
            from app.repository import get_game_session

            live = await get_game_session(db, session_id)
            assert live is not None
            narration = await _generate_dm_response(
                "I study the ward.",
                live,
                narrator=FakeNarrator(),
                db=db,
            )
    finally:
        manager.player_connections.pop(session_id, None)

    names = [hero.get("name") for hero in seen["characters"]]
    assert names == ["Ashara Brightscale"]
    absent = [hero.get("name") for hero in seen["absent_characters"]]
    assert absent == ["Lyra Moonwhisper"]
    assert "Lyra" not in narration
    assert "Ashara" in narration
