"""Authoritative combat loop — the deterministic rules engine drives combat.

The LLM never computes math here. `start_encounter` builds initiative from
character sheets + monster stats; `resolve_player_action` applies attacks,
healing, and death saves through the RulesEngine; monster turns run
automatically between player turns. The narration layer only describes
outcomes that are already decided.

Combat state is a plain dict stored on the session (JSON column), so it
survives restarts like everything else.
"""
from __future__ import annotations

import random

from app.services.dice import DiceRoller
from app.services.rules.combat import Combatant
from app.services.rules.engine import RulesEngine

# Class → (weapon damage dice, governing ability) for a reasonable default attack
CLASS_WEAPONS: dict[str, tuple[str, str]] = {
    "barbarian": ("1d12", "strength"),
    "fighter": ("1d10", "strength"),
    "paladin": ("1d10", "strength"),
    "cleric": ("1d8", "strength"),
    "druid": ("1d8", "wisdom"),
    "monk": ("1d8", "dexterity"),
    "ranger": ("1d8", "dexterity"),
    "rogue": ("1d8", "dexterity"),
    "bard": ("1d8", "dexterity"),
    "warlock": ("1d10", "charisma"),   # eldritch blast
    "sorcerer": ("1d10", "charisma"),  # fire bolt
    "wizard": ("1d10", "intelligence"),  # fire bolt
}

HEAL_POTION_DICE = "2d4+2"


def _mod(score: int) -> int:
    return (score - 10) // 2


def _prof(level: int) -> int:
    return (max(1, level) - 1) // 4 + 2


def combatant_from_character(char: dict) -> dict:
    """Build a serializable combatant entry from a character record."""
    level = int(char.get("level", 1) or 1)
    dex = int(char.get("dexterity", 10) or 10)
    class_name = (char.get("class_name") or "").lower()
    dice, ability = CLASS_WEAPONS.get(class_name, ("1d8", "strength"))
    ability_score = int(char.get(ability, 10) or 10)
    atk_mod = _mod(ability_score)
    max_hp = int(char.get("max_hp") or char.get("hp") or 8)
    return {
        "id": char["id"],
        "name": char.get("name", "Adventurer"),
        "is_player": True,
        "initiative": 0,
        "initiative_modifier": _mod(dex),
        "hp": int(char.get("hp", max_hp) or max_hp),
        "max_hp": max_hp,
        "ac": int(char.get("ac", 10) or 10),
        "attack_bonus": atk_mod + _prof(level),
        "damage_dice": f"{dice}{atk_mod:+d}" if atk_mod else dice,
        "death_save_successes": 0,
        "death_save_failures": 0,
        "is_alive": True,
        "is_stable": False,
    }


