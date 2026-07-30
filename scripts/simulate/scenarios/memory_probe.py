"""Memory/consistency probe — A/B eval scenario for narration models.

Plants canonical facts early (NPC name, a promise, an item, a location),
burns several distractor turns, then probes the DM's recall. Assertions
score how many planted facts the DM's answers actually contain.

Run against a live backend with a REAL narrator (Ollama/Anthropic/etc.):

    python -m scripts.simulate.runner --scenario memory_probe --max-turns 20 --timeout 600

Compare `assertion_failures` counts across models/providers to A/B
consistency. With the keyword-mock narrator (no LLM configured) this
scenario is expected to fail — it measures the model, not the plumbing.
"""
from __future__ import annotations

from typing import Any

from ..api_client import ApiClient
from ..bot_player import BotConfig, ScriptedPolicy, TranscriptEntry

# Facts the DM must retain. Keys are probe labels; values are the tokens we
# expect to reappear when the bot asks about them later.
PLANTED_FACTS = {
    "npc_name": ["barlow"],
    "promise": ["50", "gold"],
    "item": ["obsidian", "key"],
    "location": ["duskhollow"],
}

SCRIPT = [
    # --- plant phase ---
    "I introduce myself to the innkeeper and ask his name. He tells me he is Barlow.",
    "I promise Barlow the innkeeper 50 gold pieces if he keeps our stay a secret.",
    "I take the obsidian key from under the floorboard and pocket it carefully.",
    "I ask around about the road to Duskhollow, the burned mining village.",
    # --- distractor phase ---
    "I sharpen my blade by the fire.",
    "I order a bowl of stew and eat quietly.",
    "I check my bootlaces and count my remaining rations.",
    "I watch the rain streak down the window.",
    "I hum an old marching tune to myself.",
    "I stretch and crack my knuckles.",
    # --- probe phase ---
    "PROBE npc_name: I walk back to the innkeeper and greet him by name. What is his name?",
    "PROBE promise: I remind the innkeeper exactly what I promised to pay him and for what.",
    "PROBE item: I reach into my pocket and examine the item I took from under the floorboard. Describe it.",
    "PROBE location: I tell my companion the name of the village we are heading to. What do I say?",
]


async def build(api: ApiClient) -> dict[str, Any]:
    campaign = await api.create_minimal_campaign(name="Bot Playtest — Memory Probe")
    session = await api.create_session(campaign_id=campaign["id"])
    session_id = session["id"]
    room_code = await api.get_room_code(session_id)

    bots = [BotConfig(name="Probe (bot)", policy=ScriptedPolicy(SCRIPT))]

    return {
        "campaign_id": campaign["id"],
        "session_id": session_id,
        "room_code": room_code,
        "bots": bots,
        "expected_phases": ["exploration"],
    }


def assertions(transcript: list[TranscriptEntry], summary: dict) -> list[str]:
    """Score DM recall: each probe's narration must contain the planted tokens."""
    problems: list[str] = []

    # turn_result broadcasts embed the originating action — pair directly.
    results: dict[str, str] = {}
    for entry in transcript:
        msg = entry.message
        if entry.direction == "recv" and msg.get("type") == "turn_result":
            action = msg.get("action", "") or ""
            if action.startswith("PROBE "):
                label = action.split(":", 1)[0].removeprefix("PROBE ").strip()
                results[label] = (msg.get("narration") or "").lower()

    for label, tokens in PLANTED_FACTS.items():
        narration = results.get(label)
        if narration is None:
            problems.append(f"probe '{label}': no turn_result narration captured")
            continue
        missing = [t for t in tokens if t not in narration]
        if missing:
            problems.append(
                f"probe '{label}': DM failed to recall {missing} — narration: {narration[:160]!r}"
            )

    recalled = len(PLANTED_FACTS) - sum(1 for p in problems if p.startswith("probe"))
    summary["memory_score"] = f"{recalled}/{len(PLANTED_FACTS)}"
    return problems
