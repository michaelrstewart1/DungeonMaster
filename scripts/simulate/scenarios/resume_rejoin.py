"""Resume/rejoin scenario: verifies session persistence and the player
rejoin protocol — the two things that make long campaigns possible.

Flow (all REST, single bot keeps the WS loop honest):
  1. Bot joins + acts normally.
  2. post_setup: submit a REST action so narrative exists, hit /resume and
     verify the session snapshot + room code round-trip, then re-join with
     the same player name and verify the same player_id comes back (rejoin,
     not a duplicate roster entry).
"""
from __future__ import annotations

from typing import Any

from ..api_client import ApiClient
from ..bot_player import BotConfig, ScriptedPolicy, TranscriptEntry

# Collected during post_setup, reported by assertions()
_PROBLEMS: list[str] = []

BOT_NAME = "Rejoin Rica (bot)"


async def build(api: ApiClient) -> dict[str, Any]:
    _PROBLEMS.clear()
    campaign = await api.create_minimal_campaign(name="Bot Playtest — Resume/Rejoin")
    session = await api.create_session(campaign_id=campaign["id"])
    session_id = session["id"]
    room_code = await api.get_room_code(session_id)

    bots = [
        BotConfig(
            name=BOT_NAME,
            policy=ScriptedPolicy([
                "I carve my initials into the tavern table.",
                "I ask the barkeep about the carving I just made.",
            ]),
        )
    ]

    return {
        "campaign_id": campaign["id"],
        "session_id": session_id,
        "room_code": room_code,
        "bots": bots,
        "post_setup": post_setup,
        "expected_phases": ["exploration"],
    }


async def post_setup(api: ApiClient, ctx: dict, bots: list) -> None:
    session_id = ctx["session_id"]
    room_code = ctx["room_code"]

    # 1. Seed narrative via the REST action endpoint
    r = await api._client.post(
        f"/api/game/sessions/{session_id}/action",
        json={"type": "interact", "message": "I bury a copper coin under the floorboard."},
    )
    if r.status_code != 200:
        _PROBLEMS.append(f"REST action failed: {r.status_code} {r.text[:200]}")
        return

    # 2. Resume must return the persisted session with our narrative intact
    r = await api._client.get(f"/api/game/sessions/{session_id}/resume")
    if r.status_code != 200:
        _PROBLEMS.append(f"/resume failed: {r.status_code}")
        return
    body = r.json()
    if body.get("room_code") != room_code:
        _PROBLEMS.append(
            f"/resume room_code mismatch: {body.get('room_code')} != {room_code}"
        )
    history = body.get("session", {}).get("narrative_history") or []
    if not any("copper coin" in line for line in history):
        _PROBLEMS.append("/resume lost the narrative history (copper coin action missing)")

    # 3. Rejoin with the same player name → must map to the same player_id
    first = await api.join(room_code, "Persistent Pete")
    second = await api.join(room_code, "Persistent Pete")
    if first.player_id != second.player_id:
        _PROBLEMS.append(
            f"rejoin created a new identity: {first.player_id} != {second.player_id}"
        )
    players = await api.list_players(session_id)
    petes = [p for p in players if p.get("name") == "Persistent Pete"]
    if len(petes) != 1:
        _PROBLEMS.append(f"rejoin duplicated the roster entry: {len(petes)} Petes")


def assertions(transcript: list[TranscriptEntry], summary: dict) -> list[str]:
    problems = list(_PROBLEMS)

    # The bot should still complete its normal scripted turns
    sent = sum(
        1 for e in transcript
        if e.direction == "sent" and e.message.get("type") == "action" and e.bot == BOT_NAME
    )
    if sent < 2:
        problems.append(f"{BOT_NAME}: sent {sent} actions, expected 2")
    return problems
