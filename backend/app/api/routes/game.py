"""Game session management endpoints."""
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import base64
import hashlib
import logging
import os
import random
import re
import urllib.parse

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import GameStateResponse, CombatState
from app.models.enums import GamePhase
from app.api import storage
from app.config import settings
from app.db import get_db
import app.repository as repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/game", tags=["game"])

# Strong references to fire-and-forget narration tasks (asyncio only keeps
# weak refs, so untracked tasks can be garbage-collected mid-flight).
_background_tasks: set = set()


class GameSessionCreate(BaseModel):
    """Schema for creating a game session."""
    campaign_id: str = Field(..., description="Campaign ID for this session")
    current_phase: str = Field(default="exploration", description="Initial game phase")
    current_scene: str = Field(default="", description="Initial scene — left blank so the DM sets it from the story bible")


class PlayerActionRequest(BaseModel):
    """Schema for submitting a player action. Accepts both frontend and legacy formats."""
    type: str = Field(default="interact", description="Action type")
    message: Optional[str] = Field(default=None, description="Action message from chat")
    # Legacy fields (kept for backward compat with tests)
    character_id: Optional[str] = Field(default=None, description="Character ID")
    action: Optional[str] = Field(default=None, description="Action description")

    @property
    def resolved_action(self) -> str:
        """Get the action text regardless of which field was used."""
        return self.message or self.action or "looks around"


class PlayerActionResponse(BaseModel):
    """Response to a player action."""
    narration: str = Field(..., description="DM narration in response to the action")
    turn_number: int = Field(default=1, description="Current turn number")
    phase: str = Field(default="exploration", description="Current game phase")
    # Metadata for frontend effects
    mood: Optional[str] = Field(default=None, description="Scene mood after this action")
    effects: List[str] = Field(default_factory=list, description="Suggested screen effects: nat20, damage, spell, levelup, boss")
    # Environment & scene sync
    environment: Optional[Dict[str, str]] = Field(default=None, description="Current environment state (time_of_day, weather, etc.)")
    detected_scene: Optional[str] = Field(default=None, description="Detected scene type: tavern, dungeon, forest, etc.")
    # NPC auto-detection
    detected_npcs: List[Dict[str, str]] = Field(default_factory=list, description="NPCs detected in narration [{name, npc_type}]")
    hp_updates: List[Dict[str, object]] = Field(default_factory=list, description="Player HP after this turn")


class WorldGenerateRequest(BaseModel):
    """Schema for world generation."""
    campaign_id: str = Field(..., description="Campaign to store the world in")
    theme: str = Field(default="dark_fantasy", description="Narrative tone")
    setting: str = Field(default="", description="Brief setting description")
    hooks: list[str] = Field(default_factory=list, description="Story hooks / major threats")


class SessionSummaryRequest(BaseModel):
    """Schema for saving a session summary."""
    summary: Optional[str] = Field(default=None, description="Pre-written summary (optional)")


class EnvironmentData(BaseModel):
    """Schema for environment tracking (weather, time of day, etc.)."""
    time_of_day: str = Field(default="dawn", description="dawn, morning, noon, afternoon, dusk, evening, night, midnight")
    weather: str = Field(default="clear", description="clear, cloudy, rain, storm, snow, fog, wind")
    temperature: str = Field(default="mild", description="freezing, cold, cool, mild, warm, hot")
    season: str = Field(default="spring", description="spring, summer, autumn, winter")


# ─── World Navigation (macro travel between scenes) ─────────────────────
#
# The world map is a deterministic location graph stored on the session.
# Travel is rules-engine code: the server validates connectivity, moves the
# party, reveals neighbors, and updates the scene. The LLM only narrates
# the journey afterwards — it can never decide where the party is.

DEFAULT_WORLD_LOCATIONS: list[dict] = [
    {
        "id": "crossroads-village",
        "name": "Crossroads Village",
        "description": "A weathered village where trade roads meet. Smoke curls from the tavern chimney and rumors travel faster than carts.",
        "scene_type": "village",
        "connections": ["darkwood-forest", "mountain-pass"],
    },
    {
        "id": "darkwood-forest",
        "name": "The Darkwood",
        "description": "Ancient trees crowd out the sun. Things rustle in the undergrowth that are not deer.",
        "scene_type": "forest",
        "connections": ["crossroads-village", "hollow-cave"],
    },
    {
        "id": "mountain-pass",
        "name": "Windscar Pass",
        "description": "A narrow trail hugging the cliffside. The wind howls warnings to those who climb.",
        "scene_type": "mountain",
        "connections": ["crossroads-village", "ruined-temple"],
    },
    {
        "id": "hollow-cave",
        "name": "The Hollow Cave",
        "description": "A yawning cave mouth exhales cold, stale air. Scratch marks line the entrance stone.",
        "scene_type": "cave",
        "connections": ["darkwood-forest", "forgotten-depths"],
    },
    {
        "id": "ruined-temple",
        "name": "Ruined Temple of the Old Gods",
        "description": "Shattered columns and a defaced altar. Whatever was worshipped here did not leave willingly.",
        "scene_type": "temple",
        "connections": ["mountain-pass", "forgotten-depths"],
    },
    {
        "id": "forgotten-depths",
        "name": "The Forgotten Depths",
        "description": "A dungeon older than any map. The darkness below has weight, and it is watching.",
        "scene_type": "dungeon",
        "connections": ["hollow-cave", "ruined-temple"],
    },
]


def _build_world_locations(campaign: dict | None) -> tuple[list[dict], str | None]:
    """Build the session's world map from the campaign (or the default graph).

    Returns (locations, starting_location_id). The first location is the
    start: it is visited, and its neighbors are discovered.
    """
    raw = None
    if campaign:
        ws = campaign.get("world_state") or {}
        if isinstance(ws, dict):
            raw = ws.get("locations")
    source = raw if isinstance(raw, list) and raw else DEFAULT_WORLD_LOCATIONS

    locations: list[dict] = []
    for loc in source:
        if not isinstance(loc, dict) or not loc.get("id") or not loc.get("name"):
            continue
        locations.append({
            "id": str(loc["id"]),
            "name": str(loc["name"]),
            "description": str(loc.get("description", "")),
            "scene_type": str(loc.get("scene_type", "road")),
            "connections": [str(c) for c in (loc.get("connections") or [])],
            "discovered": False,
            "visited": False,
        })
    if not locations:
        return [], None

    start = locations[0]
    start["discovered"] = True
    start["visited"] = True
    by_id = {loc["id"]: loc for loc in locations}
    for neighbor_id in start["connections"]:
        if neighbor_id in by_id:
            by_id[neighbor_id]["discovered"] = True
    return locations, start["id"]


@router.post("/sessions", status_code=status.HTTP_201_CREATED, response_model=GameStateResponse)
async def create_game_session(session_create: GameSessionCreate, db: AsyncSession = Depends(get_db)) -> GameStateResponse:
    """Create a new game session for a campaign."""
    campaign = await repo.get_campaign(db, session_create.campaign_id)
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    
    session_id = storage.generate_id()

    world_locations, starting_location = _build_world_locations(campaign)

    session_data = {
        "id": session_id,
        "campaign_id": session_create.campaign_id,
        "current_phase": session_create.current_phase,
        "current_scene": session_create.current_scene,
        "narrative_history": [session_create.current_scene],
        "combat_state": None,
        "active_effects": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "turn_count": 0,
        "current_location": starting_location,
        "world_locations": world_locations,
        "environment": {
            "time_of_day": "dawn",
            "weather": "clear",
            "temperature": "cool",
            "season": "spring",
        },
    }
    
    # Auto-generate a room code for multiplayer join
    room_code = storage.generate_room_code()
    storage.room_codes[room_code] = session_id
    session_data["room_code"] = room_code
    storage.session_players[session_id] = []
    storage.flush("room_codes", "session_players")

    # Persist including room_code so the session is resumable after restart
    await repo.save_game_session(db, session_data)

    return GameStateResponse(**session_data)


@router.get("/sessions")
async def list_game_sessions(campaign_id: str | None = None, db: AsyncSession = Depends(get_db)) -> list[dict]:
    """List game sessions, optionally filtered by campaign_id."""
    all_sessions = await repo.list_game_sessions(db)
    sessions = []
    for sdata in all_sessions:
        if campaign_id and sdata.get("campaign_id") != campaign_id:
            continue
        sessions.append({
            "id": sdata["id"],
            "campaign_id": sdata.get("campaign_id", ""),
            "phase": sdata.get("current_phase", "exploration"),
            "turn_count": sdata.get("turn_count", 0),
            "created_at": sdata.get("created_at", ""),
            "scene": sdata.get("current_scene", "")[:120],
            "room_code": sdata.get("room_code"),
        })
    sessions.sort(key=lambda s: s.get("created_at", ""), reverse=True)
    return sessions


@router.get("/sessions/{session_id}/state", response_model=GameStateResponse)
async def get_game_state(
    session_id: str, response: Response, db: AsyncSession = Depends(get_db)
) -> GameStateResponse:
    """Get the current game state for a session.

    ``Cache-Control: no-store`` is required. A phone that reconnects and
    refetches this URL used to replay a cached earlier combat while the TV,
    which never refetched, stayed on the live scene.
    """
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")
    response.headers["Cache-Control"] = "no-store"
    return GameStateResponse(**session)


