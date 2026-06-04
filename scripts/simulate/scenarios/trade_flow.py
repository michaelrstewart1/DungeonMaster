"""Trade scenario — exercises the full player-to-player trade flow.

Two players join, the harness pre-populates each with a structured item via
the REST API, then bot A creates a trade offer to bot B and bot B accepts
over the new trade endpoints. We verify both inventories change and that
the WS `trade_offer` and `trade_resolved` messages are delivered correctly.
"""
from __future__ import annotations

import asyncio
import logging
import uuid as _uuid
from typing import Any

import httpx

from ..api_client import ApiClient
from ..bot_player import BotConfig, ScriptedPolicy, TranscriptEntry

logger = logging.getLogger(__name__)


async def build(api: ApiClient) -> dict[str, Any]:
    campaign = await api.create_minimal_campaign(name="Bot Playtest — Trade Flow")
    session = await api.create_session(
        campaign_id=campaign["id"],
        current_scene="You stand in a quiet inn, ready to trade goods.",
    )
    session_id = session["id"]
    room_code = await api.get_room_code(session_id)

    # Create two characters with a small structured_inventory each. We use
    # the same httpx client the harness wraps so we benefit from the 404
    # retry workaround.
    async def _post(path: str, payload: dict) -> dict:
        # api._client is the underlying httpx.AsyncClient.
        r = await api._client.post(path, json=payload)
        r.raise_for_status()
        return r.json()

    char_a = await _post("/api/characters", {
        "name": "Trader Alice",
        "race": "human",
        "class_name": "fighter",
        "level": 1,
        "strength": 10, "dexterity": 10, "constitution": 10,
        "intelligence": 10, "wisdom": 10, "charisma": 10,
        "hp": 10, "max_hp": 10, "ac": 10, "speed": 30,
        "experience_points": 0,
        "structured_inventory": [
            {"id": str(_uuid.uuid4()), "name": "Healing Potion", "quantity": 3,
             "rarity": "common", "item_type": "potion", "description": "Restores 2d4+2 HP"},
        ],
    })
    char_b = await _post("/api/characters", {
        "name": "Trader Bob",
        "race": "human",
        "class_name": "rogue",
        "level": 1,
        "strength": 10, "dexterity": 10, "constitution": 10,
        "intelligence": 10, "wisdom": 10, "charisma": 10,
        "hp": 10, "max_hp": 10, "ac": 10, "speed": 30,
        "experience_points": 0,
        "structured_inventory": [
            {"id": str(_uuid.uuid4()), "name": "Silver Dagger", "quantity": 1,
             "rarity": "uncommon", "item_type": "weapon", "description": ""},
        ],
    })

    # Both bots use a single scripted "say hello" then idle — the actual
    # trade is driven from the post_run hook below.
    bots: list[BotConfig] = [
        BotConfig(name="Alice", character_id=char_a["id"], policy=ScriptedPolicy(["I lay out my wares on the table."])),
        BotConfig(name="Bob", character_id=char_b["id"], policy=ScriptedPolicy(["I take a seat across from Alice."])),
    ]

    return {
        "campaign_id": campaign["id"],
        "session_id": session_id,
        "room_code": room_code,
        "bots": bots,
        "char_a_id": char_a["id"],
        "char_b_id": char_b["id"],
        "item_a_id": char_a["structured_inventory"][0]["id"],
        "item_b_id": char_b["structured_inventory"][0]["id"],
        # Hook: runner will call this after both bots are connected.
        "post_setup": _drive_trade,
    }


async def _drive_trade(api: ApiClient, ctx: dict, bots: list) -> None:
    """Initiate a trade from Alice to Bob, then accept it from Bob's side.
    Verifies the trade_offer arrives on Bob's WS and trade_resolved on both.
    """
    session_id = ctx["session_id"]
    # Find the registered player_ids — they were set on the bot's `joined`
    # attribute by BotPlayer.announce().
    alice = next(b for b in bots if b.config.name == "Alice")
    bob = next(b for b in bots if b.config.name == "Bob")
    pid_a = alice.joined.player_id if alice.joined else None
    pid_b = bob.joined.player_id if bob.joined else None
    assert pid_a and pid_b, "bots must have joined before trade hook runs"

    # Give the WS player_join broadcasts a tick to land so the server's
    # register_player binding is in place.
    await asyncio.sleep(0.3)

    create_resp = await api._client.post(
        f"/api/game/sessions/{session_id}/trades",
        json={
            "from_player_id": pid_a,
            "from_character_id": ctx["char_a_id"],
            "to_player_id": pid_b,
            "to_character_id": ctx["char_b_id"],
            "offered_items": [{"item_id": ctx["item_a_id"], "quantity": 2}],
            "requested_items": [{"item_id": ctx["item_b_id"], "quantity": 1}],
            "note": "Two potions for the dagger?",
        },
    )
    create_resp.raise_for_status()
    body = create_resp.json()
    trade_id = body["trade"]["id"]
    logger.info("trade scenario: created trade %s, delivered=%s", trade_id, body["delivered"])

    # Give Bob a moment to actually receive the WS trade_offer.
    await asyncio.sleep(0.5)

    accept_resp = await api._client.post(
        f"/api/game/sessions/{session_id}/trades/{trade_id}/respond",
        json={"action": "accept", "player_id": pid_b},
    )
    accept_resp.raise_for_status()
    assert accept_resp.json()["trade"]["status"] == "accepted"
    logger.info("trade scenario: accepted trade %s", trade_id)

    # Let trade_resolved broadcast land on both bots before we tear down.
    await asyncio.sleep(0.4)


def assertions(transcript: list[TranscriptEntry], summary: dict) -> list[str]:
    problems: list[str] = []

    # Bob should have received exactly one trade_offer.
    offers = [
        e for e in transcript
        if e.direction == "recv"
        and e.bot == "Bob"
        and e.message.get("type") == "trade_offer"
    ]
    if len(offers) != 1:
        problems.append(f"Bob expected 1 trade_offer, got {len(offers)}")

    # Alice should NOT have received the trade_offer (private send).
    alice_offers = [
        e for e in transcript
        if e.direction == "recv"
        and e.bot == "Alice"
        and e.message.get("type") == "trade_offer"
    ]
    if alice_offers:
        problems.append(f"Alice received {len(alice_offers)} trade_offer(s); should be 0 (private send)")

    # Both bots should receive trade_resolved on accept.
    for who in ("Alice", "Bob"):
        resolved = [
            e for e in transcript
            if e.direction == "recv"
            and e.bot == who
            and e.message.get("type") == "trade_resolved"
        ]
        if len(resolved) != 1:
            problems.append(f"{who} expected 1 trade_resolved, got {len(resolved)}")
        elif resolved[0].message.get("trade", {}).get("status") != "accepted":
            problems.append(f"{who} trade_resolved status was {resolved[0].message.get('trade', {}).get('status')!r}, expected 'accepted'")

    return problems