def combatant_from_enemy(name: str, hp: int, ac: int, cr: float, index: int) -> dict:
    """Build a monster combatant with CR-scaled attack profile (SRD-ish)."""
    cr = max(0.0, float(cr or 0))
    attack_bonus = 3 + int(cr // 2)
    dmg_bonus = max(1, int(cr))
    return {
        "id": f"enemy-{index}",
        "name": name,
        "is_player": False,
        "initiative": 0,
        "initiative_modifier": 1,
        "hp": int(hp),
        "max_hp": int(hp),
        "ac": int(ac),
        "cr": cr,
        "attack_bonus": attack_bonus,
        "damage_dice": f"1d6+{dmg_bonus}",
        "death_save_successes": 0,
        "death_save_failures": 0,
        "is_alive": True,
        "is_stable": False,
    }


def _as_combatant(entry: dict) -> Combatant:
    return Combatant(
        id=entry["id"],
        name=entry["name"],
        initiative=entry.get("initiative", 0),
        initiative_modifier=entry.get("initiative_modifier", 0),
        hp=entry["hp"],
        max_hp=entry["max_hp"],
        ac=entry["ac"],
        death_save_successes=entry.get("death_save_successes", 0),
        death_save_failures=entry.get("death_save_failures", 0),
        is_alive=entry.get("is_alive", True),
        is_stable=entry.get("is_stable", False),
    )


def _sync_back(entry: dict, c: Combatant) -> None:
    entry["hp"] = c.hp
    entry["death_save_successes"] = c.death_save_successes
    entry["death_save_failures"] = c.death_save_failures
    entry["is_alive"] = c.is_alive
    entry["is_stable"] = c.is_stable


def start_encounter(characters: list[dict], enemies: list[dict]) -> dict:
    """Roll initiative and build the full combat state.

    Args:
        characters: character records (dicts from the repository)
        enemies: [{"name", "hp", "ac", "cr", "count"}] e.g. from /encounter
    """
    engine = RulesEngine(DiceRoller())
    entries: list[dict] = [combatant_from_character(c) for c in characters]
    idx = 0
    for enemy in enemies:
        for _ in range(max(1, int(enemy.get("count", 1) or 1))):
            idx += 1
            e = combatant_from_enemy(
                enemy.get("name", "Monster"),
                enemy.get("hp", 10),
                enemy.get("ac", 12),
                enemy.get("cr", 0.25),
                idx,
            )
            # Number duplicate monsters for the initiative display
            dupes = [x for x in entries if not x["is_player"] and x["name"].startswith(e["name"])]
            if dupes:
                e["name"] = f"{e['name']} {len(dupes) + 1}"
            entries.append(e)

    ordered = engine.start_combat(entries)
    by_id = {e["id"]: e for e in entries}
    for c in ordered:
        by_id[c.id]["initiative"] = c.initiative
    ordered_entries = [by_id[c.id] for c in ordered]

    return {
        "round_number": 1,
        "current_turn_index": 0,
        "initiative_order": [e["name"] for e in ordered_entries],
        "combatants": ordered_entries,
        "log": [],
    }


def _alive(entries: list[dict]) -> list[dict]:
    return [e for e in entries if e.get("is_alive", True) and e["hp"] > 0]


def combat_over(state: dict) -> tuple[bool, bool]:
    """Return (over, players_won). Unconscious-but-alive players are still
    in the fight — they roll death saves — so defeat requires actual death."""
    entries = state.get("combatants", [])
    monsters_alive = [e for e in _alive(entries) if not e["is_player"]]
    players_in_fight = [e for e in entries if e["is_player"] and e.get("is_alive", True)]
    if not monsters_alive:
        return True, True
    if not players_in_fight:
        return True, False
    return False, False


def _advance_turn(state: dict) -> None:
    entries = state.get("combatants", [])
    if not entries:
        return
    n = len(entries)
    for _ in range(n):
        state["current_turn_index"] = (state.get("current_turn_index", 0) + 1) % n
        if state["current_turn_index"] == 0:
            state["round_number"] = state.get("round_number", 1) + 1
        current = entries[state["current_turn_index"]]
        # Skip the dead; unconscious players still get a turn (death save)
        if current.get("is_alive", True) and (current["hp"] > 0 or current["is_player"]):
            return


def _log(state: dict, text: str) -> None:
    state.setdefault("log", []).append(text)
    state["log"] = state["log"][-50:]


def _run_monster_turns(state: dict, engine: RulesEngine, events: list[str]) -> tuple[bool, bool]:
    """Auto-run monster turns until a living player is up or combat ends.

    Returns (over, victory)."""
    entries = state.get("combatants", [])
    guard = 0
    over, victory = combat_over(state)
    while not over and guard < 20:
        guard += 1
        current = entries[state["current_turn_index"]]
        if current["is_player"]:
            break
        if not current.get("is_alive", True) or current["hp"] <= 0:
            _advance_turn(state)
            continue
        targets = [e for e in _alive(entries) if e["is_player"]]
        if not targets:
            # No conscious player to attack — skip to the next combatant
            _advance_turn(state)
            continue
        target = random.choice(targets)
        m, t = _as_combatant(current), _as_combatant(target)
        result = engine.resolve_attack(
            m, t, current.get("attack_bonus", 3), current.get("damage_dice", "1d6+1")
        )
        desc = result.description.replace(m.id, current["name"]).replace(t.id, target["name"])
        if result.success and result.damage_dealt:
            engine.apply_damage(t, result.damage_dealt)
            if t.hp <= 0:
                desc += f" {target['name']} falls unconscious!"
        _sync_back(target, t)
        _log(state, desc)
        events.append(desc)
        over, victory = combat_over(state)
        if over:
            break
        _advance_turn(state)
    return over, victory


def run_pending_monster_turns(state: dict) -> dict:
    """Run monster turns at the top of combat (or any point where no player
    input is possible). Without this, a monster winning initiative deadlocks
    the fight: phones only enable actions on a player's turn, and monster
    turns otherwise run only inside resolve_player_action.

    Returns {"events": [...], "combat_over": bool, "victory": bool}."""
    engine = RulesEngine(DiceRoller())
    events: list[str] = []
    over, victory = _run_monster_turns(state, engine, events)
    return {"events": events, "combat_over": over, "victory": victory}


def resolve_player_action(
    state: dict,
    actor_id: str,
    action_type: str,
    target_id: str | None = None,
) -> dict:
    """Apply one player combat action, then auto-run monster turns until the
    next living player's turn (or combat ends). Returns a result dict with
    per-event descriptions; mutates `state` in place."""
    engine = RulesEngine(DiceRoller())
    entries = state.get("combatants", [])
    by_id = {e["id"]: e for e in entries}
    actor = by_id.get(actor_id)
    if actor is None:
        return {"error": f"Unknown combatant: {actor_id}", "events": []}
    if not actor["is_player"]:
        return {"error": "Only player combatants can act via this endpoint", "events": []}

    events: list[str] = []

    # If monsters won initiative, their turns run first
    pre_over, pre_victory = _run_monster_turns(state, engine, events)
    if pre_over:
        return _finish(state, entries, events, pre_victory)

    current = entries[state.get("current_turn_index", 0)] if entries else None
    if current is None or current["id"] != actor_id:
        name = current["name"] if current else "anyone"
        return {"error": f"It is not {actor['name']}'s turn (current: {name})", "events": events}

    # Unconscious players roll death saves instead of acting
    if actor["hp"] <= 0 and actor.get("is_alive", True) and not actor.get("is_stable"):
        c = _as_combatant(actor)
        result = engine.process_death_save(c)
        _sync_back(actor, c)
        events.append(f"{actor['name']}: {result.description}")
    elif action_type == "attack":
        target = by_id.get(target_id or "")
        if target is None or target["is_player"] or target["hp"] <= 0:
            # Pick the first living monster if the target is invalid
            monsters = [e for e in _alive(entries) if not e["is_player"]]
            if not monsters:
                return {"error": "No valid target", "events": []}
            target = monsters[0]
        a, t = _as_combatant(actor), _as_combatant(target)
        result = engine.resolve_attack(
            a, t, actor.get("attack_bonus", 2), actor.get("damage_dice", "1d8")
        )
        desc = result.description.replace(a.id, actor["name"]).replace(t.id, target["name"])
        if result.success and result.damage_dealt:
            engine.apply_damage(t, result.damage_dealt)
            if t.hp <= 0:
                t.is_alive = False
                desc += f" {target['name']} falls!"
        _sync_back(target, t)
        events.append(desc)
    elif action_type == "heal":
        target = by_id.get(target_id or actor_id) or actor
        t = _as_combatant(target)
        healed = engine.heal_target(t, DiceRoller().roll(HEAL_POTION_DICE).total)
        if t.hp > 0 and target["hp"] <= 0:
            t.is_alive = True
            t.is_stable = False
        _sync_back(target, t)
        events.append(f"{actor['name']} heals {target['name']} for {healed} HP ({t.hp}/{t.max_hp}).")
    elif action_type in ("dodge", "pass"):
        events.append(f"{actor['name']} takes a defensive stance.")
    else:
        return {"error": f"Unknown action_type: {action_type}", "events": []}

    # Monster pre-turn events are logged inside _run_monster_turns;
    # the player action contributes exactly one new event (the last one).
    if events:
        _log(state, events[-1])

    over, victory = combat_over(state)
    if not over:
        _advance_turn(state)
        over, victory = _run_monster_turns(state, engine, events)

    if over:
        return _finish(state, entries, events, victory)

    next_up = entries[state["current_turn_index"]]["name"]
    return {"events": events, "combat_over": False, "victory": False, "next_turn": next_up}


def _finish(state: dict, entries: list[dict], events: list[str], victory: bool) -> dict:
    xp = sum(int(float(e.get("cr", 0)) * 100) for e in entries if not e["is_player"]) if victory else 0
    summary = (
        f"Victory! The enemies are defeated. The party earns {xp} XP."
        if victory else "The party has fallen..."
    )
    _log(state, summary)
    events.append(summary)
    return {
        "events": events,
        "combat_over": True,
        "victory": victory,
        "xp_awarded": xp,
    }