@router.get("/sessions/{session_id}/resume")
async def resume_game_session(session_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    """Resume a saved session: restore its room code mapping and return
    everything a client needs to pick up where the table left off."""
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")

    # Re-register the room code so players can rejoin after a restart.
    # Never steal a code that already points at a different live session —
    # that sent a rejoining phone into an older combat while the TV stayed
    # on the current one.
    room_code = session.get("room_code")
    if not room_code:
        room_code = storage.generate_room_code()
        session["room_code"] = room_code
        await repo.save_game_session(db, session)
    mapped = storage.room_codes.get(room_code)
    if mapped and mapped != session_id:
        room_code = storage.generate_room_code()
        session["room_code"] = room_code
        await repo.save_game_session(db, session)
        mapped = None
    if mapped != session_id:
        storage.room_codes[room_code] = session_id
        storage.flush("room_codes")
    # Next night: one row per player, and last night's heroes are free until
    # someone at the table claims them again.
    from app.api.roster import prepare_rejoin_roster, visible_players

    prepare_rejoin_roster(session_id)

    history = session.get("narrative_history") or []
    return {
        "session": session,
        "room_code": room_code,
        "players": visible_players(session_id),
        "recent_narrative": history[-10:],
    }


def _latest_dm_line(session: dict) -> str:
    """Last DM line already stored on the session, else the current scene."""
    history = session.get("narrative_history") or []
    for line in reversed(history):
        text = str(line)
        if text.startswith("DM: "):
            return text[4:]
    return str(session.get("current_scene") or "")


@router.post("/sessions/{session_id}/action", response_model=PlayerActionResponse)
async def submit_player_action(
    request: Request,
    session_id: str,
    action: PlayerActionRequest,
    db: AsyncSession = Depends(get_db),
) -> PlayerActionResponse:
    """Submit a player action to the game."""
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")
    
    player_text = action.resolved_action
    turn_number = len(session["narrative_history"])
    baseline = repo.session_version(session)

    # Try real LLM narrator; fall back to keyword mock when no API key is set.
    # The prompt may use the snapshot we just read. The write below reloads
    # on a fresh session so a slow reply cannot persist that snapshot over a
    # scene the table has already moved on from.
    narrator = getattr(request.app.state, "narrator", None)
    narration = await _generate_dm_response(player_text, session, narrator, db)

    async def _apply_turn(write_db: AsyncSession) -> tuple[str, dict, str, list, list, str | None, list]:
        fresh = await repo.get_game_session(write_db, session_id)
        if fresh is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")
        if repo.session_version(fresh) != baseline:
            return ("stale", fresh, _latest_dm_line(fresh), [], [], None, [])
        settled, hp_updates = await _settle_narrated_turn(
            write_db, fresh, player_text, narration, action.character_id,
        )
        fresh.setdefault("narrative_history", []).append(f"Player: {player_text}")
        fresh["narrative_history"].append(f"DM: {settled}")
        fresh["turn_count"] = fresh.get("turn_count", 0) + 1
        effects = _detect_effects(settled, player_text)
        _advance_time(fresh)
        detected_npcs = _extract_npcs_from_narration(settled)
        _merge_detected_npcs(fresh, detected_npcs)
        detected_scene = _detect_scene_type(settled)
        if detected_scene:
            fresh["detected_scene"] = detected_scene
        saved = await repo.save_game_session(write_db, fresh)
        if not saved.applied:
            return ("stale", saved, _latest_dm_line(saved), [], [], None, [])
        await write_db.commit()
        return ("ok", saved, settled, hp_updates, effects, detected_scene, detected_npcs)

    db_factory = getattr(request.app.state, "db_factory", None)
    if db_factory is not None:
        async with db_factory() as write_db:
            outcome = await _apply_turn(write_db)
    else:
        outcome = await _apply_turn(db)

    kind, session, narration, hp_updates, effects, detected_scene, detected_npcs = outcome
    if kind == "stale":
        return PlayerActionResponse(
            narration=narration,
            turn_number=len(session.get("narrative_history") or []),
            phase=session.get("current_phase") or "exploration",
            environment=session.get("environment"),
            hp_updates=[],
        )

    mood_obj = _detect_mood(f"{session.get('current_scene', '')} {narration}")

    # Animate the DM avatar on the TV display for this narration
    from app.api.routes.avatar import trigger_speaking
    trigger_speaking(session_id, narration)

    # Long-term memory: distill this turn into canonical facts in the
    # background (never blocks the player's response).
    if narrator is not None:
        import asyncio as _asyncio
        db_factory = getattr(request.app.state, "db_factory", None)
        llm = getattr(narrator, "_llm", None)
        if db_factory is not None and llm is not None:
            from app.services.game.memory import record_turn
            from app.services.game.summarizer import maybe_roll_up
            _asyncio.create_task(record_turn(
                db_factory, llm,
                campaign_id=session.get("campaign_id", ""),
                session_id=session_id,
                turn=turn_number,
                player_action=player_text,
                narration=narration,
            ))
            # Rolling summarization keeps long-campaign context bounded
            _asyncio.create_task(maybe_roll_up(db_factory, llm, session_id))

    if hp_updates:
        from app.api.websockets.game_ws import manager
        await manager.broadcast(session_id, {
            "type": "combat_update",
            "hp_updates": hp_updates,
            "events": [],
            "narration": "",
            "phase": session.get("current_phase"),
            "combat_state": session.get("combat_state"),
        })

    return PlayerActionResponse(
        narration=narration,
        turn_number=turn_number,
        phase=session["current_phase"],
        mood=mood_obj.atmosphere,
        effects=effects,
        environment=session.get("environment"),
        detected_scene=detected_scene,
        detected_npcs=detected_npcs,
        hp_updates=hp_updates,
    )


# ─── World Travel ────────────────────────────────────────────────────────


class TravelRequest(BaseModel):
    """Schema for traveling to another world location."""
    destination_id: str = Field(..., description="ID of the destination location")


@router.get("/sessions/{session_id}/world-map")
async def get_world_map(session_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    """Get the world location graph and the party's current location."""
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")
    return {
        "current_location": session.get("current_location"),
        "locations": session.get("world_locations") or [],
    }


@router.post("/sessions/{session_id}/travel")
async def travel_to_location(
    request: Request,
    session_id: str,
    body: TravelRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Move the party to a connected world location.

    Travel is deterministic rules-engine code: connectivity is validated
    here, the scene changes here, and neighbors are revealed here. The LLM
    only narrates the journey afterwards.
    """
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")

    if session.get("current_phase") == "combat":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="The party cannot travel during combat")

    locations = session.get("world_locations") or []
    by_id = {loc["id"]: loc for loc in locations}
    if not by_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This session has no world map")

    destination = by_id.get(body.destination_id)
    if destination is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown destination")

    current_id = session.get("current_location")
    current = by_id.get(current_id) if current_id else None
    if current_id == body.destination_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The party is already there")
    if current is not None and body.destination_id not in (current.get("connections") or []):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{destination['name']} is not reachable from {current['name']}",
        )

    # Deterministic world update
    session["current_location"] = destination["id"]
    destination["visited"] = True
    destination["discovered"] = True
    for neighbor_id in destination.get("connections") or []:
        if neighbor_id in by_id:
            by_id[neighbor_id]["discovered"] = True
    session["current_scene"] = destination.get("description") or destination["name"]
    if destination.get("scene_type"):
        session["detected_scene"] = destination["scene_type"]
    _advance_time(session)

    # Narrative flavor (LLM with graceful fallback) — never decides state.
    origin_name = current["name"] if current else "their last camp"
    travel_text = f"The party travels from {origin_name} to {destination['name']}."
    narrator = getattr(request.app.state, "narrator", None)
    try:
        narration = await _generate_dm_response(travel_text, session, narrator, db)
    except Exception:
        narration = f"You arrive at {destination['name']}. {destination.get('description', '')}".strip()

    session["narrative_history"].append(f"Player: {travel_text}")
    session["narrative_history"].append(f"DM: {narration}")
    session["turn_count"] = session.get("turn_count", 0) + 1
    await repo.save_game_session(db, session)

    # Tell every screen at the table (phones, TV, observers)
    from app.api.websockets.game_ws import manager
    await manager.broadcast(session_id, {
        "type": "scene_change",
        "current_location": destination["id"],
        "location": destination,
        "narration": narration,
        "detected_scene": session.get("detected_scene"),
        "world_locations": locations,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    # Animate the DM avatar for the arrival narration
    from app.api.routes.avatar import trigger_speaking
    trigger_speaking(session_id, narration)

    return {
        "current_location": destination["id"],
        "location": destination,
        "narration": narration,
        "detected_scene": session.get("detected_scene"),
        "world_locations": locations,
    }


def _detect_effects(narration: str, player_action: str) -> List[str]:
    """Detect screen effects to trigger based on narration content."""
    import re
    text = f"{narration} {player_action}".lower()
    words = set(re.findall(r'\b\w+\b', text))
    effects: List[str] = []

    if words & {"critical", "nat 20", "natural 20", "critical hit"}:
        effects.append("nat20")
    if "natural 20" in text or "critical hit" in text:
        effects.append("nat20")
    if words & {"damage", "hit", "struck", "wounds", "bleeding", "slash", "pierced"}:
        effects.append("damage")
    if words & {"spell", "magic", "arcane", "incantation", "enchant", "conjure"}:
        effects.append("spell")
    if words & {"level"} and words & {"up", "gained", "advance"}:
        effects.append("levelup")
    if words & {"boss", "dragon", "demon", "lich", "ancient", "titan", "colossus"}:
        effects.append("boss")

    return list(set(effects))


# ── Speech verbs for NPC name extraction ──
_SPEECH_VERBS = r"(?:says?|speaks?|replies?|responds?|whispers?|shouts?|exclaims?|mutters?|growls?|announces?|asks?|calls?|declares?)"

# Generic NPC roles that should NOT be auto-saved as named NPCs
_GENERIC_ROLES = {
    "guard", "guards", "soldier", "merchant", "innkeeper", "bartender",
    "barkeep", "stranger", "figure", "man", "woman", "villager", "peasant",
    "servant", "thief", "bandit", "goblin", "orc", "skeleton", "zombie",
    "warrior", "mage", "priest", "cleric", "old man", "old woman",
    "boy", "girl", "child", "vendor", "trader", "traveler", "patron",
}


def _extract_npcs_from_narration(narration: str) -> list[dict]:
    """Extract named NPCs from DM narration text.
    
    Looks for speech patterns like 'Name says "..."' or '"..." replies Name'
    and returns only proper-noun names (not generic roles like 'the guard').
    """
    found: dict[str, str] = {}  # name_lower -> {name, npc_type}
    lower = narration.lower()

    # Pattern 1: Name VERB "..." — e.g. Kaelrath says "Hello"
    for m in re.finditer(
        rf'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s+{_SPEECH_VERBS}\s*[:,]?\s*["\u201c]',
        narration,
    ):
        name = m.group(1).strip()
        if name.lower() not in _GENERIC_ROLES and len(name) > 1:
            found.setdefault(name.lower(), {"name": name, "npc_type": _detect_npc_type(lower)})

    # Pattern 2: "..." VERB Name — e.g. "Hello" says Kaelrath
    for m in re.finditer(
        rf'["\u201d]\s+{_SPEECH_VERBS}\s+(?:the\s+)?([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)',
        narration,
    ):
        name = m.group(1).strip()
        if name.lower() not in _GENERIC_ROLES and len(name) > 1:
            found.setdefault(name.lower(), {"name": name, "npc_type": _detect_npc_type(lower)})

    # Pattern 3: Proper noun introductions — e.g. "introduces himself as Lord Voss"
    for m in re.finditer(
        r'(?:introduces?\s+(?:himself|herself|themselves)\s+as|(?:name\s+is|called|known\s+as))\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)',
        narration,
    ):
        name = m.group(1).strip()
        if name.lower() not in _GENERIC_ROLES and len(name) > 1:
            found.setdefault(name.lower(), {"name": name, "npc_type": _detect_npc_type(lower)})

    return list(found.values())


def _detect_npc_type(lower: str) -> str:
    """Detect NPC type from contextual keywords in narration text."""
    if re.search(r'\b(?:merchant|shop|buy|sell|wares|vendor|trader|goods|price|coin)\b', lower):
        return "merchant"
    if re.search(r'\b(?:guard|soldier|patrol|captain|watch|sentry|knight|warrior)\b', lower):
        return "guard"
    if re.search(r'\b(?:wizard|mage|sorcerer|archmage|conjurer|enchanter|warlock|witch)\b', lower):
        return "wizard"
    if re.search(r'\b(?:inn|tavern|bartender|barkeep|innkeeper|ale|brew|drink)\b', lower):
        return "innkeeper"
    if re.search(r'\b(?:hooded|shadow|stranger|cloaked|mysterious|dark figure|enigma)\b', lower):
        return "mysterious"
    if re.search(r'\b(?:lord|lady|king|queen|prince|princess|noble|duke|duchess|baron|countess|regent)\b', lower):
        return "noble"
    return "default"


# Scene type keywords — ported from frontend SceneArt.detectScene()
_SCENE_PATTERNS: list[tuple[str, str]] = [
    (r'\b(?:tavern|inn|bar|pub|ale\s*house|drinking|barkeep|bartender)\b', "tavern"),
    (r'\b(?:dungeon|underground|crypt|tomb|catacomb|sewer|cell|prison)\b', "dungeon"),
    (r'\b(?:forest|woods|grove|glade|thicket|treeline|canopy|clearing)\b', "forest"),
    (r'\b(?:cave|cavern|grotto|stalactite|stalagmite|underground)\b', "cave"),
    (r'\b(?:castle|fortress|keep|citadel|battlements|portcullis|throne)\b', "castle"),
    (r'\b(?:temple|shrine|altar|chapel|cathedral|holy|sacred|sanctum)\b', "temple"),
    (r'\b(?:market|bazaar|stall|vendor|merchant|square|plaza|fountain)\b', "market"),
    (r'\b(?:ship|boat|sail|deck|harbor|port|dock|maritime|anchor|mast)\b', "ship"),
    (r'\b(?:mountain|peak|summit|cliff|ridge|highland|crag|alpine)\b', "mountain"),
    (r'\b(?:swamp|marsh|bog|fen|mire|wetland|murky|stagnant)\b', "swamp"),
    (r'\b(?:desert|sand|dune|oasis|arid|scorching|wasteland)\b', "desert"),
    (r'\b(?:village|hamlet|cottage|farm|homestead|rural|pastoral)\b', "village"),
    (r'\b(?:camp|campfire|tent|bivouac|encampment|bedroll)\b', "camp"),
    (r'\b(?:road|path|trail|highway|journey|travel|crossroad)\b', "road"),
    (r'\b(?:battlefield|war|siege|army|troops|carnage|fallen)\b', "battlefield"),
]


def _detect_scene_type(text: str) -> str | None:
    """Detect the scene type from narration text using keyword matching."""
    lower = text.lower()
    for pattern, scene_type in _SCENE_PATTERNS:
        if re.search(pattern, lower):
            return scene_type
    return None


def _merge_detected_npcs(session: dict, detected: list[dict]) -> None:
    """Merge newly detected named NPCs into the session's NPC list.
    
    Only adds NPCs whose names aren't already present (case-insensitive).
    """
    if not detected:
        return
    npcs = session.setdefault("npcs", [])
    existing_names = {n.get("name", "").lower() for n in npcs}
    for npc in detected:
        if npc["name"].lower() not in existing_names:
            npcs.append({
                "name": npc["name"],
                "npc_type": npc.get("npc_type", "default"),
                "disposition": "neutral",
                "location": "",
                "notes": "Auto-detected from narration",
            })
            existing_names.add(npc["name"].lower())


async def _generate_dm_response(player_action: str, session: dict, narrator=None, db=None, on_chunk=None) -> str:
    """Generate a DM narrative response.

    Uses the real LLM narrator when available; falls back to keyword-matching
    mock responses so tests (which have no API key) continue to pass.

    When ``on_chunk`` is provided, LLM tokens are streamed to it as they
    arrive (used by the WS path to live-render narration on the DM display).
    """
    from app.services.llm.narrator import _strip_action_echo

    if narrator is not None and db is not None:
        try:
            import asyncio
            campaign_id = session.get("campaign_id", "")
            campaign = await repo.get_campaign(db, campaign_id) or {}
            world_context = campaign.get("world_state", {}).get("context", "A perilous realm.")
            from app.services.game.combat_loop import combat_prompt_brief
            brief = combat_prompt_brief(session.get("combat_state") or {})
            if brief:
                world_context = f"{world_context}\n\n{brief}"
            char_ids = campaign.get("character_ids", [])
            characters = []
            for cid in char_ids:
                c = await repo.get_character(db, cid)
                if c:
                    characters.append(c)
            from app.services.game.party import absent_party_notice, party_for_table

            characters, absent = party_for_table(characters, session.get("id", ""))
            notice = absent_party_notice(absent)
            if notice:
                world_context = f"{world_context}\n\n{notice}"
            scene = {
                "name": "Current Scene",
                "description": session.get("current_scene", ""),
            }
            story_bible = await repo.get_campaign_story_bible(db, campaign_id) or ""
            # Pass known NPCs for canon protection context
            npcs = session.get("npcs", [])

            # Layered long-term memory: quests, canon facts, and NPC registry
            # relevant to this action are injected into the world context so
            # the DM never contradicts established events across sessions.
            try:
                from app.services.game.memory import build_memory_context
                memory = await repo.get_campaign_memory(db, campaign_id)
                memory_block = build_memory_context(
                    memory,
                    player_action,
                    recent_narrative=session.get("narrative_history", []),
                )
                if memory_block:
                    world_context = f"{world_context}\n\n{memory_block}"
            except Exception as exc:
                logger.warning("Memory retrieval failed (continuing without): %s", exc)

            result = await asyncio.wait_for(
                narrator.narrate_exploration(
                    scene=scene,
                    player_action=player_action,
                    characters=characters,
                    world_context=world_context,
                    story_bible=story_bible,
                    npcs=npcs,
                    session_history=session.get("narrative_history", []),
                    history_summary=session.get("history_summary", "") or "",
                    on_chunk=on_chunk,
                    absent_characters=absent,
                ),
                timeout=90.0 if on_chunk is not None else 45.0,
            )
            # Safety net: strip echoed player action even if narrator missed it
            stripped = _strip_action_echo(result, player_action)
            if stripped != result:
                logger.info("Echo stripped: '%s...' → '%s...'", result[:60], stripped[:60])
            from app.services.game.party import uncredit_absent_heroes

            return uncredit_absent_heroes(
                stripped, [c.get("name", "") for c in absent]
            )
        except asyncio.TimeoutError:
            logger.warning("Narrator timed out after 45s, falling back to keyword mock")
        except Exception as exc:
            logger.warning("Narrator failed, falling back to keyword mock: %s", exc)

    # Keyword mock fallback
    import re
    words = set(re.findall(r'\b\w+\b', player_action.lower()))

    if words & {'look', 'examine', 'inspect', 'search'}:
        return ("You scan your surroundings carefully. The cavern walls glisten with moisture, "
                "and you notice faint scratch marks along the stone floor — something has been "
                "dragged through here recently. A faint breeze carries the scent of smoke from deeper within.")

    if words & {'attack', 'fight', 'strike', 'swing', 'shoot', 'hit', 'slash'}:
        return ("You ready your weapon and strike! Your blow connects with a satisfying impact. "
                "The echo of combat rings through the chamber. Your foe staggers but remains standing, "
                "eyes burning with renewed fury.")

    if words & {'cast', 'spell', 'magic', 'invoke'}:
        return ("Arcane energy crackles at your fingertips as you weave the incantation. "
                "The spell takes shape, illuminating the darkness with brilliant light. "
                "The magical energy surges outward, and you feel the weave of magic respond to your will.")

    if words & {'talk', 'speak', 'say', 'ask', 'greet', 'hello'}:
        return ("Your words echo through the chamber. For a moment, silence. Then a gravelly voice "
                "responds from the shadows: 'Few dare to speak so boldly in these depths. "
                "State your purpose, adventurer, before my patience wears thin.'")

    if words & {'move', 'walk', 'go', 'proceed', 'enter', 'advance', 'head', 'travel'}:
        return ("You press forward cautiously, your footsteps echoing off the ancient stone. "
                "The passage narrows before opening into a wider chamber. Dim phosphorescent "
                "moss clings to the ceiling, casting an eerie blue-green glow over everything.")

    if words & {'rest', 'sleep', 'camp', 'heal'}:
        return ("You find a sheltered alcove and take a moment to catch your breath. "
                "The sounds of the cavern seem distant here. You feel your strength slowly returning "
                "as you tend to your wounds and gather your resolve for what lies ahead.")

    if words & {'check', 'inventory', 'bag', 'pack', 'pouch', 'equipment'}:
        return ("You rummage through your belongings, taking stock of what you carry. "
                "Everything seems to be in order, though supplies won't last forever. "
                "The weight of your equipment is a familiar comfort in this uncertain place.")

    if words & {'open', 'door', 'gate', 'chest', 'lid', 'unlock'}:
        return ("You approach cautiously and reach out. With a creak of ancient hinges, "
                "the way opens before you. A draft of stale air rushes past, carrying the scent "
                "of dust and forgotten things. Beyond, darkness awaits.")

    if words & {'hide', 'sneak', 'stealth', 'quiet', 'creep'}:
        return ("You press yourself against the cold stone, steadying your breath. "
                "The shadows seem to embrace you as you move in silence. "
                "For now, you remain unseen — but these depths have eyes of their own.")

    if words & {'help', 'assist', 'aid', 'support', 'protect', 'defend', 'save', 'rescue'}:
        return ("Your offer of aid hangs in the air. There is a moment of consideration — "
                "perhaps surprise, perhaps calculation — before a response comes. "
                "'Very well. If you mean what you say, then listen carefully...'")

    if words & {'wait', 'follow', 'come', 'lead', 'continue', 'ready', 'agree', 'accept', 'yes', 'tell'}:
        return ("There is a measured pause as your words are weighed. "
                "Then, with a nod of acknowledgment, the conversation shifts. "
                "'Then let us not waste time. There is much to discuss and little daylight left.'")

    # Context-aware default: check if recent history involves NPC dialogue
    history = session.get("narrative_history", [])
    recent = " ".join(history[-4:]).lower() if history else ""
    if any(marker in recent for marker in ["says,", "replies,", "responds,", "voice", "eyes you", "pauses"]):
        return ("Your words land with weight. There is a flicker of something — "
                "respect, perhaps, or wariness — before the response comes. "
                "'Interesting. You are bolder than most who pass through here. "
                "We shall see if your actions match your words.'")

    return ("The world around you seems to shift subtly in response to your presence. "
            "Somewhere in the distance, a sound echoes — a reminder that you are not alone "
            "in this place, and that every choice carries consequence.")


@router.get("/sessions/{session_id}/greeting")
async def get_session_greeting(request: Request, session_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    """Generate the session-opening greeting and last-session recap."""
    import asyncio

    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")

    campaign_id = session.get("campaign_id", "")
    campaign = await repo.get_campaign(db, campaign_id) or {}
    char_ids = campaign.get("character_ids", [])
    characters = []
    for cid in char_ids:
        c = await repo.get_character(db, cid)
        if c:
            characters.append(c)
    world_context = campaign.get("world_state", {}).get("context", "")
    last_summary = await repo.get_campaign_session_summary(db, campaign_id) or ""

    narrator = getattr(request.app.state, "narrator", None)

    # Check for existing story bible (don't generate one here — too slow)
    existing_bible = await repo.get_campaign_story_bible(db, campaign_id)

    # Generate story bible in background (fire-and-forget, don't block greeting)
    if narrator is not None and not existing_bible:
        tone = campaign.get("world_state", {}).get("theme", "dark_fantasy")
        async def _gen_bible():
            try:
                bible = await narrator.generate_story_bible(
                    campaign_name=campaign.get("name", "Adventure"),
                    world_context=world_context,
                    tone=tone,
                )
                await repo.set_campaign_story_bible(db, campaign_id, bible)
            except Exception:
                pass
        asyncio.create_task(_gen_bible())

    from app.services.game.party import absent_party_notice, party_for_table, uncredit_absent_heroes

    present, absent = party_for_table(characters, session_id)
    absent_names = [c.get("name", "") for c in absent]
    notice = absent_party_notice(absent)

    if narrator is not None:
        greeting_world_context = world_context
        if existing_bible and not world_context:
            greeting_world_context = existing_bible.split("\n\n")[0] if "\n\n" in existing_bible else existing_bible[:300]
        if notice:
            greeting_world_context = f"{greeting_world_context}\n\n{notice}"
        try:
            greeting = await asyncio.wait_for(
                narrator.generate_session_greeting(
                    campaign_name=campaign.get("name", "Adventure"),
                    characters=present,
                    last_summary=last_summary,
                    world_context=greeting_world_context,
                ),
                timeout=25.0,
            )
        except asyncio.TimeoutError:
            greeting = None  # fall through to static greeting
    else:
        greeting = None

    if not greeting:
        campaign_name = campaign.get("name", "Adventure")
        if last_summary:
            greeting = (
                f"Welcome back, brave souls. When last we met, {last_summary} "
                "Now, the adventure continues — steel yourselves."
            )
        else:
            greeting = (
                f"Welcome, adventurers, to {campaign_name}. "
                "A world of danger and wonder awaits you. "
                "Your legend begins tonight — what will history remember of you?"
            )

    greeting = uncredit_absent_heroes(greeting, absent_names)
    return {"greeting": greeting}


@router.post("/sessions/{session_id}/summary")
async def save_session_summary(
    request: Request, session_id: str, body: SessionSummaryRequest, db: AsyncSession = Depends(get_db)
) -> dict:
    """Save (or auto-generate) a session summary for next session's recap."""
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")

    campaign_id = session.get("campaign_id", "")
    campaign = await repo.get_campaign(db, campaign_id) or {}

    if body.summary:
        summary = body.summary
    else:
        narrator = getattr(request.app.state, "narrator", None)
        if narrator is not None:
            summary = await narrator.generate_session_summary(
                narrative_history=session.get("narrative_history", []),
                campaign_name=campaign.get("name", ""),
            )
        else:
            history = session.get("narrative_history", [])
            summary = history[-1] if history else "The party's deeds were recorded."

    await repo.set_campaign_session_summary(db, campaign_id, summary)
    return {"summary": summary}


@router.post("/sessions/{session_id}/end")
async def end_game_session(
    request: Request, session_id: str, db: AsyncSession = Depends(get_db)
) -> dict:
    """End a session for the night: generate a recap, persist it to the
    campaign for next session's greeting, stamp the session as ended, and
    tell all connected players."""
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")

    campaign_id = session.get("campaign_id", "")
    campaign = await repo.get_campaign(db, campaign_id) or {}

    narrator = getattr(request.app.state, "narrator", None)
    summary = None
    if narrator is not None:
        try:
            summary = await narrator.generate_session_summary(
                narrative_history=session.get("narrative_history", []),
                campaign_name=campaign.get("name", ""),
            )
        except Exception:
            summary = None
    if not summary:
        history = session.get("narrative_history", [])
        summary = history[-1] if history else "The party's deeds were recorded."

    if campaign_id:
        await repo.set_campaign_session_summary(db, campaign_id, summary)

    session["ended_at"] = datetime.now(timezone.utc).isoformat()
    session["end_summary"] = summary
    await repo.save_game_session(db, session)

    from app.api.websockets.game_ws import manager
    await manager.broadcast(session_id, {
        "type": "session_ended",
        "summary": summary,
        "timestamp": session["ended_at"],
    })

    return {"summary": summary, "ended_at": session["ended_at"]}


# NPC Journal endpoints
class NPCData(BaseModel):
    """NPC data model with structured canon and social state."""
    name: str = Field(..., description="NPC name")
    npc_type: str = Field(..., description="NPC type (merchant, guard, wizard, etc.)")
    disposition: str = Field(default="unknown", description="Disposition (friendly, neutral, hostile, unknown)")
    location: str = Field(default="", description="Last known location")
    notes: str = Field(default="", description="Notes about the NPC")
    # Enriched fields for canon protection and NPC dialogue
    backstory: str = Field(default="", description="Established backstory (DM canon — players cannot rewrite)")
    personality: str = Field(default="", description="Personality traits and mannerisms")
    goals: str = Field(default="", description="What the NPC wants")
    fears: str = Field(default="", description="What the NPC is afraid of")
    secrets: str = Field(default="", description="Hidden information (revealed only if dramatically appropriate)")
    attitude_to_party: Dict[str, Any] = Field(
        default_factory=lambda: {"trust": 0, "fear": 0, "respect": 0, "attraction": 0},
        description="Numeric attitude scores toward the party (-10 to 10)",
    )


class SessionNPCsResponse(BaseModel):
    """Response with session NPCs."""
    npcs: List[NPCData] = Field(default_factory=list, description="List of NPCs")


@router.get("/sessions/{session_id}/npcs", response_model=SessionNPCsResponse)
async def get_session_npcs(session_id: str, db: AsyncSession = Depends(get_db)) -> SessionNPCsResponse:
    """Get all NPCs for a session."""
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")
    
    npcs_data = session.get("npcs", [])
    npcs = [NPCData(**npc) if isinstance(npc, dict) else npc for npc in npcs_data]
    return SessionNPCsResponse(npcs=npcs)


@router.post("/sessions/{session_id}/npcs", response_model=SessionNPCsResponse)
async def add_session_npc(session_id: str, npc: NPCData, db: AsyncSession = Depends(get_db)) -> SessionNPCsResponse:
    """Add or update an NPC in a session."""
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")
    
    if "npcs" not in session:
        session["npcs"] = []
    
    # Find existing NPC with same name (case-insensitive)
    existing_idx = None
    for idx, existing_npc in enumerate(session["npcs"]):
        existing_name = existing_npc.get("name", "") if isinstance(existing_npc, dict) else existing_npc.name
        if existing_name.lower() == npc.name.lower():
            existing_idx = idx
            break
    
    npc_dict = npc.dict()
    
    if existing_idx is not None:
        session["npcs"][existing_idx] = npc_dict
    else:
        session["npcs"].append(npc_dict)
    
    await repo.save_game_session(db, session)
    
    npcs = [NPCData(**n) if isinstance(n, dict) else n for n in session["npcs"]]
    return SessionNPCsResponse(npcs=npcs)


class NPCTalkRequest(BaseModel):
    """Request to talk to an NPC."""
    npc_name: str = Field(..., description="Name of the NPC to talk to")
    message: str = Field(..., description="What the player says or does")


class NPCTalkResponse(BaseModel):
    """Response from NPC conversation."""
    narration: str = Field(..., description="The NPC's response narration")
    npc_name: str = Field(..., description="Name of the NPC who responded")


@router.post("/sessions/{session_id}/npc-talk", response_model=NPCTalkResponse)
async def talk_to_npc(
    request: Request,
    session_id: str,
    body: NPCTalkRequest,
    db: AsyncSession = Depends(get_db),
) -> NPCTalkResponse:
    """Talk to a specific NPC using the dedicated NPC dialogue pipeline.
    
    Routes through narrate_npc_interaction() with the NPC's full structured state,
    canon protection rules, and personality-driven responses.
    """
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")

    # Find the NPC by name (case-insensitive)
    npcs = session.get("npcs", [])
    target_npc = None
    for npc in npcs:
        npc_name = npc.get("name", "") if isinstance(npc, dict) else npc.name
        if npc_name.lower() == body.npc_name.lower():
            target_npc = npc if isinstance(npc, dict) else npc.dict()
            break

    if target_npc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"NPC '{body.npc_name}' not found in session. Add them first via the NPC journal.",
        )

    narrator = getattr(request.app.state, "narrator", None)
    if narrator is not None:
        try:
            import asyncio
            narration = await asyncio.wait_for(
                narrator.narrate_npc_interaction(
                    npc=target_npc,
                    player_message=body.message,
                ),
                timeout=45.0,
            )
        except asyncio.TimeoutError:
            narration = f"{target_npc['name']} regards you thoughtfully but says nothing for the moment."
        except Exception as exc:
            logger.warning("NPC dialogue failed: %s", exc)
            narration = f"{target_npc['name']} seems distracted and doesn't respond clearly."
    else:
        # Keyword mock fallback for tests
        npc_name = target_npc.get("name", "The NPC")
        disposition = target_npc.get("disposition", "neutral")
        if disposition == "friendly":
            narration = f'{npc_name} smiles warmly. "Well met, friend. What brings you here?"'
        elif disposition == "hostile":
            narration = f'{npc_name} narrows their eyes. "Speak quickly. My patience is thin."'
        else:
            narration = f'{npc_name} regards you with a measured gaze. "What do you want?"'

    # Record in narrative history
    session["narrative_history"].append(f"Player: [To {target_npc['name']}] {body.message}")
    session["narrative_history"].append(f"DM: {narration}")
    session["turn_count"] = session.get("turn_count", 0) + 1
    await repo.save_game_session(db, session)

    return NPCTalkResponse(narration=narration, npc_name=target_npc["name"])


@router.post("/world/generate")
async def generate_world(request: Request, body: WorldGenerateRequest, db: AsyncSession = Depends(get_db)) -> dict:
    """Generate a rich world context and store it in the campaign."""
    campaign = await repo.get_campaign(db, body.campaign_id)
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    narrator = getattr(request.app.state, "narrator", None)
    if narrator is not None:
        world_context = await narrator.generate_world(
            theme=body.theme,
            setting=body.setting,
            campaign_name=campaign.get("name", ""),
            hooks=body.hooks,
        )
    else:
        world_context = (
            f"The realm of {body.setting or 'Valdris'} is ancient and perilous. "
            "Three factions vie for power while a shadow grows in the east. "
            "The players arrive at a crossroads moment in history."
        )

    if "world_state" not in campaign:
        campaign["world_state"] = {}
    campaign["world_state"]["context"] = world_context
    campaign["world_state"]["theme"] = body.theme
    campaign["world_state"]["setting"] = body.setting
    await repo.save_campaign(db, campaign)

    return {"world_context": world_context}


async def _sync_combatant_hp(db: AsyncSession, combat_state: dict) -> list[dict]:
    """Write player HP from the combat snapshot onto the character records.

    The full end-of-fight sync also rewrites potions and spell slots. Mid-fight
    we only persist HP, so a phone reload and the TV party list match the bar
    without waiting for combat to end. Healing-potion stacks are left alone:
    the combat snapshot does not mirror them until the fight is over.
    """
    from app.services.game.combat_loop import hp_updates_from_state

    updates = hp_updates_from_state(combat_state)
    by_id = {c["id"]: c for c in combat_state.get("combatants", []) if c.get("is_player")}
    saved: list[dict] = []
    for update in updates:
        character = await repo.get_character(db, update["character_id"])
        if character is None:
            continue
        entry = by_id.get(update["character_id"]) or {}
        character["hp"] = update["hp"]
        if entry and not entry.get("is_alive", True):
            character["is_dead"] = True
        await repo.save_character(db, character)
        saved.append(update)
    return saved


async def apply_reported_hp(
    db: AsyncSession,
    session: dict,
    text: str,
    actor_id: str | None = None,
) -> list[dict]:
    """Apply a spoken damage total or "now at X of Y HP" to the party.

    Prefers the live combat snapshot when a fight is running, and falls back
    to the campaign's character records so a narrated hit still moves the bar
    when initiative was never opened.
    """
    from app.services.game.combat_loop import apply_hp_text

    if not text:
        return []
    combat_state = session.get("combat_state") or {}
    combatants = [c for c in combat_state.get("combatants", []) if c.get("is_player")]
    if combatants:
        notes = apply_hp_text(combatants, text, actor_id=actor_id)
        if not notes:
            return []
        return await _sync_combatant_hp(db, combat_state)

    campaign = await repo.get_campaign(db, session.get("campaign_id", "")) or {}
    characters = []
    for cid in campaign.get("character_ids", []):
        character = await repo.get_character(db, cid)
        if character is not None:
            characters.append(character)
    if not characters:
        return []
    before = {c["id"]: int(c.get("hp") or 0) for c in characters}
    notes = apply_hp_text(characters, text, actor_id=actor_id)
    if not notes:
        return []
    saved = []
    for character in characters:
        if int(character.get("hp") or 0) == before.get(character["id"]):
            continue
        await repo.save_character(db, character)
        saved.append({
            "character_id": character["id"],
            "name": character.get("name"),
            "hp": int(character.get("hp") or 0),
            "max_hp": int(character.get("max_hp") or character.get("hp") or 0),
        })
    return saved


async def _settle_narrated_turn(
    db: AsyncSession,
    session: dict,
    action: str,
    narration: str,
    actor_id: str | None,
) -> tuple[str, list[dict]]:
    """Resolve a monster handoff and write any stated HP change.

    Shared by the host chat endpoint. The phone socket does the same work
    before it broadcasts ``turn_result``.
    """
    from app.services.game.combat_loop import (
        announce_current_player,
        hp_updates_from_state,
        note_current_player_acted,
        prepare_player_facing_narration,
        resolve_waiting_monster_turn,
        settle_narrated_monster_turn,
    )

    ran_engine_monster = False
    combat_state = session.get("combat_state") or {}
    if combat_state.get("combatants"):
        note_current_player_acted(combat_state, actor_id)
        resolved = resolve_waiting_monster_turn(combat_state, narration)
        ran_engine_monster = bool(resolved.get("events")) or bool(resolved.get("combat_over"))
        if resolved.get("events"):
            narration = f"{' '.join(resolved['events'])} {narration}".strip()
        if resolved.get("combat_over"):
            session["current_phase"] = "exploration"
            await _sync_combatants_to_characters(db, combat_state)
            session["combat_state"] = None
        elif resolved.get("events"):
            session["combat_state"] = combat_state
            await _sync_combatant_hp(db, combat_state)
    else:
        campaign = await repo.get_campaign(db, session.get("campaign_id", "")) or {}
        party = []
        for cid in campaign.get("character_ids", []):
            character = await repo.get_character(db, cid)
            if character:
                party.append(character)
        narration = settle_narrated_monster_turn(narration, party, actor_id=actor_id)
    narration = prepare_player_facing_narration(narration, session.get("combat_state"))
    hp_source = action if ran_engine_monster else f"{action}\n{narration}"
    hp_updates = await apply_reported_hp(db, session, hp_source, actor_id=actor_id)
    if ran_engine_monster and session.get("combat_state"):
        await _sync_combatant_hp(db, session["combat_state"])
        hp_updates = hp_updates_from_state(session["combat_state"]) or hp_updates
    note = announce_current_player(session.get("combat_state") or {})
    if note and note not in narration:
        narration = f"{narration} {note}".strip()
    return narration, hp_updates


async def _sync_combatants_to_characters(db: AsyncSession, combat_state: dict) -> None:
    """Write combat-snapshot resource changes back to durable character
    records. Combat state is a self-contained JSON snapshot (see
    combat_loop.py's module docstring) — HP, consumed potions, and spent
    spell slots only ever change on that snapshot, never on the DB record,
    while a fight is in progress. This must run BEFORE the snapshot is
    discarded (combat end or manual end-combat), or every combat resource
    silently resets to its pre-fight value on the next encounter.
    """
    for c in combat_state.get("combatants", []):
        if not c.get("is_player"):
            continue
        character = await repo.get_character(db, c["id"])
        if character is None:
            continue

        character["hp"] = max(0, int(c.get("hp", character.get("hp", 0))))
        if not c.get("is_alive", True):
            character["is_dead"] = True

        # Potions: the combat mirror (`healing_potions`) only ever shrinks —
        # match by item id against the character's real inventory and either
        # update the remaining quantity or drop the stack if it was fully
        # consumed (absent from the final mirror).
        final_potions = {
            p["id"]: int(p.get("quantity", 0))
            for p in c.get("healing_potions", []) if p.get("id")
        }
        inv = character.get("structured_inventory") or []
        new_inv = []
        for item in inv:
            if not isinstance(item, dict):
                new_inv.append(item)
                continue
            effect = item.get("effect")
            is_heal_potion = isinstance(effect, dict) and effect.get("type") == "heal"
            item_id = item.get("id")
            if is_heal_potion and item_id:
                remaining = final_potions.get(item_id, 0)
                if remaining <= 0:
                    continue  # fully consumed during combat
                new_inv.append({**item, "quantity": remaining})
            else:
                new_inv.append(item)
        character["structured_inventory"] = new_inv

        # Spell slots: persist what's left so casters don't get a full
        # refill on their next encounter — only a rest restores them.
        if c.get("spellcasting_ability"):
            character["spell_slots_current"] = dict(c.get("spell_slots", {}))

        await repo.save_character(db, character)


class RestRequest(BaseModel):
    """A short or long rest for some/all of the party."""
    rest_type: str = Field(..., description="'short' or 'long'")
    character_ids: List[str] = Field(default_factory=list, description="Characters to rest (empty = whole campaign party)")


class RestResult(BaseModel):
    character_id: str
    character_name: str
    hp_before: int
    hp_after: int


class RestResponse(BaseModel):
    rest_type: str
    results: List[RestResult]


@router.post("/sessions/{session_id}/rest", response_model=RestResponse)
async def rest(session_id: str, body: RestRequest, db: AsyncSession = Depends(get_db)) -> RestResponse:
    """Short rest: heal half max HP, no slot recovery (warlock pact-slot
    recovery on short rest is not modeled). Long rest: full HP, spell slots
    reset to max, conditions cleared. Dead characters are unaffected."""
    if body.rest_type not in ("short", "long"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="rest_type must be 'short' or 'long'")

    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")
    if session.get("combat_state"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot rest during combat")

    campaign = await repo.get_campaign(db, session.get("campaign_id", "")) or {}
    char_ids = body.character_ids or list(campaign.get("character_ids", []))

    results: list[RestResult] = []
    for cid in char_ids:
        character = await repo.get_character(db, cid)
        if character is None or character.get("is_dead"):
            continue
        max_hp = int(character.get("max_hp") or character.get("hp") or 1)
        hp_before = int(character.get("hp", max_hp))
        if body.rest_type == "long":
            character["hp"] = max_hp
            # NOTE: repo.save_character only merges/overwrites extra_data
            # keys, it never deletes them — pop() here would silently no-op
            # against the persisted record, so slots must be reset to None
            # explicitly (combatant_from_character treats None as "full").
            character["spell_slots_current"] = None
            character["conditions"] = []
        else:
            character["hp"] = min(max_hp, hp_before + max_hp // 2)
        await repo.save_character(db, character)
        results.append(RestResult(
            character_id=cid,
            character_name=character.get("name", "Unknown"),
            hp_before=hp_before,
            hp_after=character["hp"],
        ))

    session.setdefault("narrative_history", []).append(f"DM: The party takes a {body.rest_type} rest.")
    await repo.save_game_session(db, session)

    from app.api.websockets.game_ws import manager
    await manager.broadcast(session_id, {
        "type": "rest_complete",
        "rest_type": body.rest_type,
        "results": [r.model_dump() for r in results],
    })

    return RestResponse(rest_type=body.rest_type, results=results)


class StartCombatEnemy(BaseModel):
    """One enemy group for /start-combat — same shape as /encounter's
    EnemyData, plus optional combat-only fields the generator doesn't set."""
    name: str = Field(..., description="Enemy name")
    hp: int = Field(..., gt=0, description="Hit points")
    ac: int = Field(..., ge=0, description="Armor class")
    cr: float = Field(..., ge=0, description="Challenge rating")
    count: int = Field(default=1, ge=1, description="How many of this enemy")
    damage_type: Optional[str] = Field(None, description="Damage type dealt, e.g. 'fire' (default: bludgeoning)")
    damage_resistances: List[str] = Field(default_factory=list, description="Damage types this enemy resists")
    damage_vulnerabilities: List[str] = Field(default_factory=list, description="Damage types this enemy is vulnerable to")


class StartCombatRequest(BaseModel):
    """Optional encounter payload — when provided, full initiative is rolled."""
    enemies: List[StartCombatEnemy] = Field(default_factory=list, description="e.g. from /encounter")


@router.post("/sessions/{session_id}/start-combat", response_model=GameStateResponse)
async def start_combat(session_id: str, body: StartCombatRequest | None = None, db: AsyncSession = Depends(get_db)) -> GameStateResponse:
    """Start combat encounter in the session.

    With an enemies payload, the deterministic rules engine rolls initiative
    for the whole party + monsters and builds the full combat state. Without
    one, a bare combat phase is opened (legacy behavior).
    """
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")

    session["current_phase"] = GamePhase.COMBAT.value
    opening_events: list[str] = []
    opening_rolls: list[dict] = []
    if body is not None and body.enemies:
        from app.services.game.combat_loop import (
            announce_current_player,
            format_initiative_summary,
            hp_updates_from_state,
            run_pending_monster_turns,
            start_encounter,
        )

        campaign = await repo.get_campaign(db, session.get("campaign_id", "")) or {}
        characters = []
        for cid in campaign.get("character_ids", []):
            c = await repo.get_character(db, cid)
            if c:
                characters.append(c)
        combat_state = start_encounter(characters, [e.model_dump(exclude_none=True) for e in body.enemies])
        # If monsters won initiative, run their opening turns NOW — otherwise
        # combat deadlocks: no phone shows "your turn" and monster turns only
        # run inside resolve_player_action, which nobody can call.
        pre = run_pending_monster_turns(combat_state)
        opening_events = list(pre["events"])
        opening_rolls = pre.get("rolls", [])
        if pre["combat_over"]:
            session["current_phase"] = GamePhase.EXPLORATION.value
            session["combat_state"] = None
            await _sync_combatants_to_characters(db, combat_state)
        else:
            announcement = announce_current_player(combat_state)
            if announcement:
                opening_events.append(announcement)
                combat_state.setdefault("log", []).append(announcement)
            session["combat_state"] = combat_state
            await _sync_combatant_hp(db, combat_state)
        opening_hp = hp_updates_from_state(combat_state)
        opening = "Combat begins! " + format_initiative_summary(combat_state)
        session.setdefault("narrative_history", []).append(f"DM: {opening}")
        for ev in opening_events:
            session["narrative_history"].append(f"DM: {ev}")
    else:
        session["combat_state"] = {
            "initiative_order": [],
            "current_turn_index": 0,
            "round_number": 1,
        }
    await repo.save_game_session(db, session)

    # Notify all connected clients (phones + DM display)
    from app.api.websockets.game_ws import manager
    await manager.broadcast(session_id, {
        "type": "combat_started",
        "combat_state": session["combat_state"],
    })
    if opening_events:
        # Monsters acted before any player turn — tell the table what happened,
        # and name the player who is actually up so nobody waits on a monster.
        await manager.broadcast(session_id, {
            "type": "combat_update",
            "events": opening_events,
            "rolls": opening_rolls,
            "narration": " ".join(opening_events),
            "combat_state": session["combat_state"],
            "phase": session["current_phase"],
            "hp_updates": opening_hp,
        })
    return GameStateResponse(**session)


class CombatActionRequest(BaseModel):
    """A player's combat action, resolved by the deterministic rules engine."""
    actor_id: str = Field(..., description="Combatant id (character id)")
    action_type: str = Field(
        ..., description="attack | heal | dodge | pass | move | dash | disengage | retreat | cast_spell | shove | stand_up | climb_out"
    )
    target_id: Optional[str] = Field(None, description="Target combatant id (for attack/heal/cast_spell/shove)")
    target_x: Optional[int] = Field(None, description="Destination x (for move)")
    target_y: Optional[int] = Field(None, description="Destination y (for move)")
    spell_name: Optional[str] = Field(None, description="Spell name (for cast_spell)")
    slot_level: Optional[int] = Field(None, description="Slot level to cast at, defaults to the spell's base level")
    shove_type: Optional[str] = Field(None, description="'push' or 'prone' (for shove), defaults to 'prone'")
    player_id: Optional[str] = Field(
        None, description="Player id claiming this action. Required once players have joined the session via room code; ignored for solo/desktop sessions with no registered players."
    )
    action_text: Optional[str] = Field(
        None, description="The sentence the player typed. Echoed to every screen; the rules engine still resolves action_type."
    )
    client_id: Optional[str] = Field(
        None, description="Phone line id. A retry of the same id is not applied twice."
    )
    sender: Optional[str] = Field(None, description="Display name for the typed line")


@router.post("/sessions/{session_id}/combat-action")
async def combat_action(session_id: str, body: CombatActionRequest, request: Request, db: AsyncSession = Depends(get_db)) -> dict:
    """Resolve a combat action authoritatively (dice, HP, death saves are
    computed by the rules engine — the LLM only narrates afterwards)."""
    from app.services.game.combat_loop import resolve_player_action

    from app.api.action_receipts import claim_client_action, release_client_action

    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")

    if not claim_client_action(session_id, body.client_id):
        return {
            "ok": True,
            "duplicate": True,
            "events": [],
            "narration": "",
            "combat_state": session.get("combat_state"),
            "phase": session.get("current_phase"),
        }

    # Once players have joined via room code, a combat action must be claimed
    # by the player who owns that character — prevents one phone from acting
    # for someone else's character. Solo/desktop sessions with no registered
    # roster (and all existing tests) are unaffected.
    registered_players = storage.session_players.get(session_id) or []
    if registered_players:
        from app.api.routes.items import _player_owns_character
        if not body.player_id or not _player_owns_character(session_id, body.player_id, body.actor_id):
            release_client_action(session_id, body.client_id)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="That isn't your character")

    combat_state = session.get("combat_state")
    if not combat_state or not combat_state.get("combatants"):
        release_client_action(session_id, body.client_id)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No active combat with initiative — call start-combat with enemies first")

    result = resolve_player_action(
        combat_state, body.actor_id, body.action_type, body.target_id, body.target_x, body.target_y,
        spell_name=body.spell_name, slot_level=body.slot_level, shove_type=body.shove_type,
    )
    if result.get("error"):
        release_client_action(session_id, body.client_id)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=result["error"])

    # Persist deterministic outcomes into the narrative record
    for ev in result["events"]:
        session.setdefault("narrative_history", []).append(f"DM: {ev}")

    # Double-award guard: if combat is ending, re-check the persisted session
    # for a concurrent request that already finished it (cleared
    # combat_state) before we get here. If so, another in-flight request
    # already ran the sync/XP/broadcast for this same kill — skip doing it
    # again rather than double-persisting or double-awarding XP.
    already_finished_elsewhere = False
    if result.get("combat_over"):
        fresh = await repo.get_game_session(db, session_id)
        already_finished_elsewhere = fresh is not None and fresh.get("combat_state") is None

    xp_awards: list[dict] = []
    from app.services.game.combat_loop import hp_updates_from_state
    hp_updates = hp_updates_from_state(combat_state)
    if already_finished_elsewhere:
        session["combat_state"] = None
        session["current_phase"] = GamePhase.EXPLORATION.value
    else:
        if result.get("combat_over"):
            session["current_phase"] = GamePhase.EXPLORATION.value
            await _sync_combatants_to_characters(db, combat_state)
            session["combat_state"] = None
        else:
            session["combat_state"] = combat_state
            await _sync_combatant_hp(db, combat_state)
        await repo.save_game_session(db, session)

        # On victory, persist the deterministic XP award to each player
        # character so pending level-ups are queued for LevelUpModal to pick
        # up — combat_loop itself never touches the DB (see module
        # docstring), so this is the one spot where the authoritative
        # xp_awarded number actually lands on a character record.
        if result.get("combat_over") and result.get("victory") and result.get("xp_awarded"):
            player_ids = [c["id"] for c in combat_state.get("combatants", []) if c.get("is_player")]
            if player_ids:
                _, xp_awards = await _apply_xp_award(db, player_ids, result["xp_awarded"])

    # The deterministic outcome is broadcast IMMEDIATELY — flavor narration
    # from the LLM runs as a background task so a slow/rate-limited provider
    # can never stall the request (previously requests queued behind serial
    # LLM calls and hit the reverse-proxy 60s timeout as 504s).
    payload = {
        **result,
        "narration": " ".join(result["events"]),
        "combat_state": session.get("combat_state"),
        "phase": session["current_phase"],
        "xp_awards": xp_awards,
        "hp_updates": hp_updates,
    }

    if already_finished_elsewhere:
        return payload

    from app.api.websockets.game_ws import manager
    if body.action_text:
        actor = next(
            (c for c in (combat_state or {}).get("combatants") or [] if c.get("id") == body.actor_id),
            None,
        )
        await manager.broadcast(session_id, {
            "type": "player_action",
            "client_id": body.client_id,
            "character_id": body.actor_id,
            "text": body.action_text,
            "sender": body.sender or (actor or {}).get("name") or "",
            "timestamp": datetime.now().isoformat(),
        })
    await manager.broadcast(session_id, {"type": "combat_update", **payload})

    narrator = getattr(request.app.state, "narrator", None)
    if narrator is not None:
        import asyncio as _asyncio

        events_text = " ".join(result["events"])
        history_snapshot = list(session.get("narrative_history", []))
        combat_snapshot = dict(combat_state or {})

        async def _narrate_in_background() -> None:
            try:
                narration = await _asyncio.wait_for(
                    narrator.narrate_combat_action(
                        combat_snapshot,
                        {"description": events_text},
                        [],
                        session_history=history_snapshot,
                    ),
                    timeout=30.0,
                )
            except Exception:
                logger.exception("Combat narration failed for session %s", session_id)
                # The rules engine already moved the turn. Leaving this
                # unannounced is what stuck the DM on Waiting mid-sentence.
                await manager.broadcast(session_id, {
                    "type": "narration_end",
                    "narration": "",
                    "phase": session.get("current_phase"),
                    "combat_state": session.get("combat_state"),
                    "recover": True,
                })
                return
            if narration:
                from app.api.routes.avatar import trigger_speaking
                trigger_speaking(session_id, narration)
                from app.services.game.combat_loop import prepare_player_facing_narration
                narration = prepare_player_facing_narration(narration, None if result.get("combat_over") else combat_snapshot)
                payload = {
                    "type": "turn_result",
                    "narration": narration,
                    "hp_updates": hp_updates_from_state(combat_snapshot),
                }
                # Flavor text can finish after the fight — or after the table
                # has moved to another scene. Attach combat only when the
                # stored session is still this fight, and use that row, not
                # the snapshot captured when the action started.
                if not result.get("combat_over"):
                    live_factory = getattr(request.app.state, "db_factory", None)
                    live: dict = {}
                    if live_factory is not None:
                        try:
                            async with live_factory() as live_db:
                                live = await repo.get_game_session(live_db, session_id) or {}
                        except Exception:
                            live = {}
                    live_combat = live.get("combat_state") or {}
                    if live.get("current_phase") == "combat" and live_combat.get("combatants"):
                        payload["combat_state"] = live_combat
                        payload["phase"] = "combat"
                        payload["state_version"] = repo.session_version(live)
                await manager.broadcast(session_id, payload)

        task = _asyncio.create_task(_narrate_in_background())
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)
        # Let a narration that fails immediately broadcast narration_end
        # before this response returns, so the table is not left waiting.
        await _asyncio.sleep(0)

    return payload


@router.post("/sessions/{session_id}/end-combat", response_model=GameStateResponse)
async def end_combat(session_id: str, db: AsyncSession = Depends(get_db)) -> GameStateResponse:
    """End combat encounter in the session."""
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")

    combat_state = session.get("combat_state")
    if combat_state:
        await _sync_combatants_to_characters(db, combat_state)

    session["current_phase"] = GamePhase.EXPLORATION.value
    session["combat_state"] = None
    await repo.save_game_session(db, session)
    return GameStateResponse(**session)




# --- Additional endpoints below (no duplicate schemas) ---


class SceneMood(BaseModel):
    """Atmospheric mood metadata for the current scene."""
    atmosphere: str = Field(default="neutral", description="Overall mood: dark, warm, tense, mystical, peaceful, combat")
    lighting: str = Field(default="dim", description="Lighting: bright, dim, dark, magical, fire")
    weather: str = Field(default="clear", description="Weather: clear, rain, storm, fog, snow, wind")
    danger_level: str = Field(default="low", description="Danger level: safe, low, moderate, high, deadly")
    ambient_sounds: List[str] = Field(default_factory=list, description="Suggested ambient sounds")


MOOD_KEYWORDS = {
    "dark": {"dark", "shadow", "dungeon", "cave", "crypt", "tomb", "undead", "death", "horror"},
    "warm": {"tavern", "inn", "fire", "hearth", "home", "feast", "celebration", "warm"},
    "tense": {"trap", "ambush", "stealth", "sneak", "hidden", "lurk", "danger", "threat"},
    "mystical": {"magic", "arcane", "spell", "enchant", "rune", "ancient", "portal", "fey", "ethereal"},
    "peaceful": {"village", "meadow", "forest", "stream", "dawn", "sunrise", "garden", "temple"},
    "combat": {"battle", "fight", "attack", "charge", "sword", "arrow", "blood", "war"},
}

LIGHTING_KEYWORDS = {
    "bright": {"sun", "daylight", "noon", "bright", "open", "desert"},
    "dark": {"dark", "pitch", "blind", "deep", "underground", "cave"},
    "magical": {"glow", "rune", "crystal", "enchant", "aurora", "shimmer"},
    "fire": {"torch", "fire", "flame", "candle", "lantern", "hearth"},
}


def _detect_mood(scene_text: str) -> SceneMood:
    """Analyze scene text to determine atmospheric mood."""
    import re
    words = set(re.findall(r'\b\w+\b', scene_text.lower()))

    atmosphere = "neutral"
    best_score = 0
    for mood, keywords in MOOD_KEYWORDS.items():
        score = len(words & keywords)
        if score > best_score:
            best_score = score
            atmosphere = mood

    lighting = "dim"
    best_score = 0
    for light, keywords in LIGHTING_KEYWORDS.items():
        score = len(words & keywords)
        if score > best_score:
            best_score = score
            lighting = light

    danger = "low"
    if atmosphere == "combat":
        danger = "high"
    elif atmosphere == "tense":
        danger = "moderate"
    elif atmosphere == "dark":
        danger = "moderate"
    elif atmosphere == "peaceful":
        danger = "safe"

    # Suggest ambient sounds based on mood
    sound_map = {
        "dark": ["dripping_water", "distant_rumble", "wind_howl"],
        "warm": ["crackling_fire", "crowd_murmur", "lute_music"],
        "tense": ["heartbeat", "creaking_wood", "distant_footsteps"],
        "mystical": ["ethereal_hum", "wind_chimes", "distant_bells"],
        "peaceful": ["birdsong", "flowing_water", "gentle_breeze"],
        "combat": ["battle_drums", "steel_clash", "war_horns"],
        "neutral": ["ambient_wind", "crickets"],
    }

    return SceneMood(
        atmosphere=atmosphere,
        lighting=lighting,
        danger_level=danger,
        ambient_sounds=sound_map.get(atmosphere, ["ambient_wind"]),
    )


def _advance_time(session: dict) -> None:
    """Advance time of day in the session with chance of weather change.
    
    Cycles through: dawn -> morning -> noon -> afternoon -> dusk -> evening -> night -> midnight -> dawn
    Has 20% chance to change weather each turn.
    """
    if "environment" not in session:
        session["environment"] = {
            "time_of_day": "dawn",
            "weather": "clear",
            "temperature": "cool",
            "season": "spring",
        }
    
    env = session["environment"]
    
    # Time cycle progression
    time_cycle = ["dawn", "morning", "noon", "afternoon", "dusk", "evening", "night", "midnight"]
    current_time = env.get("time_of_day", "dawn")
    current_idx = time_cycle.index(current_time) if current_time in time_cycle else 0
    next_idx = (current_idx + 1) % len(time_cycle)
    env["time_of_day"] = time_cycle[next_idx]
    
    # 20% chance to change weather
    if random.random() < 0.2:
        weather_options = ["clear", "cloudy", "rain", "storm", "snow", "fog", "wind"]
        current_weather = env.get("weather", "clear")
        # Pick a different weather
        available = [w for w in weather_options if w != current_weather]
        if available:
            env["weather"] = random.choice(available)
    
    # Adjust temperature based on time of day
    temp_by_time = {
        "midnight": "freezing",
        "dawn": "cold",
        "morning": "cool",
        "noon": "warm",
        "afternoon": "hot",
        "dusk": "cool",
        "evening": "cold",
        "night": "freezing",
    }
    env["temperature"] = temp_by_time.get(env["time_of_day"], "mild")


@router.get("/sessions/{session_id}/environment", response_model=EnvironmentData)
async def get_environment(session_id: str, db: AsyncSession = Depends(get_db)) -> EnvironmentData:
    """Get the current environment (weather, time of day, etc.)."""
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")
    
    env = session.get("environment", {
        "time_of_day": "dawn",
        "weather": "clear",
        "temperature": "cool",
        "season": "spring",
    })
    return EnvironmentData(**env)


@router.post("/sessions/{session_id}/environment", response_model=EnvironmentData)
async def update_environment(session_id: str, env: EnvironmentData, db: AsyncSession = Depends(get_db)) -> EnvironmentData:
    """Update the environment (weather, time of day, etc.)."""
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")
    
    session["environment"] = env.dict()
    await repo.save_game_session(db, session)
    return EnvironmentData(**session["environment"])


@router.get("/sessions/{session_id}/mood")
async def get_scene_mood(session_id: str, db: AsyncSession = Depends(get_db)) -> SceneMood:
    """Get the atmospheric mood of the current scene."""
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")

    scene = session.get("current_scene", "")
    history = session.get("narrative_history", [])
    recent = " ".join(history[-4:]) if history else ""
    combined = f"{scene} {recent}"

    return _detect_mood(combined)


@router.get("/sessions/{session_id}/recap")
async def get_session_recap(session_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    """Get the recap of the previous session for cinematic display."""
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")

    campaign_id = session.get("campaign_id", "")
    campaign = await repo.get_campaign(db, campaign_id) or {}
    campaign_name = campaign.get("name", "Your Adventure")
    last_summary = await repo.get_campaign_session_summary(db, campaign_id) or ""

    if not last_summary:
        return {"has_recap": False, "campaign_name": campaign_name, "recap_text": ""}

    return {
        "has_recap": True,
        "campaign_name": campaign_name,
        "recap_text": last_summary,
    }


# --- Encounter Generation ---

class EnemyData(BaseModel):
    """A single enemy in an encounter."""
    name: str = Field(..., description="Enemy name")
    hp: int = Field(..., description="Hit points")
    ac: int = Field(..., description="Armor class")
    cr: float = Field(..., description="Challenge rating")
    count: int = Field(default=1, description="How many of this enemy")
    damage_type: Optional[str] = Field(None, description="Best-effort damage type parsed from SRD data (default: bludgeoning)")


class EncounterRequest(BaseModel):
    """Request to generate a random encounter."""
    environment: str = Field(..., description="Environment: dungeon, forest, cave, mountain, swamp, urban")
    difficulty: str = Field(..., description="Difficulty: easy, medium, hard, deadly")
    party_level: int = Field(default=1, description="Average party level (1-20)")


class EncounterResponse(BaseModel):
    """Response with generated encounter details."""
    enemies: List[EnemyData] = Field(..., description="List of enemies")
    total_xp: int = Field(..., description="Total XP for the encounter")
    difficulty_rating: str = Field(..., description="Actual difficulty: easy, medium, hard, deadly")
    description: str = Field(..., description="Flavor text for the encounter")


# SRD Monster Database grouped by CR and environment
SRD_MONSTERS = {
    "dungeon": {
        0.125: [
            {"name": "Cultist", "hp": 5, "ac": 12},
            {"name": "Goblin", "hp": 7, "ac": 15},
            {"name": "Skeleton", "hp": 13, "ac": 15},
            {"name": "Zombie", "hp": 22, "ac": 8},
            {"name": "Commoner", "hp": 4, "ac": 10},
        ],
        0.25: [
            {"name": "Gnoll", "hp": 22, "ac": 15},
            {"name": "Orc", "hp": 15, "ac": 13},
            {"name": "Wererat", "hp": 33, "ac": 12},
            {"name": "Ghoul", "hp": 22, "ac": 12},
            {"name": "Hobgoblin", "hp": 11, "ac": 18},
        ],
        0.5: [
            {"name": "Wyvern", "hp": 110, "ac": 13},
            {"name": "Ogre", "hp": 59, "ac": 11},
            {"name": "Specter", "hp": 22, "ac": 12},
            {"name": "Troll", "hp": 84, "ac": 15},
            {"name": "Chimera", "hp": 114, "ac": 14},
        ],
        1: [
            {"name": "Bandit Captain", "hp": 65, "ac": 15},
            {"name": "Cult Fanatic", "hp": 33, "ac": 13},
            {"name": "Druid", "hp": 27, "ac": 11},
            {"name": "Knight", "hp": 52, "ac": 18},
            {"name": "Veteran", "hp": 52, "ac": 17},
        ],
        2: [
            {"name": "Berserker", "hp": 67, "ac": 13},
            {"name": "Priest", "hp": 27, "ac": 13},
            {"name": "Manticore", "hp": 68, "ac": 13},
            {"name": "Werewolf", "hp": 18, "ac": 12},
            {"name": "Ghast", "hp": 36, "ac": 13},
        ],
        3: [
            {"name": "Basilisk", "hp": 52, "ac": 15},
            {"name": "Cockatrice", "hp": 27, "ac": 12},
            {"name": "Mimic", "hp": 17, "ac": 12},
            {"name": "Wight", "hp": 45, "ac": 14},
            {"name": "Treant", "hp": 138, "ac": 16},
        ],
        5: [
            {"name": "Hill Giant", "hp": 105, "ac": 13},
            {"name": "Mummy", "hp": 97, "ac": 11},
            {"name": "Troll Regenerating", "hp": 84, "ac": 15},
            {"name": "Medusa", "hp": 71, "ac": 15},
            {"name": "Chimera Ancient", "hp": 114, "ac": 14},
        ],
    },
    "forest": {
        0.125: [
            {"name": "Deer", "hp": 4, "ac": 13},
            {"name": "Badger", "hp": 3, "ac": 12},
            {"name": "Stirge", "hp": 1, "ac": 14},
            {"name": "Raven", "hp": 1, "ac": 14},
            {"name": "Lizard", "hp": 1, "ac": 12},
        ],
        0.25: [
            {"name": "Wolf", "hp": 11, "ac": 13},
            {"name": "Boar", "hp": 11, "ac": 11},
            {"name": "Aarakocra", "hp": 13, "ac": 13},
            {"name": "Elk", "hp": 13, "ac": 10},
            {"name": "Giant Spider", "hp": 26, "ac": 14},
        ],
        0.5: [
            {"name": "Ape", "hp": 19, "ac": 12},
            {"name": "Black Bear", "hp": 34, "ac": 12},
            {"name": "Dire Wolf", "hp": 37, "ac": 13},
            {"name": "Giant Ape", "hp": 157, "ac": 12},
            {"name": "Tiger", "hp": 37, "ac": 12},
        ],
        1: [
            {"name": "Dryad", "hp": 22, "ac": 14},
            {"name": "Pixie", "hp": 1, "ac": 15},
            {"name": "Satyr", "hp": 31, "ac": 14},
            {"name": "Owlbear", "hp": 59, "ac": 13},
            {"name": "Giant Constrictor Snake", "hp": 60, "ac": 12},
        ],
        2: [
            {"name": "Allosaurus", "hp": 51, "ac": 12},
            {"name": "Ankheg", "hp": 39, "ac": 14},
            {"name": "Couatl", "hp": 97, "ac": 19},
            {"name": "Gnoll Pack Lord", "hp": 49, "ac": 16},
            {"name": "Giant Hyena", "hp": 45, "ac": 12},
        ],
        3: [
            {"name": "Cyclops", "hp": 138, "ac": 14},
            {"name": "Hydra", "hp": 172, "ac": 15},
            {"name": "Manticores", "hp": 68, "ac": 13},
            {"name": "Phoenix", "hp": 175, "ac": 15},
            {"name": "Wyvern", "hp": 110, "ac": 13},
        ],
    },
    "cave": {
        0.125: [
            {"name": "Giant Centipede", "hp": 4, "ac": 14},
            {"name": "Bat", "hp": 1, "ac": 12},
            {"name": "Giant Rat", "hp": 7, "ac": 15},
            {"name": "Dwarf", "hp": 27, "ac": 15},
            {"name": "Goblin", "hp": 7, "ac": 15},
        ],
        0.25: [
            {"name": "Giant Scorpion", "hp": 32, "ac": 15},
            {"name": "Giant Spider Web", "hp": 26, "ac": 14},
            {"name": "Troglodyte", "hp": 13, "ac": 11},
            {"name": "Duergar", "hp": 26, "ac": 16},
            {"name": "Drow", "hp": 13, "ac": 15},
        ],
        0.5: [
            {"name": "Troll", "hp": 84, "ac": 15},
            {"name": "Wyvern", "hp": 110, "ac": 13},
            {"name": "Chimera", "hp": 114, "ac": 14},
            {"name": "Behir", "hp": 168, "ac": 17},
            {"name": "Purple Worm", "hp": 248, "ac": 19},
        ],
        1: [
            {"name": "Cloaker", "hp": 78, "ac": 14},
            {"name": "Duergar Mage", "hp": 26, "ac": 15},
            {"name": "Drow Elite Warrior", "hp": 71, "ac": 18},
            {"name": "Invisible Stalker", "hp": 22, "ac": 15},
            {"name": "Will-o'-the-Wisp", "hp": 22, "ac": 19},
        ],
        2: [
            {"name": "Basilisk", "hp": 52, "ac": 15},
            {"name": "Beholder", "hp": 180, "ac": 17},
            {"name": "Medusa", "hp": 71, "ac": 15},
            {"name": "Otyugh", "hp": 114, "ac": 14},
            {"name": "Chimera Ancient", "hp": 114, "ac": 14},
        ],
    },
    "mountain": {
        0.125: [
            {"name": "Eagle", "hp": 26, "ac": 13},
            {"name": "Goat", "hp": 22, "ac": 12},
            {"name": "Hawk", "hp": 1, "ac": 13},
            {"name": "Pony", "hp": 11, "ac": 12},
            {"name": "Snow Hare", "hp": 1, "ac": 14},
        ],
        0.25: [
            {"name": "Aarakocra", "hp": 13, "ac": 13},
            {"name": "Giant Eagle", "hp": 26, "ac": 13},
            {"name": "Giant Goat", "hp": 19, "ac": 12},
            {"name": "Manticore Adolescent", "hp": 34, "ac": 12},
            {"name": "Wyvern Juvenile", "hp": 55, "ac": 12},
        ],
        0.5: [
            {"name": "Chimera", "hp": 114, "ac": 14},
            {"name": "Hydra", "hp": 172, "ac": 15},
            {"name": "Wyvern", "hp": 110, "ac": 13},
            {"name": "Roc", "hp": 195, "ac": 15},
            {"name": "Giant Eagle Massive", "hp": 26, "ac": 13},
        ],
        1: [
            {"name": "Air Elemental", "hp": 90, "ac": 15},
            {"name": "Cloud Giant Scout", "hp": 142, "ac": 15},
            {"name": "Frost Giant Scout", "hp": 65, "ac": 15},
            {"name": "Phoenix", "hp": 175, "ac": 15},
            {"name": "Storm Giant Scout", "hp": 178, "ac": 16},
        ],
        2: [
            {"name": "Chimera", "hp": 114, "ac": 14},
            {"name": "Fire Giant", "hp": 162, "ac": 17},
            {"name": "Frost Giant", "hp": 150, "ac": 15},
            {"name": "Hill Giant", "hp": 105, "ac": 13},
            {"name": "Remorhaz", "hp": 195, "ac": 17},
        ],
    },
    "swamp": {
        0.125: [
            {"name": "Frog", "hp": 1, "ac": 11},
            {"name": "Snake", "hp": 1, "ac": 11},
            {"name": "Giant Frog", "hp": 7, "ac": 11},
            {"name": "Lizard Swamp", "hp": 1, "ac": 12},
            {"name": "Stirge Swarm", "hp": 22, "ac": 14},
        ],
        0.25: [
            {"name": "Giant Constrictor Snake", "hp": 30, "ac": 12},
            {"name": "Giant Poisonous Snake", "hp": 11, "ac": 13},
            {"name": "Giant Spider Swamp", "hp": 26, "ac": 14},
            {"name": "Giant Toad", "hp": 39, "ac": 11},
            {"name": "Will-o'-the-Wisp", "hp": 22, "ac": 19},
        ],
        0.5: [
            {"name": "Giant Ape", "hp": 157, "ac": 12},
            {"name": "Giant Constrictor Huge", "hp": 60, "ac": 12},
            {"name": "Shambling Mound", "hp": 52, "ac": 15},
            {"name": "Troll", "hp": 84, "ac": 15},
            {"name": "Wyvern", "hp": 110, "ac": 13},
        ],
        1: [
            {"name": "Drowned Assassin", "hp": 45, "ac": 16},
            {"name": "Hydra Swamp", "hp": 172, "ac": 15},
            {"name": "Lizardfolk Shaman", "hp": 27, "ac": 15},
            {"name": "Shambling Mound Overgrown", "hp": 52, "ac": 15},
            {"name": "Will-o'-the-Wisp Grave", "hp": 22, "ac": 19},
        ],
        2: [
            {"name": "Behir", "hp": 168, "ac": 17},
            {"name": "Hydra Ancient", "hp": 172, "ac": 15},
            {"name": "Shambling Mound Ancient", "hp": 52, "ac": 15},
            {"name": "Troll Regenerating", "hp": 84, "ac": 15},
            {"name": "Will-o'-the-Wisp Devouring", "hp": 22, "ac": 19},
        ],
    },
    "urban": {
        0.125: [
            {"name": "Commoner", "hp": 4, "ac": 10},
            {"name": "Guard", "hp": 11, "ac": 16},
            {"name": "Thug", "hp": 32, "ac": 12},
            {"name": "Cultist", "hp": 5, "ac": 12},
            {"name": "Noble", "hp": 9, "ac": 15},
        ],
        0.25: [
            {"name": "Assassin", "hp": 78, "ac": 16},
            {"name": "Bandit Captain", "hp": 65, "ac": 15},
            {"name": "Gladiator", "hp": 112, "ac": 15},
            {"name": "Knight", "hp": 52, "ac": 18},
            {"name": "Warlord", "hp": 229, "ac": 18},
        ],
        0.5: [
            {"name": "Champion", "hp": 143, "ac": 18},
            {"name": "Demon Imp", "hp": 10, "ac": 12},
            {"name": "Devil Imp", "hp": 10, "ac": 12},
            {"name": "Shambling Mound", "hp": 52, "ac": 15},
            {"name": "Water Elemental", "hp": 90, "ac": 15},
        ],
        1: [
            {"name": "Cult Fanatic Leader", "hp": 33, "ac": 14},
            {"name": "Djinn", "hp": 161, "ac": 17},
            {"name": "Eladrin Mage", "hp": 127, "ac": 15},
            {"name": "Priest High", "hp": 27, "ac": 13},
            {"name": "Troll Underground", "hp": 84, "ac": 15},
        ],
        2: [
            {"name": "Beholder Newborn", "hp": 90, "ac": 15},
            {"name": "Chimera Urban", "hp": 114, "ac": 14},
            {"name": "Marid", "hp": 229, "ac": 17},
            {"name": "Medusa Cursed", "hp": 71, "ac": 15},
            {"name": "Naga Guardian", "hp": 75, "ac": 16},
        ],
    },
}

# XP thresholds for party difficulty (per player, combined for party)
XP_THRESHOLDS = {
    1: {"easy": 25, "medium": 50, "hard": 75, "deadly": 100},
    2: {"easy": 50, "medium": 100, "hard": 150, "deadly": 200},
    3: {"easy": 75, "medium": 150, "hard": 225, "deadly": 400},
    4: {"easy": 125, "medium": 250, "hard": 375, "deadly": 500},
    5: {"easy": 250, "medium": 500, "hard": 750, "deadly": 1100},
    6: {"easy": 300, "medium": 600, "hard": 900, "deadly": 1400},
    7: {"easy": 350, "medium": 750, "hard": 1100, "deadly": 1700},
    8: {"easy": 450, "medium": 1000, "hard": 1400, "deadly": 2100},
    9: {"easy": 550, "medium": 1200, "hard": 1600, "deadly": 2400},
    10: {"easy": 600, "medium": 1500, "hard": 1900, "deadly": 2800},
}

ENVIRONMENT_DESCRIPTIONS = {
    "dungeon": [
        "You enter a crumbling stone chamber filled with the stench of decay. Torchlight flickers across ancient carvings.",
        "The underground passage echoes with unsettling sounds. Moisture drips from the vaulted ceiling above.",
        "A vast dungeon complex sprawls before you, its corridors twisting into shadow and mystery.",
        "Chains hang from the walls of this forsaken keep. Something stirs in the darkness.",
        "Ancient stonework bears signs of arcane magic. The air crackles with residual power.",
    ],
    "forest": [
        "Ancient trees tower overhead, their canopy blocking out the sun. Danger lurks between every trunk.",
        "The forest path ahead is overgrown with twisted vines and gnarled roots.",
        "Dappled moonlight filters through the dense foliage. Strange sounds echo through the trees.",
        "You push through thick undergrowth into a clearing—but it's not empty.",
        "The forest grows darker and more primal the deeper you venture.",
    ],
    "cave": [
        "The cavern walls glisten with moisture and strange mineral formations.",
        "Echoing drips and distant howls fill the darkness ahead.",
        "You enter a massive underground cavern filled with bioluminescent flora.",
        "The air grows colder as you descend deeper into the earth.",
        "Stalactites hang like weapons above a cavern floor littered with bone.",
    ],
    "mountain": [
        "The mountain pass narrows ahead, winds howling between jagged peaks.",
        "You spot movement on the rocky slopes above—silhouetted against the sky.",
        "The air thins as you climb higher, the world sprawling below you.",
        "Storm clouds gather over the mountain peaks, bringing an ominous chill.",
        "Ancient ruins cling to the mountainside, weathered by countless ages.",
    ],
    "swamp": [
        "Murky water stretches before you, fog rising from its depths.",
        "The air is thick and suffocating, filled with the sounds of unseen creatures.",
        "Twisted trees emerge from stagnant water, their roots tangled and menacing.",
        "Will-o'-the-wisps flicker in the darkness ahead—or perhaps something worse.",
        "The swamp reeks of decay and ancient magic.",
    ],
    "urban": [
        "The city streets are darker than you expected. Shadows seem to move of their own accord.",
        "You turn a corner into an alley—and find yourselves face to face with trouble.",
        "The tavern goes quiet as you enter. Something feels very wrong.",
        "City guards or hired assassins? It's hard to tell in the dim torchlight.",
        "A masked figure emerges from the crowd, hand on their weapon.",
    ],
}


def _calculate_encounter_difficulty(total_xp: int, party_size: int, party_level: int) -> str:
    """Determine if encounter is easy, medium, hard, or deadly."""
    target_threshold = XP_THRESHOLDS.get(party_level, XP_THRESHOLDS[10])
    
    if total_xp <= target_threshold["easy"] * party_size:
        return "easy"
    elif total_xp <= target_threshold["medium"] * party_size:
        return "medium"
    elif total_xp <= target_threshold["hard"] * party_size:
        return "hard"
    else:
        return "deadly"


def _get_cr_value(difficulty: str, party_level: int) -> tuple[float, float]:
    """Get the CR range for the requested difficulty."""
    # Suggested CR is roughly party_level - 1 to party_level + 2
    base_cr = max(0.125, party_level - 1)
    
    difficulty_adjustments = {
        "easy": (-0.5, 0.5),
        "medium": (0, 1),
        "hard": (0.5, 1.5),
        "deadly": (1, 2),
    }
    
    adj_low, adj_high = difficulty_adjustments.get(difficulty, (0, 1))
    return (max(0.125, base_cr + adj_low), base_cr + adj_high)


_DAMAGE_TYPE_RE = re.compile(r"(\w+)\s+damage")


def _srd_damage_type(name: str) -> Optional[str]:
    """Best-effort damage type for a named monster, parsed from the SRD
    monster's free-text `actions` description (e.g. "...Hit: 5 (1d6+2)
    slashing damage." -> "slashing"). Returns None when the monster isn't
    in the SRD table or no damage type could be parsed — callers fall back
    to combat_loop's "bludgeoning" default in that case."""
    from app.services.srd.data import srd_monsters

    name_lower = name.lower()
    for monster in srd_monsters:
        if monster.name.lower() == name_lower:
            match = _DAMAGE_TYPE_RE.search(monster.actions or "")
            return match.group(1).lower() if match else None
    return None


@router.post("/sessions/{session_id}/encounter", response_model=EncounterResponse)
async def generate_encounter(session_id: str, body: EncounterRequest, db: AsyncSession = Depends(get_db)) -> EncounterResponse:
    """Generate a random encounter based on party level and environment."""
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")
    
    # Validate inputs
    valid_envs = set(SRD_MONSTERS.keys())
    if body.environment not in valid_envs:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Environment must be one of: {', '.join(sorted(valid_envs))}"
        )
    
    valid_difficulties = {"easy", "medium", "hard", "deadly"}
    if body.difficulty not in valid_difficulties:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Difficulty must be one of: {', '.join(sorted(valid_difficulties))}"
        )
    
    party_level = max(1, min(20, body.party_level))
    
    # Get monsters for this environment
    environment_monsters = SRD_MONSTERS[body.environment]
    
    # Get target CR range
    cr_low, cr_high = _get_cr_value(body.difficulty, party_level)
    
    # Find available CRs in range
    available_crs = [cr for cr in environment_monsters.keys() if cr_low <= cr <= cr_high]
    
    if not available_crs:
        # Fallback: use closest CR
        all_crs = sorted(environment_monsters.keys())
        closest_cr = min(all_crs, key=lambda x: abs(x - (cr_low + cr_high) / 2))
        available_crs = [closest_cr]
    
    # Generate encounter
    enemies: List[EnemyData] = []
    total_xp = 0
    target_xp = XP_THRESHOLDS.get(party_level, XP_THRESHOLDS[10]).get(body.difficulty, 100) * 4  # 4 party members baseline
    
    # Randomly select 1-3 enemy types
    num_types = random.randint(1, 3)
    for _ in range(num_types):
        selected_cr = random.choice(available_crs)
        monster_template = random.choice(environment_monsters[selected_cr])
        
        # Determine count based on difficulty and XP budget
        cr_xp = selected_cr * 100  # Approximate XP per CR
        count = max(1, min(8, int((target_xp - total_xp) / (cr_xp * 0.7))))
        
        if total_xp >= target_xp * 0.8:
            count = max(1, count // 2)
        
        enemy = EnemyData(
            name=monster_template["name"],
            hp=monster_template["hp"],
            ac=monster_template["ac"],
            cr=selected_cr,
            count=count,
            damage_type=_srd_damage_type(monster_template["name"]),
        )
        enemies.append(enemy)
        total_xp += int(cr_xp * count)
    
    # Ensure we have at least one enemy
    if not enemies:
        selected_cr = random.choice(available_crs)
        monster_template = random.choice(environment_monsters[selected_cr])
        enemies = [EnemyData(
            name=monster_template["name"],
            hp=monster_template["hp"],
            ac=monster_template["ac"],
            cr=selected_cr,
            count=1,
            damage_type=_srd_damage_type(monster_template["name"]),
        )]
        total_xp = int(selected_cr * 100)
    
    # Recalculate actual difficulty
    actual_difficulty = _calculate_encounter_difficulty(total_xp, 4, party_level)
    
    # Get flavor text
    description = random.choice(ENVIRONMENT_DESCRIPTIONS[body.environment])
    
    return EncounterResponse(
        enemies=enemies,
        total_xp=total_xp,
        difficulty_rating=actual_difficulty,
        description=description
    )




class LootItem(BaseModel):
    """A single loot item."""
    name: str = Field(..., description="Item name")
    description: str = Field(default="", description="Item description")
    rarity: str = Field(default="common", description="Rarity: common, uncommon, rare, very-rare, legendary")
    quantity: int = Field(default=1, description="How many")
    item_type: str = Field(default="misc", description="Type: weapon, armor, potion, scroll, ring, misc")


class AddLootRequest(BaseModel):
    """Request to add loot to the party."""
    items: List[LootItem]


class GoldTransactionRequest(BaseModel):
    """Request to add/subtract gold."""
    amount: int = Field(..., description="Gold amount (negative to subtract)")
    reason: str = Field(default="", description="Reason for transaction")


@router.get("/sessions/{session_id}/loot")
async def get_party_loot(session_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    """Get the party's loot inventory."""
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")
    return {
        "items": session.get("party_loot", []),
        "gold": session.get("party_gold", 0),
    }


@router.post("/sessions/{session_id}/loot")
async def add_party_loot(session_id: str, body: AddLootRequest, db: AsyncSession = Depends(get_db)) -> dict:
    """Add loot items to the party inventory."""
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")
    if "party_loot" not in session:
        session["party_loot"] = []
    for item in body.items:
        session["party_loot"].append(item.model_dump())
    await repo.save_game_session(db, session)
    return {"items": session["party_loot"], "gold": session.get("party_gold", 0)}


@router.post("/sessions/{session_id}/gold")
async def update_party_gold(session_id: str, body: GoldTransactionRequest, db: AsyncSession = Depends(get_db)) -> dict:
    """Add or subtract gold from the party."""
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")
    current = session.get("party_gold", 0)
    new_total = max(0, current + body.amount)
    session["party_gold"] = new_total
    await repo.save_game_session(db, session)
    return {"gold": new_total, "transaction": f"{'+' if body.amount >= 0 else ''}{body.amount} GP — {body.reason or 'adjustment'}"}


# ─── Loot Distribution ────────────────────────────────────────────────


class DistributeLootRequest(BaseModel):
    """Request to distribute a loot item to a character."""
    item_index: int = Field(..., ge=0, description="Index of item in party_loot list")
    character_id: str = Field(..., description="Character to receive the item")
    quantity: int = Field(default=1, ge=1, description="Quantity to give (for stackable items)")


@router.post("/sessions/{session_id}/distribute-loot")
async def distribute_loot(session_id: str, body: DistributeLootRequest, db: AsyncSession = Depends(get_db)) -> dict:
    """Move a loot item from party inventory to a character's inventory."""
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")
    character = await repo.get_character(db, body.character_id)
    if character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")

    party_loot = session.get("party_loot", [])

    if body.item_index >= len(party_loot):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid item index")

    item = party_loot[body.item_index]
    available = item.get("quantity", 1)
    take = min(body.quantity, available)

    if "inventory" not in character:
        character["inventory"] = []

    label = item["name"] if take == 1 else f"{item['name']} x{take}"
    character["inventory"].append(label)

    if "structured_inventory" not in character:
        character["structured_inventory"] = []
    distributed_item = {**item, "quantity": take}
    character["structured_inventory"].append(distributed_item)

    # Reduce or remove from party loot
    remaining = available - take
    if remaining <= 0:
        party_loot.pop(body.item_index)
    else:
        item["quantity"] = remaining

    await repo.save_game_session(db, session)
    await repo.save_character(db, character)

    return {
        "distributed": {"item": item["name"], "quantity": take, "to": character.get("name", body.character_id)},
        "party_loot": party_loot,
        "character_inventory": character["inventory"],
    }


# ─── XP Auto-Award from Game Events ───────────────────────────────────

# CR-based XP values (D&D 5e standard)
CR_XP_VALUES = {
    "0": 10, "1/8": 25, "1/4": 50, "1/2": 100,
    "1": 200, "2": 450, "3": 700, "4": 1100, "5": 1800,
    "6": 2300, "7": 2900, "8": 3900, "9": 5000, "10": 5900,
    "11": 7200, "12": 8400, "13": 10000, "14": 11500, "15": 13000,
    "16": 15000, "17": 18000, "18": 20000, "19": 22000, "20": 25000,
}


class XPEventRequest(BaseModel):
    """Structured XP event from the DM (combat victory, quest completion, etc)."""
    event_type: str = Field(..., description="Type: combat, quest, milestone, discovery, roleplay")
    description: str = Field(default="", description="What happened")
    xp_total: Optional[int] = Field(None, ge=0, description="Total XP to split (if known)")
    cr: Optional[str] = Field(None, description="CR of defeated creature (auto-calculates XP)")
    creature_count: int = Field(default=1, ge=1, description="Number of creatures defeated")
    character_ids: List[str] = Field(default_factory=list, description="Characters to award XP to (empty = all in campaign)")


class XPEventResponse(BaseModel):
    """Response after awarding XP from a game event."""
    total_xp: int
    xp_per_character: int
    awards: List[dict]


async def _apply_xp_award(db: AsyncSession, char_ids: List[str], total_xp: int) -> tuple[int, list[dict]]:
    """Split total_xp evenly across char_ids, persist to each character
    (bumping level + queuing pending_level_ups when a threshold is crossed),
    and return (xp_each, awards)."""
    xp_each = total_xp // len(char_ids) if char_ids else 0
    awards = []

    for cid in char_ids:
        character = await repo.get_character(db, cid)
        old_xp = character.get("experience_points", 0)
        old_level = character.get("level", 1)
        character["experience_points"] = old_xp + xp_each

        from app.api.routes.characters import _level_for_xp
        new_level = _level_for_xp(character["experience_points"])
        leveled_up = new_level > old_level
        if leveled_up:
            character["level"] = new_level
            pending = character.get("pending_level_ups", [])
            for lvl in range(old_level + 1, new_level + 1):
                pending.append({
                    "from_level": lvl - 1,
                    "to_level": lvl,
                    "choices_made": False,
                    "hp_rolled": False,
                })
            character["pending_level_ups"] = pending

        await repo.save_character(db, character)

        awards.append({
            "character_id": cid,
            "character_name": character.get("name", "Unknown"),
            "xp_awarded": xp_each,
            "total_xp": character["experience_points"],
            "old_level": old_level,
            "new_level": new_level,
            "leveled_up": leveled_up,
        })

    return xp_each, awards


@router.post("/sessions/{session_id}/xp-event", response_model=XPEventResponse)
async def award_xp_event(session_id: str, body: XPEventRequest, db: AsyncSession = Depends(get_db)) -> XPEventResponse:
    """Award XP to characters from a game event (combat, quest, etc)."""
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")

    campaign_id = session.get("campaign_id", "")
    campaign = await repo.get_campaign(db, campaign_id) or {}

    # Determine total XP
    if body.xp_total is not None:
        total_xp = body.xp_total
    elif body.cr is not None:
        per_creature = CR_XP_VALUES.get(body.cr, 0)
        total_xp = per_creature * body.creature_count
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Must provide either xp_total or cr")

    # Determine recipients
    if body.character_ids:
        char_ids = []
        for cid in body.character_ids:
            if await repo.character_exists(db, cid):
                char_ids.append(cid)
    else:
        char_ids = []
        for cid in campaign.get("character_ids", []):
            if await repo.character_exists(db, cid):
                char_ids.append(cid)

    if not char_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid characters to award XP to")

    xp_each, awards = await _apply_xp_award(db, char_ids, total_xp)

    # Log the event to session
    xp_log = session.get("xp_log", [])
    xp_log.append({
        "event_type": body.event_type,
        "description": body.description,
        "total_xp": total_xp,
        "xp_per_character": xp_each,
        "character_ids": char_ids,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    session["xp_log"] = xp_log
    await repo.save_game_session(db, session)

    return XPEventResponse(total_xp=total_xp, xp_per_character=xp_each, awards=awards)



# ─── Level-Up Management ──────────────────────────────────────────────


class LevelUpChoices(BaseModel):
    """Player's choices for a level-up."""
    ability_score_increase: Optional[dict] = Field(None, description="ASI choices, e.g. {'strength': 2} or {'dex': 1, 'con': 1}")
    hp_method: Optional[str] = Field(None, description="'average' or 'roll' — when 'roll', the server rolls the hit die itself")
    hp_roll: Optional[int] = Field(None, description="Legacy client-supplied HP roll result; validated against the class hit die (1..hit_die)")
    new_spells: List[str] = Field(default_factory=list, description="New spells learned (max 2 per level-up)")
    new_skill: Optional[str] = Field(None, description="New skill proficiency (if applicable)")
    feat: Optional[str] = Field(None, description="Feat chosen (instead of ASI)")


# Hit dice by class
_HIT_DICE = {
    "barbarian": 12, "fighter": 10, "paladin": 10, "ranger": 10,
    "bard": 8, "cleric": 8, "druid": 8, "monk": 8, "rogue": 8, "warlock": 8,
    "sorcerer": 6, "wizard": 6,
}

# ASI levels (standard D&D 5e)
_ASI_LEVELS = {4, 8, 12, 16, 19}

MAX_NEW_SPELLS_PER_LEVEL_UP = 2


@router.get("/spellbook")
async def get_spellbook() -> dict:
    """Curated combat-capable spells (see rules/spellbook.py) for the
    level-up spell picker. Not the full SRD spell list — only spells the
    deterministic combat engine can actually cast."""
    from app.services.rules.spellbook import SPELLBOOK

    spells = sorted(
        (
            {"name": s.name, "level": s.level, "is_cantrip": s.is_cantrip, "school": s.school.value}
            for s in SPELLBOOK.values()
        ),
        key=lambda s: (s["level"], s["name"]),
    )
    return {"spells": spells}


@router.get("/characters/{character_id}/pending-level-ups")
async def get_pending_level_ups(character_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    """Get any pending level-up choices for a character."""
    character = await repo.get_character(db, character_id)
    if character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    return {
        "character_id": character_id,
        "character_name": character.get("name", "Unknown"),
        "level": character.get("level", 1),
        "pending": character.get("pending_level_ups", []),
    }


@router.post("/characters/{character_id}/apply-level-up")
async def apply_level_up(character_id: str, body: LevelUpChoices, db: AsyncSession = Depends(get_db)) -> dict:
    """Apply level-up choices to a character."""
    character = await repo.get_character(db, character_id)
    if character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")

    pending = character.get("pending_level_ups", [])
    if not pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No pending level-ups")

    level_up = pending[0]  # Process the oldest pending level-up
    to_level = level_up["to_level"]
    class_name = character.get("class_name", "fighter").lower()

    # 1. HP increase — 'roll' asks the server to roll the hit die itself
    # (a client-supplied roll can't be trusted); a bare hp_roll is kept for
    # older callers but validated against the die so it can't be forged.
    hit_die = _HIT_DICE.get(class_name, 8)
    con_mod = (character.get("constitution", 10) - 10) // 2
    hp_roll_result: Optional[int] = None
    if body.hp_method == "roll":
        from app.services.dice import DiceRoller
        hp_roll_result = DiceRoller().roll(f"1d{hit_die}").total
        hp_gain = max(1, hp_roll_result + con_mod)
    elif body.hp_roll is not None:
        if not (1 <= body.hp_roll <= hit_die):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"hp_roll must be between 1 and {hit_die} for this class",
            )
        hp_roll_result = body.hp_roll
        hp_gain = max(1, body.hp_roll + con_mod)
    else:
        # Take the average (rounded up)
        hp_gain = max(1, (hit_die // 2 + 1) + con_mod)

    character["hp"] = character.get("hp", 8) + hp_gain
    if character.get("max_hp"):
        character["max_hp"] = character["max_hp"] + hp_gain
    else:
        character["max_hp"] = character["hp"]

    # 2. ASI or Feat (only at ASI levels) — validate the full ASI budget
    # BEFORE mutating any ability score, so a request that goes over +2
    # never leaves the character partially modified.
    if to_level in _ASI_LEVELS:
        if body.feat:
            features = character.get("features", [])
            features.append(f"Feat: {body.feat}")
            character["features"] = features
        elif body.ability_score_increase:
            ability_map = {
                "str": "strength", "strength": "strength",
                "dex": "dexterity", "dexterity": "dexterity",
                "con": "constitution", "constitution": "constitution",
                "int": "intelligence", "intelligence": "intelligence",
                "wis": "wisdom", "wisdom": "wisdom",
                "cha": "charisma", "charisma": "charisma",
            }
            if sum(body.ability_score_increase.values()) > 2:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="ASI total cannot exceed +2")
            for ability, increase in body.ability_score_increase.items():
                full_name = ability_map.get(ability.lower(), ability.lower())
                if full_name in character:
                    character[full_name] = min(20, character[full_name] + increase)

    # 3. New spells (capped + deduped — full class-spell-list validation is
    # out of scope for this curated combat engine, see rules/spellbook.py)
    if body.new_spells:
        if len(body.new_spells) > MAX_NEW_SPELLS_PER_LEVEL_UP:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot learn more than {MAX_NEW_SPELLS_PER_LEVEL_UP} new spells per level-up",
            )
        spells = character.get("spells_known", [])
        for name in body.new_spells:
            if name not in spells:
                spells.append(name)
        character["spells_known"] = spells

    # 4. New skill
    if body.new_skill:
        skills = character.get("skills", [])
        if body.new_skill not in skills:
            skills.append(body.new_skill)
            character["skills"] = skills

    # 5. Update proficiency bonus
    character["proficiency_bonus"] = (to_level - 1) // 4 + 2

    # Mark this level-up as complete
    level_up["choices_made"] = True
    level_up["hp_rolled"] = True
    pending.pop(0)
    character["pending_level_ups"] = pending

    await repo.save_character(db, character)

    return {
        "character_id": character_id,
        "level": character.get("level", 1),
        "hp_gained": hp_gain,
        "hp_roll_result": hp_roll_result,
        "changes_applied": True,
        "remaining_level_ups": len(pending),
        "character": character,
    }


# ─── Multiplayer: Room Codes & Join ────────────────────────────────────


class JoinRequest(BaseModel):
    """Schema for joining a game session via room code."""
    room_code: str = Field(..., description="4-letter room code")
    player_name: str = Field(..., description="Player's display name")
    character_id: Optional[str] = Field(default=None, description="Optional character ID to use")
    player_id: Optional[str] = Field(default=None, description="Previous player ID for rejoin")
    device_id: Optional[str] = Field(default=None, description="Stable id for this phone")


@router.get("/sessions/{session_id}/room-code")
async def get_room_code(session_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    """Get or create the room code for a session."""
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")

    code = session.get("room_code")
    if not code:
        code = storage.generate_room_code()
        storage.room_codes[code] = session_id
        storage.flush("room_codes")
        session["room_code"] = code
        await repo.save_game_session(db, session)

    return {"room_code": code, "session_id": session_id}


@router.post("/join")
async def join_game(body: JoinRequest, db: AsyncSession = Depends(get_db)) -> dict:
    """Join a game session using a room code."""
    code = body.room_code.strip().upper()
    session_id = storage.room_codes.get(code)
    if not session_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid room code")
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid room code")

    # Same phone (player id or device) or the same name reclaims the stale
    # row instead of adding a duplicate. A hero already on that seat is kept;
    # picking a different one is select-character.
    from app.api.roster import reconcile_seat

    seat, rejoined = reconcile_seat(
        session_id,
        name=body.player_name,
        player_id=body.player_id,
        device_id=body.device_id,
        character_id=body.character_id,
    )

    return {
        "session_id": session_id,
        "player_id": seat["id"],
        "campaign_id": session.get("campaign_id", ""),
        "rejoined": rejoined,
        "character_id": seat.get("character_id"),
        "previous_character_id": seat.get("previous_character_id"),
    }


@router.get("/resolve-code/{room_code}")
async def resolve_room_code(room_code: str, db: AsyncSession = Depends(get_db)) -> dict:
    """Resolve a room code to its session WITHOUT joining the roster.

    Used by read-only observers so they can find the session from the
    table's room code with zero side effects on the game.
    """
    code = room_code.strip().upper()
    session_id = storage.room_codes.get(code)
    if not session_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid room code")
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid room code")
    return {"session_id": session_id, "campaign_id": session.get("campaign_id", "")}


@router.get("/sessions/{session_id}/players")
async def get_session_players(session_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    """Get the list of players in a session."""
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")
    from app.api.roster import visible_players

    return {"players": visible_players(session_id)}


class SelectCharacterRequest(BaseModel):
    """Schema for claiming a character in a multiplayer session."""
    player_id: str = Field(..., description="Player ID from /game/join")
    character_id: str = Field(..., description="Character to claim")


@router.post("/sessions/{session_id}/select-character")
async def select_character(
    session_id: str, body: SelectCharacterRequest, db: AsyncSession = Depends(get_db)
) -> dict:
    """Claim a character for a player — enforces one player per character.

    Without this, two phones could silently pick the same hero and combat
    turns for the unclaimed characters would stall forever.
    """
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")

    from app.api.roster import release_character_from_absent, visible_players

    players = storage.session_players.get(session_id, [])
    me = next((p for p in players if p.get("id") == body.player_id), None)
    if me is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found in session")

    # A seat that left the table does not keep the hero. Someone still here does.
    release_character_from_absent(session_id, body.character_id, body.player_id)
    taken_by = next(
        (
            p for p in players
            if p.get("character_id") == body.character_id
            and p.get("id") != body.player_id
            and p.get("present") is not False
        ),
        None,
    )
    if taken_by is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Character already claimed by {taken_by.get('name', 'another player')}",
        )

    me["character_id"] = body.character_id
    me["present"] = True
    storage.flush("session_players")

    from app.api.websockets.game_ws import manager
    await manager.broadcast(session_id, {
        "type": "player_update",
        "players": visible_players(session_id),
        "connection_count": manager.get_connection_count(session_id),
    })

    return {"ok": True, "player_id": body.player_id, "character_id": body.character_id}


# ─── TTS Narration ──────────────────────────────────────────────────────


class NarrateTTSRequest(BaseModel):
    """Request TTS audio for narration text."""
    text: str = Field(..., description="Narration text to synthesize")


@router.post("/sessions/{session_id}/narrate-tts")
async def narrate_tts(session_id: str, body: NarrateTTSRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Synthesize narration text to audio and return MP3 bytes."""
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")

    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Text is required")

    # Use configured TTS provider from app state, fall back to fake
    from app.services.voice.tts import FakeTTS
    tts = getattr(request.app.state, "tts", FakeTTS())

    try:
        audio_bytes = await tts.synthesize(text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {e}")

    from fastapi.responses import Response
    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={"Content-Disposition": "inline; filename=narration.mp3"},
    )


# ─── Scene Image Generation ─────────────────────────────────────────────

SCENE_IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "generated_scenes")
os.makedirs(SCENE_IMAGES_DIR, exist_ok=True)

# Curated prompts per scene type for high-quality, consistent backgrounds
_SCENE_PROMPTS: dict[str, str] = {
    "tavern": "interior of a medieval fantasy tavern, warm firelight, wooden beams, mugs of ale on tables, cozy atmosphere",
    "dungeon": "dark underground dungeon corridor, stone walls, flickering torchlight, iron chains, ominous shadows",
    "forest": "ancient enchanted forest at twilight, massive trees, dappled moonlight, mystical fog between trunks",
    "cave": "vast underground cavern with glowing crystals, stalactites, underground river, bioluminescent fungi",
    "castle": "grand medieval castle throne room, tall stone pillars, stained glass windows, banners hanging from walls",
    "battlefield": "aftermath of a medieval battle, scorched earth, broken weapons, smoke rising, dramatic sky",
    "temple": "ancient stone temple interior, divine light streaming through cracks, altar with offerings, mystical runes",
    "market": "bustling medieval fantasy marketplace, colorful stalls, exotic wares, crowded cobblestone street",
    "ship": "deck of a fantasy sailing ship at sea, billowing sails, stormy horizon, wooden railing and rigging",
    "mountain": "dramatic mountain pass at dawn, jagged peaks, narrow trail along cliff edge, clouds below",
    "swamp": "murky fantasy swamp, gnarled dead trees, green fog, glowing eyes in darkness, still dark water",
    "desert": "vast fantasy desert with ancient ruins half-buried in sand, scorching sun, heat shimmer",
    "village": "quiet medieval village at dusk, thatched cottages, dirt road, smoke from chimneys, lantern light",
    "camp": "adventurer campsite in wilderness at night, campfire, bedrolls, starry sky, surrounding darkness",
    "road": "winding dirt road through rolling hills, distant mountains, dramatic clouds, lone waystone marker",
}

_SCENE_STYLE_SUFFIX = (
    "wide panoramic landscape, dark fantasy digital painting, atmospheric, "
    "dramatic cinematic lighting, muted earth tones, painterly style, "
    "no text, no characters, no watermark, no UI elements"
)


def _scene_cache_key(scene_type: str) -> str:
    """Deterministic cache key from scene type."""
    return hashlib.sha256(scene_type.encode()).hexdigest()[:16]


def _get_cached_scene_path(scene_type: str) -> str | None:
    """Return filesystem path if cached image exists."""
    key = _scene_cache_key(scene_type)
    for ext in (".jpg", ".png"):
        path = os.path.join(SCENE_IMAGES_DIR, f"{key}{ext}")
        if os.path.exists(path):
            return path
    return None


async def _generate_scene_dalle(scene_type: str) -> str | None:
    """Generate scene image via OpenAI's image API (gpt-image-1). Returns file path or None."""
    if not settings.openai_api_key:
        return None

    prompt_body = _SCENE_PROMPTS.get(scene_type, f"fantasy {scene_type} environment")
    prompt = f"{prompt_body}, {_SCENE_STYLE_SUFFIX}"

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-image-1",
                    "prompt": prompt,
                    "n": 1,
                    "size": "1536x1024",
                    "quality": "medium",
                },
            )
            resp.raise_for_status()
            image_data = resp.json()["data"][0]

            # API defaults to b64_json for this model/account; fall back to
            # downloading the url if the account's API version returns one.
            if "b64_json" in image_data:
                image_bytes = base64.b64decode(image_data["b64_json"])
            else:
                img_resp = await client.get(image_data["url"])
                img_resp.raise_for_status()
                image_bytes = img_resp.content

            key = _scene_cache_key(scene_type)
            path = os.path.join(SCENE_IMAGES_DIR, f"{key}.jpg")
            with open(path, "wb") as f:
                f.write(image_bytes)

            logger.info("Scene image generated for '%s' (%d bytes)", scene_type, len(image_bytes))
            return path
    except Exception as e:
        logger.warning("Scene image generation failed for '%s': %s", scene_type, e)
        return None


async def _generate_scene_pollinations(scene_type: str) -> str | None:
    """Generate scene image via Pollinations.ai (free, no API key). Returns file path or None."""
    prompt_body = _SCENE_PROMPTS.get(scene_type, f"fantasy {scene_type} environment")
    prompt = f"{prompt_body}, {_SCENE_STYLE_SUFFIX}"
    encoded = urllib.parse.quote(prompt)
    seed = int(hashlib.sha256(scene_type.encode()).hexdigest()[:8], 16)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1792&height=1024&seed={seed}&nologo=true"

    try:
        async with httpx.AsyncClient(timeout=90.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()

            if len(resp.content) < 5000:
                logger.warning("Pollinations returned suspiciously small image for '%s'", scene_type)
                return None

            key = _scene_cache_key(scene_type)
            path = os.path.join(SCENE_IMAGES_DIR, f"{key}.jpg")
            with open(path, "wb") as f:
                f.write(resp.content)

            logger.info("Pollinations scene image generated for '%s' (%d bytes)", scene_type, len(resp.content))
            return path
    except Exception as e:
        logger.warning("Pollinations scene generation failed for '%s': %s", scene_type, e)
        return None


class SceneImageRequest(BaseModel):
    """Request to generate a scene background image."""
    scene_type: str = Field(..., description="Scene type: tavern, dungeon, forest, etc.")
    description: Optional[str] = Field(default=None, description="Optional scene description for context")


class SceneImageResponse(BaseModel):
    """Response with the scene image URL."""
    image_url: str = Field(..., description="URL to the scene background image")
    scene_type: str = Field(..., description="Scene type this image represents")
    cached: bool = Field(default=False, description="Whether this was served from cache")


@router.post("/sessions/{session_id}/scene-image", response_model=SceneImageResponse)
async def generate_scene_image(
    session_id: str,
    body: SceneImageRequest,
    db: AsyncSession = Depends(get_db),
) -> SceneImageResponse:
    """Generate (or return cached) AI scene background image."""
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")

    scene_type = body.scene_type.strip().lower()
    if not scene_type:
        raise HTTPException(status_code=400, detail="scene_type is required")

    key = _scene_cache_key(scene_type)

    # Check cache first
    cached_path = _get_cached_scene_path(scene_type)
    if cached_path:
        url = f"/api/scene-images/{key}.jpg"
        # Persist in session for reload
        session["scene_image_url"] = url
        await repo.save_game_session(db, session)
        return SceneImageResponse(image_url=url, scene_type=scene_type, cached=True)

    # Generate: try DALL-E first, fall back to Pollinations
    path = await _generate_scene_dalle(scene_type)
    if not path:
        path = await _generate_scene_pollinations(scene_type)

    if not path:
        raise HTTPException(status_code=502, detail="Image generation failed — both providers unavailable")

    url = f"/api/scene-images/{key}.jpg"

    # Persist in session for reload
    session["scene_image_url"] = url
    await repo.save_game_session(db, session)

    return SceneImageResponse(image_url=url, scene_type=scene_type, cached=False)
