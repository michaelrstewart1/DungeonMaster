"""Game session management endpoints."""
from typing import List, Optional
from datetime import datetime, timezone
import logging
import random

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import GameStateResponse, CombatState
from app.models.enums import GamePhase
from app.api import storage
from app.db import get_db
import app.repository as repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/game", tags=["game"])


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


@router.post("/sessions", status_code=status.HTTP_201_CREATED, response_model=GameStateResponse)
async def create_game_session(session_create: GameSessionCreate, db: AsyncSession = Depends(get_db)) -> GameStateResponse:
    """Create a new game session for a campaign."""
    campaign = await repo.get_campaign(db, session_create.campaign_id)
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    
    session_id = storage.generate_id()
    
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
        "environment": {
            "time_of_day": "dawn",
            "weather": "clear",
            "temperature": "cool",
            "season": "spring",
        },
    }
    
    await repo.save_game_session(db, session_data)

    # Auto-generate a room code for multiplayer join
    room_code = storage.generate_room_code()
    storage.room_codes[room_code] = session_id
    session_data["room_code"] = room_code
    storage.session_players[session_id] = []

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
        })
    sessions.sort(key=lambda s: s.get("created_at", ""), reverse=True)
    return sessions


@router.get("/sessions/{session_id}/state", response_model=GameStateResponse)
async def get_game_state(session_id: str, db: AsyncSession = Depends(get_db)) -> GameStateResponse:
    """Get the current game state for a session."""
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")
    return GameStateResponse(**session)


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

    # Try real LLM narrator; fall back to keyword mock when no API key is set
    narrator = getattr(request.app.state, "narrator", None)
    narration = await _generate_dm_response(player_text, session, narrator, db)
    
    # Add to narrative history
    session["narrative_history"].append(f"Player: {player_text}")
    session["narrative_history"].append(f"DM: {narration}")
    session["turn_count"] = session.get("turn_count", 0) + 1

    # Detect effects from narration for frontend
    effects = _detect_effects(narration, player_text)
    mood_obj = _detect_mood(f"{session.get('current_scene', '')} {narration}")

    # Auto-advance time and potentially change weather
    _advance_time(session)

    await repo.save_game_session(db, session)

    return PlayerActionResponse(
        narration=narration,
        turn_number=turn_number,
        phase=session["current_phase"],
        mood=mood_obj.atmosphere,
        effects=effects,
    )


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


async def _generate_dm_response(player_action: str, session: dict, narrator=None, db=None) -> str:
    """Generate a DM narrative response.

    Uses the real LLM narrator when available; falls back to keyword-matching
    mock responses so tests (which have no API key) continue to pass.
    """
    from app.services.llm.narrator import _strip_action_echo

    if narrator is not None and db is not None:
        try:
            import asyncio
            campaign_id = session.get("campaign_id", "")
            campaign = await repo.get_campaign(db, campaign_id) or {}
            world_context = campaign.get("world_state", {}).get("context", "A perilous realm.")
            char_ids = campaign.get("character_ids", [])
            characters = []
            for cid in char_ids:
                c = await repo.get_character(db, cid)
                if c:
                    characters.append(c)
            scene = {
                "name": "Current Scene",
                "description": session.get("current_scene", ""),
            }
            story_bible = await repo.get_campaign_story_bible(db, campaign_id) or ""
            result = await asyncio.wait_for(
                narrator.narrate_exploration(
                    scene=scene,
                    player_action=player_action,
                    characters=characters,
                    world_context=world_context,
                    story_bible=story_bible,
                ),
                timeout=45.0,
            )
            # Safety net: strip echoed player action even if narrator missed it
            stripped = _strip_action_echo(result, player_action)
            if stripped != result:
                logger.info("Echo stripped: '%s...' → '%s...'", result[:60], stripped[:60])
            return stripped
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

    return ("The cavern seems to respond to your presence — "
            "shadows shift along the walls, and you hear a distant sound, like stone grinding "
            "against stone. Something has taken notice of you.")


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

    if narrator is not None:
        greeting_world_context = world_context
        if existing_bible and not world_context:
            greeting_world_context = existing_bible.split("\n\n")[0] if "\n\n" in existing_bible else existing_bible[:300]
        try:
            greeting = await asyncio.wait_for(
                narrator.generate_session_greeting(
                    campaign_name=campaign.get("name", "Adventure"),
                    characters=characters,
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


# NPC Journal endpoints
class NPCData(BaseModel):
    """NPC data model."""
    name: str = Field(..., description="NPC name")
    npc_type: str = Field(..., description="NPC type (merchant, guard, wizard, etc.)")
    disposition: str = Field(default="unknown", description="Disposition (friendly, neutral, hostile, unknown)")
    location: str = Field(default="", description="Last known location")
    notes: str = Field(default="", description="Notes about the NPC")


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


@router.post("/sessions/{session_id}/start-combat", response_model=GameStateResponse)
async def start_combat(session_id: str, db: AsyncSession = Depends(get_db)) -> GameStateResponse:
    """Start combat encounter in the session."""
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")
    
    session["current_phase"] = GamePhase.COMBAT.value
    session["combat_state"] = {
        "initiative_order": [],
        "current_turn_index": 0,
        "round_number": 1,
    }
    await repo.save_game_session(db, session)
    return GameStateResponse(**session)


@router.post("/sessions/{session_id}/end-combat", response_model=GameStateResponse)
async def end_combat(session_id: str, db: AsyncSession = Depends(get_db)) -> GameStateResponse:
    """End combat encounter in the session."""
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")
    
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
            count=count
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
            count=1
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

    xp_each = total_xp // len(char_ids)
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
    hp_roll: Optional[int] = Field(None, description="HP roll result (if rolling; None = take average)")
    new_spells: List[str] = Field(default_factory=list, description="New spells learned")
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

    # 1. HP increase
    hit_die = _HIT_DICE.get(class_name, 8)
    con_mod = (character.get("constitution", 10) - 10) // 2
    if body.hp_roll is not None:
        hp_gain = max(1, body.hp_roll + con_mod)
    else:
        # Take the average (rounded up)
        hp_gain = max(1, (hit_die // 2 + 1) + con_mod)

    character["hp"] = character.get("hp", 8) + hp_gain
    if character.get("max_hp"):
        character["max_hp"] = character["max_hp"] + hp_gain
    else:
        character["max_hp"] = character["hp"]

    # 2. ASI or Feat (only at ASI levels)
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
            total_increase = 0
            for ability, increase in body.ability_score_increase.items():
                full_name = ability_map.get(ability.lower(), ability.lower())
                if full_name in character:
                    character[full_name] = min(20, character[full_name] + increase)
                    total_increase += increase
            if total_increase > 2:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="ASI total cannot exceed +2")

    # 3. New spells
    if body.new_spells:
        spells = character.get("spells_known", [])
        spells.extend(body.new_spells)
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

    player_id = storage.generate_id()
    player_info = {
        "id": player_id,
        "name": body.player_name,
        "character_id": body.character_id,
        "joined_at": datetime.now(timezone.utc).isoformat(),
    }

    if session_id not in storage.session_players:
        storage.session_players[session_id] = []
    storage.session_players[session_id].append(player_info)

    return {
        "session_id": session_id,
        "player_id": player_id,
        "campaign_id": session.get("campaign_id", ""),
    }


@router.get("/sessions/{session_id}/players")
async def get_session_players(session_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    """Get the list of players in a session."""
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")
    return {"players": storage.session_players.get(session_id, [])}


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
