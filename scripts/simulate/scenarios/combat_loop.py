"""Combat loop scenario: drives the rules-engine combat endpoints end to end.

post_setup starts an encounter against weak goblins and fights it to the end
via /combat-action, verifying:
  - initiative includes the party character + numbered monsters
  - the deterministic engine reports events every action
  - combat ends in victory with XP, session returns to exploration
  - connected players receive combat_started / combat_update broadcasts
"""
from __future__ import annotations

from typing import Any

from ..api_client import ApiClient
from ..bot_player import BotConfig, ScriptedPolicy, TranscriptEntry

_PROBLEMS: list[str] = []

BOT_NAME = "Brawler Bram (bot)"

CHARACTER = {
    "name": "Bram",
    "race": "human",
    "class_name": "fighter",
    "level": 3,
    "strength": 16,
    "dexterity": 12,
    "constitution": 14,
    "intelligence": 10,
    "wisdom": 10,
    "charisma": 8,
    "max_hp": 28,
    "ac": 16,
}

ENEMIES = [{"name": "Goblin", "hp": 2, "ac": 8, "cr": 0.25, "count": 2}]


async def build(api: ApiClient) -> dict[str, Any]:
    _PROBLEMS.clear()
    character = await api.create_character(CHARACTER)

    payload = {
        "name": "Bot Playtest — Combat Loop",
        "description": "Auto-created by scripts/simulate for combat harness runs.",
        "character_ids": [character["id"]],
        "world_state": {"context": "A goblin ambush on the forest road."},
        "dm_settings": {},
    }
    r = await api._client.post("/api/campaigns", json=payload)
    r.raise_for_status()
    campaign = r.json()

    session = await api.create_session(
        campaign_id=campaign["id"],
        current_scene="Two goblins leap from the underbrush, blades drawn!",
    )
    session_id = session["id"]
    room_code = await api.get_room_code(session_id)

    bots = [
        BotConfig(
            name=BOT_NAME,
            policy=ScriptedPolicy(["I ready my sword and watch the treeline."]),
        )
    ]

    return {
        "campaign_id": campaign["id"],
        "session_id": session_id,
        "room_code": room_code,
        "bots": bots,
        "character_id": character["id"],
        "post_setup": post_setup,
        "expected_phases": ["exploration", "combat"],
    }


async def post_setup(api: ApiClient, ctx: dict, bots: list) -> None:
    session_id = ctx["session_id"]
    char_id = ctx["character_id"]

    # Start the encounter through the rules engine
    r = await api._client.post(
        f"/api/game/sessions/{session_id}/start-combat",
        json={"enemies": ENEMIES},
    )
    if r.status_code != 200:
        _PROBLEMS.append(f"start-combat failed: {r.status_code} {r.text[:200]}")
        return
    cs = r.json().get("combat_state") or {}
    order = cs.get("initiative_order") or []
    if len(order) != 3:
        _PROBLEMS.append(f"initiative should list 3 combatants, got {order}")
    if "Bram" not in order:
        _PROBLEMS.append(f"party character missing from initiative: {order}")

    # Fight to the finish (bounded)
    finished = False
    for _ in range(40):
        r = await api._client.post(
            f"/api/game/sessions/{session_id}/combat-action",
            json={"actor_id": char_id, "action_type": "attack"},
        )
        if r.status_code == 409:
            finished = True  # combat already resolved
            break
        if r.status_code != 200:
            _PROBLEMS.append(f"combat-action failed: {r.status_code} {r.text[:200]}")
            return
        body = r.json()
        if not body.get("events"):
            _PROBLEMS.append("combat-action returned no events")
        if body.get("combat_over"):
            finished = True
            if not body.get("victory"):
                _PROBLEMS.append("expected victory against 2 weak goblins")
            if body.get("xp_awarded", 0) <= 0:
                _PROBLEMS.append(f"expected XP award, got {body.get('xp_awarded')}")
            break
    if not finished:
        _PROBLEMS.append("combat did not finish within 40 actions")
        return

    # Session must be back in exploration with the fight in the record
    r = await api._client.get(f"/api/game/sessions/{session_id}/state")
    state = r.json()
    if state.get("current_phase") != "exploration":
        _PROBLEMS.append(f"phase after combat should be exploration, got {state.get('current_phase')}")
    if not any("Victory" in line for line in state.get("narrative_history", [])):
        _PROBLEMS.append("victory summary missing from narrative history")


def assertions(transcript: list[TranscriptEntry], summary: dict) -> list[str]:
    problems = list(_PROBLEMS)

    # The connected bot should have observed the combat broadcasts
    types_seen = {
        e.message.get("type")
        for e in transcript
        if e.direction == "recv" and e.bot == BOT_NAME
    }
    if "combat_started" not in types_seen:
        problems.append("bot never received combat_started broadcast")
    if "combat_update" not in types_seen:
        problems.append("bot never received combat_update broadcast")
    return problems
