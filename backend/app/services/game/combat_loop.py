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
import re

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


def format_initiative_summary(state: dict) -> str:
    """One line naming every combatant with the initiative total that placed them.

    The order of `combatants` is the turn order. Totals are the rules-engine
    d20 + Dexterity modifier, not a display placeholder.
    """
    parts: list[str] = []
    for entry in state.get("combatants") or []:
        name = entry.get("name") or "Unknown"
        if entry.get("initiative") is None:
            parts.append(name)
            continue
        total = int(entry.get("initiative") or 0)
        mod = int(entry.get("initiative_modifier") or 0)
        parts.append(f"{name} {total} (d20{mod:+d})")
    if not parts:
        return "Initiative: (none)"
    return "Initiative: " + ", ".join(parts)


_ATTACK_RE = re.compile(
    r"\b(attack|attacks|attacking|shoot|shoots|shooting|fire|fires|firing|"
    r"strike|strikes|striking|swing|swings|swinging|stab|stabs|stabbing|"
    r"slash|slashes|slashing|bow|hit|hits|hitting|cast|casts|casting|spell|spells)\b",
    re.I,
)
_HEAL_RE = re.compile(
    r"\b(potion|potions|heal|heals|healing|drink|drinks|drinking)\b",
    re.I,
)
_DODGE_RE = re.compile(
    r"\b(dodge|dodges|dodging|defend|defends|defending|defense|defensive|"
    r"retreat|retreats|retreating|flee|flees|fleeing|disengage)\b",
    re.I,
)
_DICE_ROLL_RE = re.compile(r"\brolls?\s+d\d+\b", re.I)


# "Thorne takes 14 damage … now at 20 of 34 HP" is a sheet update, not a swing.
# Damage-type words inside that report (slashing, hit) must not start an attack.
_HP_REPORT_RE = re.compile(
    r"\b(?:takes|take|took|suffers|suffered)\s+\d+\s+(?:points of\s+)?damage\b"
    r"|(?:now at|down to)\s+\d+\s+(?:of|/)\s+\d+",
    re.I,
)


