"""Tavern brawl scenario — 4 AutoGen-backed personas free-roleplay for N turns.

Falls back to `ScriptedPolicy` per-bot if Ollama isn't reachable, so this
scenario remains runnable in CI without a GPU (it then degrades to a smaller
scripted version of the smoke test).
"""
from __future__ import annotations

import logging
from typing import Any

from ..agents import PERSONAS, LLMPolicy
from ..api_client import ApiClient
from ..bot_player import BotConfig, ScriptedPolicy, TranscriptEntry

logger = logging.getLogger(__name__)


_FALLBACK_SCRIPTS: dict[str, list[str]] = {
    "Lyra Moonwhisper": [
        "I cast detect magic and study the booth in the corner.",
        "I share what arcane traces I see with the others.",
        "I prepare misty step in case we need to retreat.",
    ],
    "Thorin Ironforge": [
        "I size up the hooded stranger and step between them and the rest of us.",
        "I keep my axe loose at my side and watch the exits.",
        "I growl a low warning to anyone who comes too close.",
    ],
    "Zephyr Quickfoot": [
        "I slip into the shadows near the window and listen.",
        "I check the patrons' belts for blades or coin pouches.",
        "I signal Thorin that two armed figures are by the back door.",
    ],
    "Grimshaw Stormblade": [
        "I offer the stranger a cup of mead in the name of peace.",
        "I invoke my divine sense — is there evil in this room?",
        "I stand ready, shield strapped, eyes calm.",
    ],
}


async def build(api: ApiClient) -> dict[str, Any]:
    campaign = await api.create_minimal_campaign(name="Bot Playtest — Tavern Brawl")
    session = await api.create_session(
        campaign_id=campaign["id"],
        current_scene=(
            "The Drowned Crow is loud tonight. A hooded figure in the corner "
            "has been watching your table for the last hour."
        ),
    )
    session_id = session["id"]
    room_code = await api.get_room_code(session_id)

    persona_names = list(PERSONAS.keys())

    bots: list[BotConfig] = []
    llm_used = 0
    for name in persona_names:
        persona = PERSONAS[name]
        others = [n for n in persona_names if n != name]
        policy = await LLMPolicy.try_create(persona, other_persona_names=others)
        if policy is not None:
            llm_used += 1
            bots.append(BotConfig(name=persona.name, policy=policy))
        else:
            script = _FALLBACK_SCRIPTS[persona.name]
            bots.append(BotConfig(name=persona.name, policy=ScriptedPolicy(script)))

    logger.info(
        "tavern_brawl: %d/%d bots using LLM (rest scripted fallback)",
        llm_used,
        len(bots),
    )

    return {
        "campaign_id": campaign["id"],
        "session_id": session_id,
        "room_code": room_code,
        "bots": bots,
        "expected_phases": ["exploration"],
        "llm_bots": llm_used,
    }


def assertions(transcript: list[TranscriptEntry], summary: dict) -> list[str]:
    """Loose checks — this scenario is for realism, not strict regression."""
    problems: list[str] = []

    actions_sent: dict[str, int] = {}
    for entry in transcript:
        if entry.direction == "sent" and entry.message.get("type") == "action":
            actions_sent[entry.bot] = actions_sent.get(entry.bot, 0) + 1

    bots = summary.get("bots", [])
    for bot in bots:
        if actions_sent.get(bot, 0) < 1:
            problems.append(f"{bot}: sent 0 actions")

    return problems
