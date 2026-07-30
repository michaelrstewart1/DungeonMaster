"""Campaign memory service — the AI DM's long-term memory.

Two halves:

* **Extraction** (write path): after each turn, an LLM pass distills the
  narration into canonical facts, quest updates, NPC sightings, and
  locations. Runs fire-and-forget so it never adds latency to play.
* **Retrieval** (read path): before narrating, the most relevant memory
  entries are selected by keyword/entity overlap with the player's action
  and recent scene, and rendered as a compact context block.

Deterministic code owns the memory structures; the LLM only proposes
facts, which are merged conservatively (no deletions, capped sizes).
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

MAX_EVENTS = 300
MAX_NPCS = 100
MAX_LOCATIONS = 60
MAX_QUESTS = 40

_STOPWORDS = frozenset(
    "the a an and or but if then of to in on at for with from by is are was "
    "were be been being i you he she it we they my your his her its our their "
    "this that these those as not no do does did done have has had will would "
    "can could should must may might there here what who whom which when where "
    "why how all any some each into out up down over under again very just "
    "say says said go goes went get gets got make makes made take takes took".split()
)

EXTRACTION_PROMPT = """You are the memory-keeper for a D&D campaign. From the exchange below, extract durable facts worth remembering for future sessions. Respond with ONLY a JSON object (no prose, no markdown fences) in this exact shape:
{
  "events": ["short canonical fact", ...],
  "quests": [{"title": "...", "status": "active|completed|failed", "notes": "..."}],
  "npcs": [{"name": "...", "npc_type": "...", "disposition": "friendly|neutral|hostile|unknown", "location": "...", "notes": "...", "alive": true}],
  "locations": [{"name": "...", "description": "..."}]
}
Rules:
- Only include things that MATTER later: named NPCs, promises made, items gained/lost, deaths, discoveries, quest progress, places visited.
- Events must be short, past-tense, third-person facts ("The party agreed to escort Mira to Duskhollow").
- Omit any array that has nothing worth recording. Return {} if nothing is memorable.
"""


def _tokenize(text: str) -> set[str]:
    return {
        w for w in re.findall(r"[a-z']+", text.lower())
        if len(w) > 2 and w not in _STOPWORDS
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Retrieval — build a compact memory block for the narrator prompt
# ---------------------------------------------------------------------------

def build_memory_context(
    memory: dict,
    player_action: str,
    recent_narrative: list[str] | None = None,
    max_events: int = 8,
    max_npcs: int = 6,
) -> str:
    """Render the most relevant memory as a prompt block.

    Active quests are always included (they anchor the plot); events and
    NPCs are ranked by keyword overlap with the player's action + recent
    scene, with recency as a tie-breaker.
    """
    if not memory:
        return ""

    query_tokens = _tokenize(player_action)
    for entry in (recent_narrative or [])[-4:]:
        query_tokens |= _tokenize(entry)

    sections: list[str] = []

    # Quests: all active ones, most recent first
    quests = [q for q in memory.get("quests", []) if q.get("status") == "active"]
    if quests:
        lines = [f"- {q.get('title', '')}" + (f" — {q['notes']}" if q.get("notes") else "") for q in quests[-MAX_QUESTS:]]
        sections.append("ACTIVE QUESTS:\n" + "\n".join(lines))

    # Events: rank by relevance, keep chronological order in output
    events = memory.get("events", [])
    if events:
        scored = []
        for idx, ev in enumerate(events):
            fact = ev.get("fact", "") if isinstance(ev, dict) else str(ev)
            overlap = len(query_tokens & _tokenize(fact))
            scored.append((overlap, idx, fact))
        # Relevant events first; always include the last few for recency
        relevant = [s for s in scored if s[0] > 0]
        relevant.sort(key=lambda s: (-s[0], -s[1]))
        chosen = {idx for _, idx, _ in relevant[:max_events]}
        chosen |= {s[1] for s in scored[-3:]}  # last 3 facts always in
        picked = [scored[i][2] for i in sorted(chosen)][-max_events:]
        if picked:
            sections.append("ESTABLISHED FACTS (canon — never contradict):\n" + "\n".join(f"- {f}" for f in picked))

    # NPCs: mentioned by name first, then most recently seen
    npcs = memory.get("npcs", [])
    if npcs:
        def npc_score(n: dict) -> int:
            return 100 if _tokenize(n.get("name", "")) & query_tokens else 0
        ranked = sorted(enumerate(npcs), key=lambda p: (-npc_score(p[1]), -p[0]))
        picked_npcs = [n for _, n in ranked[:max_npcs]]
        lines = []
        for n in picked_npcs:
            bits = [n.get("name", "?")]
            if n.get("npc_type"):
                bits.append(f"({n['npc_type']})")
            if not n.get("alive", True):
                bits.append("[DEAD]")
            if n.get("disposition") and n["disposition"] != "unknown":
                bits.append(f"disposition: {n['disposition']}")
            if n.get("location"):
                bits.append(f"last seen: {n['location']}")
            if n.get("notes"):
                bits.append(f"— {n['notes']}")
            lines.append("- " + " ".join(bits))
        sections.append("KNOWN NPCS (keep names, personalities, and status consistent):\n" + "\n".join(lines))

    # Locations only when referenced
    locations = memory.get("locations", [])
    loc_lines = [
        f"- {loc.get('name', '')}: {loc.get('description', '')}"
        for loc in locations
        if _tokenize(loc.get("name", "")) & query_tokens
    ]
    if loc_lines:
        sections.append("KNOWN LOCATIONS:\n" + "\n".join(loc_lines[:4]))

    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# Extraction — distill a turn into memory updates (LLM-assisted)
# ---------------------------------------------------------------------------

def _parse_extraction(raw: str) -> dict:
    """Parse the LLM's JSON reply, tolerating markdown fences and prose."""
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\s*|\s*```$", "", text, flags=re.IGNORECASE)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {}
    try:
        data = json.loads(match.group(0))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, ValueError):
        return {}


def merge_extraction(memory: dict, extracted: dict, session_id: str, turn: int) -> dict:
    """Merge extracted facts into campaign memory. Additive and capped —
    the LLM can propose, never erase."""
    stamp = _now()

    for fact in extracted.get("events", []) or []:
        if not isinstance(fact, str) or not fact.strip():
            continue
        fact = fact.strip()
        existing = {e.get("fact", "").lower() for e in memory["events"]}
        if fact.lower() in existing:
            continue
        memory["events"].append({
            "fact": fact,
            "session_id": session_id,
            "turn": turn,
            "timestamp": stamp,
        })
    memory["events"] = memory["events"][-MAX_EVENTS:]

    for quest in extracted.get("quests", []) or []:
        if not isinstance(quest, dict) or not quest.get("title"):
            continue
        title_l = quest["title"].strip().lower()
        match = next((q for q in memory["quests"] if q.get("title", "").lower() == title_l), None)
        if match:
            if quest.get("status") in ("active", "completed", "failed"):
                match["status"] = quest["status"]
            if quest.get("notes"):
                match["notes"] = quest["notes"]
            match["updated_at"] = stamp
        else:
            memory["quests"].append({
                "title": quest["title"].strip(),
                "status": quest.get("status", "active"),
                "notes": quest.get("notes", ""),
                "updated_at": stamp,
            })
    memory["quests"] = memory["quests"][-MAX_QUESTS:]

    for npc in extracted.get("npcs", []) or []:
        if not isinstance(npc, dict) or not npc.get("name"):
            continue
        name_l = npc["name"].strip().lower()
        match = next((n for n in memory["npcs"] if n.get("name", "").lower() == name_l), None)
        if match:
            for key in ("npc_type", "disposition", "location", "notes"):
                if npc.get(key):
                    match[key] = npc[key]
            if npc.get("alive") is False:
                match["alive"] = False
            match["last_seen_session"] = session_id
        else:
            memory["npcs"].append({
                "name": npc["name"].strip(),
                "npc_type": npc.get("npc_type", ""),
                "disposition": npc.get("disposition", "unknown"),
                "location": npc.get("location", ""),
                "notes": npc.get("notes", ""),
                "alive": npc.get("alive", True) is not False,
                "last_seen_session": session_id,
            })
    memory["npcs"] = memory["npcs"][-MAX_NPCS:]

    for loc in extracted.get("locations", []) or []:
        if not isinstance(loc, dict) or not loc.get("name"):
            continue
        name_l = loc["name"].strip().lower()
        match = next((x for x in memory["locations"] if x.get("name", "").lower() == name_l), None)
        if match:
            if loc.get("description"):
                match["description"] = loc["description"]
            match["visited"] = True
        else:
            memory["locations"].append({
                "name": loc["name"].strip(),
                "description": loc.get("description", ""),
                "visited": True,
            })
    memory["locations"] = memory["locations"][-MAX_LOCATIONS:]

    return memory


async def extract_turn_facts(llm, player_action: str, narration: str) -> dict:
    """Ask the LLM to distill this turn into memory updates.

    Returns {} on any failure — memory extraction must never break play.
    """
    from app.services.llm.base import LLMMessage

    try:
        response = await llm.generate(
            messages=[LLMMessage(
                role="user",
                content=f"Player: {player_action}\n\nDM narration: {narration}",
            )],
            system_prompt=EXTRACTION_PROMPT,
            temperature=0.1,
            max_tokens=400,
        )
        return _parse_extraction(response.content)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Memory extraction failed: %s", exc)
        return {}


async def record_turn(db_factory, llm, campaign_id: str, session_id: str,
                      turn: int, player_action: str, narration: str) -> None:
    """Full write path: extract facts and persist them. Designed to run as
    a fire-and-forget task after the turn response is already sent."""
    from app import repository as repo

    extracted = await extract_turn_facts(llm, player_action, narration)
    if not extracted or not any(extracted.get(k) for k in ("events", "quests", "npcs", "locations")):
        return
    try:
        async with db_factory() as db:
            memory = await repo.get_campaign_memory(db, campaign_id)
            merge_extraction(memory, extracted, session_id, turn)
            await repo.save_campaign_memory(db, memory)
            await db.commit()
        logger.info(
            "Campaign memory updated (campaign=%s: +%d events, %d quests, %d npcs)",
            campaign_id, len(extracted.get("events", []) or []),
            len(extracted.get("quests", []) or []), len(extracted.get("npcs", []) or []),
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Failed to persist campaign memory: %s", exc)