def classify_combat_text(text: str) -> str | None:
    """Map a free-text combat message onto the rules engine, or a dice report.

    Returns ``attack``, ``dodge``, ``heal``, ``roll``, or None.
    Attack wording wins over a dice report so "I roll to attack" still attacks.
    An HP report is neither: the sheet update has to reach the character.
    """
    if not text:
        return None
    if _HP_REPORT_RE.search(text):
        return None
    if _ATTACK_RE.search(text):
        return "attack"
    if _HEAL_RE.search(text):
        return "heal"
    if _DODGE_RE.search(text):
        return "dodge"
    if _DICE_ROLL_RE.search(text):
        return "roll"
    return None


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

    summary = format_initiative_summary({"combatants": ordered_entries})
    return {
        "round_number": 1,
        "current_turn_index": 0,
        "initiative_order": [e["name"] for e in ordered_entries],
        "combatants": ordered_entries,
        "log": [summary],
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


def current_combatant(state: dict) -> dict | None:
    """The combatant the initiative index currently points at."""
    entries = state.get("combatants") or []
    if not entries:
        return None
    idx = int(state.get("current_turn_index") or 0)
    if idx < 0 or idx >= len(entries):
        return None
    return entries[idx]


def announce_current_player(state: dict) -> str:
    """Name the player who is up, so a reply never ends on an enemy turn."""
    current = current_combatant(state)
    if current and current.get("is_player"):
        return f"It is now {current['name']}'s turn."
    return ""


def hp_updates_from_state(state: dict) -> list[dict]:
    """Player HP snapshot for phones and the TV party list."""
    updates = []
    for entry in state.get("combatants") or []:
        if not entry.get("is_player"):
            continue
        updates.append({
            "character_id": entry.get("id"),
            "name": entry.get("name"),
            "hp": max(0, int(entry.get("hp") or 0)),
            "max_hp": max(0, int(entry.get("max_hp") or 0)),
        })
    return updates


def _clean_actor_name(raw: str) -> str:
    name = re.sub(r"^(?:the|a|an)\s+", "", (raw or "").strip(), flags=re.I)
    return name.strip(" .\"'")


def _names_match(query: str, full: str) -> bool:
    q = _clean_actor_name(query).lower()
    f = (full or "").strip().lower()
    if not q or not f:
        return False
    if q == f:
        return True
    first = f.split()[0]
    if q == first:
        return True
    if f.startswith(q + " ") or q.startswith(f + " "):
        return True
    return False


def _combatant_named(state: dict, raw: str) -> dict | None:
    """Find a combatant named by narration. Prefer the longest matching name."""
    name = _clean_actor_name(raw)
    if not name:
        return None
    best: dict | None = None
    best_len = 0
    lowered = name.lower()
    for entry in state.get("combatants") or []:
        entry_name = entry.get("name") or ""
        if _names_match(name, entry_name) or (
            entry_name and (entry_name.lower() in lowered or lowered in entry_name.lower())
        ):
            if len(entry_name) > best_len:
                best = entry
                best_len = len(entry_name)
    return best


# "It is now Crimson Fang Legionnaire 1's turn"
_TURN_HANDOFF_RE = re.compile(
    r"(?:it is|it['’]s)\s+(?:now\s+)?(?P<name>.+?)['’]s\s+turn\b",
    re.I,
)
_WHAT_DO_YOU_DO_RE = re.compile(r"\s*what do you do\??", re.I)
_HP_ASK_RE = re.compile(
    r"(?i)[^.?!]*\b(?:what is your|what['’]s your|how much damage|report your|"
    r"tell me your|calculate your|let me know your)\b[^.?!]*"
    r"(?:hp|hit points|damage)[^.?!]*[.?!]?"
)


def narration_assigns_nonplayer(narration: str, state: dict) -> bool:
    """True when the reply puts an enemy or NPC on the spot and waits.

    Only combatants already in the initiative count. An unknown name (a
    villager, a shopkeeper) must not skip the player who is actually up.
    """
    if not narration or not state.get("combatants"):
        return False
    match = _TURN_HANDOFF_RE.search(narration)
    if match:
        found = _combatant_named(state, match.group("name"))
        if found is not None and not found.get("is_player"):
            return True
    ask = _WHAT_DO_YOU_DO_RE.search(narration)
    if not ask:
        return False
    window = narration[max(0, ask.start() - 160):ask.start()].lower()
    for entry in state.get("combatants") or []:
        if entry.get("is_player"):
            continue
        enemy = (entry.get("name") or "").lower()
        if enemy and enemy in window:
            return True
    return False


def resolve_waiting_monster_turn(state: dict, narration: str | None = None) -> dict:
    """Run enemy/NPC turns immediately so combat never waits on the players.

    If narration declares a monster's turn while a player is still marked
    current, that player's turn has ended. Advance, then resolve every
    following non-player until a player is up or the fight is over.
    """
    if narration and narration_assigns_nonplayer(narration, state):
        current = current_combatant(state)
        if current and current.get("is_player"):
            _advance_turn(state)
    current = current_combatant(state)
    if current is None or current.get("is_player"):
        return {"events": [], "combat_over": False, "victory": False}
    return run_pending_monster_turns(state)


def prepare_player_facing_narration(narration: str, state: dict | None) -> str:
    """Drop monster-turn handoffs and requests for the players to report HP.

    The rules engine owns enemy turns and hit points. A reply that asks the
    table to play a legionnaire, or to do the HP math, is rewritten so the
    next player character is named instead.
    """
    if not narration:
        return narration
    state = state or {}
    player_line = announce_current_player(state)
    replaced = False

    def _replace_handoff(match: re.Match) -> str:
        nonlocal replaced
        found = _combatant_named(state, match.group("name"))
        if found is not None and not found.get("is_player"):
            replaced = True
            return player_line
        return match.group(0)

    updated = _TURN_HANDOFF_RE.sub(_replace_handoff, narration)
    if not replaced and player_line and narration_assigns_nonplayer(narration, state):
        updated = _WHAT_DO_YOU_DO_RE.sub(f" {player_line}", updated, count=1)
        replaced = True
    elif replaced:
        updated = _WHAT_DO_YOU_DO_RE.sub("", updated)
    updated = _HP_ASK_RE.sub("", updated)
    updated = re.sub(r"[ \t]{2,}", " ", updated)
    updated = re.sub(r"\s+([.?!])", r"\1", updated)
    return correct_borrowed_advantage(updated.strip(), state)


def combat_prompt_brief(state: dict | None) -> str:
    """Authoritative combat block injected into the DM's context."""
    if not state or not state.get("combatants"):
        return ""
    lines = [
        "## Active combat (rules engine — authoritative)",
        format_initiative_summary(state),
    ]
    current = current_combatant(state)
    if current:
        kind = "player character" if current.get("is_player") else "enemy/NPC"
        lines.append(f"It is {current.get('name', 'someone')}'s turn ({kind}).")
    for entry in state.get("combatants") or []:
        if entry.get("is_player"):
            lines.append(
                f"{entry.get('name', 'Adventurer')} HP {int(entry.get('hp') or 0)}/{int(entry.get('max_hp') or 0)}."
            )
    lines.append(
        "Resolve every enemy and NPC turn yourself in this same reply, then name the next player character. "
        "Do not hand an enemy or NPC turn to the players. "
        "Do not ask players to report their HP; the numbers above are already on the sheet."
    )
    lines.append(
        "Advantage is two fresh d20s for this check; never reuse an earlier roll. "
        "Damage on a hit is a damage roll, and that roll is stated."
    )
    return "\n".join(lines)


# "Thorne takes 7 slashing" is damage even when the word "damage" is absent.
_TAKES_DAMAGE_RE = re.compile(
    r"(?P<name>[A-Z][\w'’\-]*(?:\s+[A-Z][\w'’\-]*)*)\s+"
    r"(?:takes|take|took|suffers|suffered)\s+(?P<amt>\d+)\s+"
    r"(?:points of\s+)?"
    r"(?:damage|(?:slashing|piercing|bludgeoning|lightning|fire|cold|poison|acid|"
    r"necrotic|radiant|thunder|force|psychic)(?:\s+damage)?)\b",
)
_YOU_TAKE_RE = re.compile(
    r"\byou\s+(?:take|took|suffer|suffered)\s+(?P<amt>\d+)\s+(?:points of\s+)?damage\b",
    re.I,
)
_ABS_HP_RE = re.compile(
    r"(?:(?P<name>(?-i:[A-Z])[\w'’\-]*(?:\s+(?-i:[A-Z])[\w'’\-]*)*)\s+)?"
    r"(?:is |are )?(?:now at|down to)\s+(?P<hp>\d+)\s+(?:of|/)\s+(?P<max>\d+)\s*(?:hp|hit points)\b",
    re.I,
)
_YOU_ABS_RE = re.compile(
    r"\byou (?:are|['’]re) (?:now at|down to)\s+(?P<hp>\d+)\s+(?:of|/)\s+(?P<max>\d+)\s*(?:hp|hit points)\b",
    re.I,
)
_DAMAGE_TYPE = (
    r"slashing|piercing|bludgeoning|lightning|fire|cold|poison|acid|"
    r"necrotic|radiant|thunder|force|psychic"
)
# "3 (1d6) lightning" keeps the number and the type with a parenthetical between them.
_TYPED_DAMAGE_RE = re.compile(
    rf"(\d+)\s+(?:\([^)]*\)\s+)?(?:points of\s+)?(?:{_DAMAGE_TYPE})\b",
    re.I,
)
# "using the higher roll of 18 from the previous turn" is not advantage.
_BORROWED_ADVANTAGE_RE = re.compile(
    r"[^.?!]*\b(?:higher|lower)\s+roll\s+of\s+\d+\b[^.?!]*"
    r"\b(?:previous|earlier|prior|last)\b[^.?!]*[.?!]?",
    re.I,
)
_FLAT_DAMAGE_RE = re.compile(
    rf"\b(?P<amt>\d+)\s+(?P<kind>{_DAMAGE_TYPE}|damage)\b",
    re.I,
)
_HIT_TARGET_RE = re.compile(
    r"\b(?:hit|hits|hitting|strikes|strike|wounds|damages|against)\s+"
    r"(?P<name>[A-Z][\w'’\-]*(?:\s+[A-Z][\w'’\-]*)*)",
)
# A narrated fight, as opposed to "it's the innkeeper's turn" at the bar.
_COMBAT_CUE_RE = re.compile(
    r"\b(attack|attacks|hit|hits|damage|wounded|wound|initiative|combat|battle|"
    r"slash|slashing|weapon|hammer|sword|bow|armor|legionnaire|goblin|orc|"
    r"captain|soldier|bandit|creature|monster|enemy|foe|healing|spell)\b",
    re.I,
)


def settle_narrated_monster_turn(
    narration: str,
    characters: list[dict],
    actor_id: str | None = None,
) -> str:
    """Resolve a narrated enemy turn the table was told to play.

    When the DM says it is a non-player's turn and waits — and the reply is
    clearly a fight — roll that creature's attack, state the HP result, and
    name a player character. Party members and quiet social turns are left
    alone. Does not mutate ``characters``; the HP sentence is applied by
    ``apply_hp_text``.
    """
    if not narration or not characters:
        return narration
    match = _TURN_HANDOFF_RE.search(narration)
    if match is None or not _COMBAT_CUE_RE.search(narration):
        return narration
    raw_name = _clean_actor_name(match.group("name"))
    players = [c for c in characters if c.get("name")]
    if any(_names_match(raw_name, c.get("name") or "") for c in players):
        return narration
    target = None
    hit = _HIT_TARGET_RE.search(narration)
    if hit:
        target = _find_entry(players, hit.group("name"))
    if target is None:
        target = _find_entry(players, actor_id=actor_id) or (players[0] if players else None)
    if target is None:
        return narration
    roller = DiceRoller()
    attack = roller.roll("1d20")
    bonus = 4
    total = attack.total + bonus
    ac = int(target.get("ac") or 10)
    max_hp = int(target.get("max_hp") or target.get("hp") or 1)
    if attack.is_fumble or total < ac:
        action = (
            f"{raw_name} attacks {target.get('name')} and misses "
            f"(d20 {attack.rolls[0]}+{bonus} = {total} vs AC {ac})."
        )
    else:
        amount = roller.roll("1d6+2").total
        new_hp = max(0, int(target.get("hp") or 0) - amount)
        action = (
            f"{raw_name} hits {target.get('name')} for {amount} damage "
            f"(d20 {attack.rolls[0]}+{bonus} = {total} vs AC {ac}). "
            f"{target.get('name')} is now at {new_hp} of {max_hp} HP."
        )
    handoff = f"It is now {target.get('name')}'s turn."
    updated = _TURN_HANDOFF_RE.sub(f"{action} {handoff}", narration, count=1)
    updated = _WHAT_DO_YOU_DO_RE.sub("", updated)
    updated = _HP_ASK_RE.sub("", updated)
    updated = re.sub(r"[ \t]{2,}", " ", updated)
    return updated.strip()


def _player_entries(entries: list[dict]) -> list[dict]:
    return [e for e in entries if e.get("is_player", True)]


def _find_entry(entries: list[dict], name: str | None = None, actor_id: str | None = None) -> dict | None:
    players = _player_entries(entries)
    if name:
        matches = [e for e in players if _names_match(name, e.get("name") or "")]
        if len(matches) == 1:
            return matches[0]
    if actor_id:
        for entry in players:
            if entry.get("id") == actor_id:
                return entry
    return None


def _rightmost_player(entries: list[dict], window: str) -> dict | None:
    """The player named latest in ``window``, for '… Thorne … is now at 20'."""
    best: dict | None = None
    best_at = -1
    for entry in _player_entries(entries):
        name = entry.get("name") or ""
        if not name:
            continue
        found_at = -1
        for match in re.finditer(rf"\b{re.escape(name)}\b", window):
            found_at = match.start()
        first = name.split()[0]
        if first and first != name:
            for match in re.finditer(rf"\b{re.escape(first)}\b", window):
                found_at = max(found_at, match.start())
        if found_at >= best_at and found_at >= 0:
            best = entry
            best_at = found_at
    return best


def apply_hp_text(entries: list[dict], text: str, actor_id: str | None = None) -> list[str]:
    """Apply a damage report or an absolute HP statement to player entries.

    Mutates ``entries`` in place. An absolute "now at 20 of 34 HP" wins over
    a damage amount in the same text, so a report cannot be subtracted twice.
    Returns short log lines for each character whose HP changed.
    """
    if not text or not entries:
        return []
    notes: list[str] = []
    consumed: set[str] = set()

    def _set_hp(entry: dict, hp: int, reason: str, reported_max: int | None = None) -> None:
        key = str(entry.get("id") or entry.get("name"))
        if key in consumed:
            return
        if reported_max and int(reported_max) > 0:
            entry["max_hp"] = int(reported_max)
        before = int(entry.get("hp") or 0)
        max_hp = int(entry.get("max_hp") or before or hp)
        hp = max(0, min(max_hp, int(hp))) if max_hp else max(0, int(hp))
        if hp == before:
            consumed.add(key)
            return
        entry["hp"] = hp
        if hp <= 0 and entry.get("is_player"):
            # Unconscious, not dead — death saves still happen on their turn.
            entry["is_alive"] = entry.get("is_alive", True)
        consumed.add(key)
        notes.append(f"{entry.get('name', 'Someone')} {reason} ({hp}/{entry.get('max_hp', hp)} HP).")

    for match in _ABS_HP_RE.finditer(text):
        name = match.group("name")
        # A capitalized name that isn't a player ("The Captain is now at")
        # belongs to that creature. Only an unnamed "is now at" looks backward
        # for the player the sentence is about.
        if name:
            entry = _find_entry(entries, name)
        else:
            window = text[max(0, match.start() - 180):match.start()]
            entry = _rightmost_player(entries, window)
        if entry is not None:
            _set_hp(
                entry,
                int(match.group("hp")),
                f"is now at {match.group('hp')} HP",
                int(match.group("max")),
            )

    for match in _YOU_ABS_RE.finditer(text):
        entry = _find_entry(entries, actor_id=actor_id)
        if entry is not None:
            _set_hp(entry, int(match.group("hp")), f"is now at {match.group('hp')} HP")

    for match in _TAKES_DAMAGE_RE.finditer(text):
        entry = _find_entry(entries, match.group("name"))
        if entry is None:
            continue
        _set_hp(entry, int(entry.get("hp") or 0) - int(match.group("amt")), f"takes {match.group('amt')} damage")

    for match in _YOU_TAKE_RE.finditer(text):
        entry = _find_entry(entries, actor_id=actor_id)
        if entry is not None:
            _set_hp(entry, int(entry.get("hp") or 0) - int(match.group("amt")), f"takes {match.group('amt')} damage")

    typed = [int(n) for n in _TYPED_DAMAGE_RE.findall(text)]
    if typed:
        target = None
        hit = _HIT_TARGET_RE.search(text)
        if hit:
            target = _find_entry(entries, hit.group("name"))
        if target is None and re.search(r"\byou take\b", text, re.I):
            target = _find_entry(entries, actor_id=actor_id)
        if target is not None:
            amount = sum(typed)
            _set_hp(target, int(target.get("hp") or 0) - amount, f"takes {amount} damage")

    return notes


def _player_attack_profile(state: dict | None) -> tuple[int, str]:
    """To-hit bonus and damage dice for the player who is up, else the first player."""
    state = state or {}
    ordered: list[dict] = []
    current = current_combatant(state)
    if current and current.get("is_player"):
        ordered.append(current)
    for entry in state.get("combatants") or []:
        if entry.get("is_player") and entry not in ordered:
            ordered.append(entry)
    for entry in ordered:
        bonus = int(entry.get("attack_bonus") or 0)
        dice = str(entry.get("damage_dice") or "1d6")
        return bonus, dice
    return 0, "1d6"


def _format_dice_roll(label: str, notation: str, result, suffix: str = "") -> str:
    mod = int(getattr(result, "modifier", 0) or 0)
    mod_txt = ""
    if mod:
        mod_txt = f" {'+' if mod > 0 else '-'} {abs(mod)}"
    tail = f" {suffix}" if suffix else ""
    return f"{label} {notation}: {list(result.rolls)}{mod_txt} = {result.total}{tail}."


def correct_borrowed_advantage(narration: str, state: dict | None = None) -> str:
    """Replace an advantage total copied from an earlier roll.

    Advantage rolls two new d20s for this check and keeps the higher. A hit's
    damage is rolled and written into the line. Earlier rolls are not read.
    Narration that does not cite a previous roll is returned unchanged.
    """
    if not narration or _BORROWED_ADVANTAGE_RE.search(narration) is None:
        return narration
    modifier, damage_notation = _player_attack_profile(state)
    kind = "piercing"
    flat = _FLAT_DAMAGE_RE.search(narration)
    if flat and flat.group("kind").lower() != "damage":
        kind = flat.group("kind").lower()
    sneak_die = None
    if re.search(r"sneak attack", narration, re.I):
        mentioned = re.search(
            r"sneak attack(?:\s+\w+){0,6}?\s*(\d+d\d+)",
            narration,
            re.I,
        )
        sneak_die = mentioned.group(1) if mentioned else "2d6"
    roller = DiceRoller()
    first = roller.roll("1d20")
    second = roller.roll("1d20")
    faces = [int(first.rolls[0]), int(second.rolls[0])]
    kept = max(faces)
    total = kept + modifier
    higher = f"using the higher, {kept}"
    if modifier:
        sign = "+" if modifier > 0 else "-"
        higher += f" {sign} {abs(modifier)} = {total}"
    advantage_line = (
        f"Advantage on this check is two fresh d20s ({faces[0]} and {faces[1]}), "
        f"{higher}."
    )
    updated = _BORROWED_ADVANTAGE_RE.sub(advantage_line, narration, count=1)
    clauses = [
        _format_dice_roll("Damage roll", damage_notation, roller.roll(damage_notation), kind),
    ]
    if sneak_die:
        clauses.append(_format_dice_roll("Sneak Attack roll", sneak_die, roller.roll(sneak_die)))
    damage_text = " ".join(clauses)
    if _FLAT_DAMAGE_RE.search(updated):
        updated = _FLAT_DAMAGE_RE.sub(damage_text, updated, count=1)
    elif "damage roll" not in updated.lower():
        updated = f"{updated.rstrip()} {damage_text}"
    updated = re.sub(r"[ \t]{2,}", " ", updated)
    return updated.strip()


def resolve_player_action(
    state: dict,
    actor_id: str,
    action_type: str,
    target_id: str | None = None,
    target_x: int | None = None,
    target_y: int | None = None,
    *,
    spell_name: str | None = None,
    slot_level: int | None = None,
    shove_type: str | None = None,
) -> dict:
    """Apply one player combat action, then auto-run monster turns until the
    next living player's turn (or combat ends). Returns a result dict with
    per-event descriptions; mutates `state` in place.

    ``target_x``, ``target_y``, ``spell_name``, ``slot_level``, and
    ``shove_type`` are accepted so the combat-action route can pass the full
    request body. Movement and named-spell resolution are not handled here;
    attack / dodge / heal / pass are.
    """
    del target_x, target_y, spell_name, slot_level, shove_type
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
    announcement = announce_current_player(state)
    if announcement:
        events.append(announcement)
        _log(state, announcement)
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
