"""Smoke scenario: 3 bots, each sends a fixed sequence of scripted actions."""
from __future__ import annotations

from typing import Any

from ..api_client import ApiClient
from ..bot_player import BotConfig, ScriptedPolicy, TranscriptEntry

BOT_SCRIPTS: dict[str, list[str]] = {
    "Thorin (bot)": [
        "I look around the room and size up the patrons.",
        "I approach the hooded stranger and ask their business.",
        "I rest my hand on the haft of my axe, watchful.",
    ],
    "Lyra (bot)": [
        "I order a drink and listen for gossip.",
        "I cast a quiet detect-magic and scan the booth.",
        "I share what I sense with my companions.",
    ],
    "Zephyr (bot)": [
        "I slip into the shadows by the wall to watch.",
        "I check the exits and note who's armed.",
        "I signal Thorin with a low whistle.",
    ],
}


async def build(api: ApiClient) -> dict[str, Any]:
    campaign = await api.create_minimal_campaign(name="Bot Playtest — Smoke")
    session = await api.create_session(campaign_id=campaign["id"])
    session_id = session["id"]
    room_code = await api.get_room_code(session_id)

    bots = [
        BotConfig(name=name, policy=ScriptedPolicy(actions))
        for name, actions in BOT_SCRIPTS.items()
    ]

    return {
        "campaign_id": campaign["id"],
        "session_id": session_id,
        "room_code": room_code,
        "bots": bots,
        "expected_phases": ["exploration"],
    }


def assertions(transcript: list[TranscriptEntry], summary: dict) -> list[str]:
    """Verify each bot sent its full script and received turn_results."""
    problems: list[str] = []

    actions_sent: dict[str, int] = {}
    turn_results_recv: dict[str, int] = {}

    for entry in transcript:
        msg = entry.message
        if entry.direction == "sent" and msg.get("type") == "action":
            actions_sent[entry.bot] = actions_sent.get(entry.bot, 0) + 1
        if entry.direction == "recv" and msg.get("type") == "turn_result":
            turn_results_recv[entry.bot] = turn_results_recv.get(entry.bot, 0) + 1

    for bot_name, script in BOT_SCRIPTS.items():
        sent = actions_sent.get(bot_name, 0)
        if sent != len(script):
            problems.append(
                f"{bot_name}: sent {sent} actions, expected {len(script)}"
            )

    # Every bot should observe at least 1 turn_result echo (proving the WS
    # broadcast loop reached them). Stricter receive-count assertions are
    # racy because a bot whose policy is exhausted may exit before later
    # broadcasts arrive — that's expected behavior, not a bug.
    for bot_name in BOT_SCRIPTS:
        recv = turn_results_recv.get(bot_name, 0)
        if recv < 1:
            problems.append(
                f"{bot_name}: received 0 turn_result broadcasts (WS broadcast loop unreachable?)"
            )

    return problems
