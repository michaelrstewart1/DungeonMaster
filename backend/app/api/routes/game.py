"""Game session management endpoints."""
from typing import List, Optional
from datetime import datetime, timezone
import random

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.models.schemas import GameStateResponse, CombatState
from app.models.enums import GamePhase
from app.api import storage

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


@router.post("/sessions", status_code=status.HTTP_201_CREATED, response_model=GameStateResponse)
async def create_game_session(session_create: GameSessionCreate) -> GameStateResponse:
    """Create a new game session for a campaign."""
    # Verify campaign exists
    if session_create.campaign_id not in storage.campaigns:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
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
    }
    
    storage.game_sessions[session_id] = session_data
    return GameStateResponse(**session_data)


@router.get("/sessions")
async def list_game_sessions(campaign_id: str | None = None) -> list[dict]:
    """List game sessions, optionally filtered by campaign_id."""
    sessions = []
    for sid, sdata in storage.game_sessions.items():
        if campaign_id and sdata.get("campaign_id") != campaign_id:
            continue
        sessions.append({
            "id": sid,
            "campaign_id": sdata.get("campaign_id", ""),
            "phase": sdata.get("current_phase", "exploration"),
            "turn_count": sdata.get("turn_count", 0),
            "created_at": sdata.get("created_at", ""),
            "scene": sdata.get("current_scene", "")[:120],
        })
    sessions.sort(key=lambda s: s.get("created_at", ""), reverse=True)
    return sessions


@router.get("/sessions/{session_id}/state", response_model=GameStateResponse)
async def get_game_state(session_id: str) -> GameStateResponse:
    """Get the current game state for a session."""
    if session_id not in storage.game_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game session not found"
        )
    
    return GameStateResponse(**storage.game_sessions[session_id])


@router.post("/sessions/{session_id}/action", response_model=PlayerActionResponse)
async def submit_player_action(
    request: Request,
    session_id: str,
    action: PlayerActionRequest,
) -> PlayerActionResponse:
    """Submit a player action to the game."""
    if session_id not in storage.game_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game session not found"
        )
    
    session = storage.game_sessions[session_id]
    player_text = action.resolved_action
    turn_number = len(session["narrative_history"])

    # Try real LLM narrator; fall back to keyword mock when no API key is set
    narrator = getattr(request.app.state, "narrator", None)
    narration = await _generate_dm_response(player_text, session, narrator)
    
    # Add to narrative history
    session["narrative_history"].append(f"Player: {player_text}")
    session["narrative_history"].append(f"DM: {narration}")
    session["turn_count"] = session.get("turn_count", 0) + 1

    # Detect effects from narration for frontend
    effects = _detect_effects(narration, player_text)
    mood_obj = _detect_mood(f"{session.get('current_scene', '')} {narration}")

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


async def _generate_dm_response(player_action: str, session: dict, narrator=None) -> str:
    """Generate a DM narrative response.

    Uses the real LLM narrator when available; falls back to keyword-matching
    mock responses so tests (which have no API key) continue to pass.
    """
    if narrator is not None:
        try:
            campaign_id = session.get("campaign_id", "")
            campaign = storage.campaigns.get(campaign_id, {})
            world_context = campaign.get("world_state", {}).get("context", "A perilous realm.")
            characters = [
                storage.characters[cid]
                for cid in campaign.get("character_ids", [])
                if cid in storage.characters
            ]
            scene = {
                "name": "Current Scene",
                "description": session.get("current_scene", ""),
            }
            story_bible = storage.story_bibles.get(campaign_id, "")
            return await narrator.narrate_exploration(
                scene=scene,
                player_action=player_action,
                characters=characters,
                world_context=world_context,
                story_bible=story_bible,
            )
        except Exception:
            pass  # fall through to keyword mock

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

    return (f"You {player_action}. The cavern seems to respond to your presence — "
            "shadows shift along the walls, and you hear a distant sound, like stone grinding "
            "against stone. Something has taken notice of you.")


@router.get("/sessions/{session_id}/greeting")
async def get_session_greeting(request: Request, session_id: str) -> dict:
    """Generate the session-opening greeting and last-session recap.

    Returns:
        {"greeting": "...wizard voice narration..."}
    """
    if session_id not in storage.game_sessions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")

    session = storage.game_sessions[session_id]
    campaign_id = session.get("campaign_id", "")
    campaign = storage.campaigns.get(campaign_id, {})
    characters = [
        storage.characters[cid]
        for cid in campaign.get("character_ids", [])
        if cid in storage.characters
    ]
    world_context = campaign.get("world_state", {}).get("context", "")
    last_summary = storage.session_summaries.get(campaign_id, "")

    narrator = getattr(request.app.state, "narrator", None)

    # Generate a story bible for this campaign if one doesn't exist yet
    if narrator is not None and campaign_id not in storage.story_bibles:
        tone = campaign.get("world_state", {}).get("theme", "dark_fantasy")
        try:
            bible = await narrator.generate_story_bible(
                campaign_name=campaign.get("name", "Adventure"),
                world_context=world_context,
                tone=tone,
            )
            storage.story_bibles[campaign_id] = bible
        except Exception:
            pass  # non-fatal; DM still works without it

    if narrator is not None:
        # Enrich world_context with the story bible's world section for the greeting
        bible = storage.story_bibles.get(campaign_id, "")
        greeting_world_context = world_context
        if bible and not world_context:
            # Use first paragraph of bible as world context hint for the greeting
            greeting_world_context = bible.split("\n\n")[0] if "\n\n" in bible else bible[:300]
        greeting = await narrator.generate_session_greeting(
            campaign_name=campaign.get("name", "Adventure"),
            characters=characters,
            last_summary=last_summary,
            world_context=greeting_world_context,
        )
    elif last_summary:
        greeting = (
            f"Welcome back, brave souls. When last we met, {last_summary} "
            "Now, the adventure continues — steel yourselves."
        )
    else:
        greeting = (
            "Welcome, adventurers. A world of danger and wonder awaits you. "
            "Your legend begins tonight — what will history remember of you?"
        )

    return {"greeting": greeting}


@router.post("/sessions/{session_id}/summary")
async def save_session_summary(
    request: Request, session_id: str, body: SessionSummaryRequest
) -> dict:
    """Save (or auto-generate) a session summary for next session's recap.

    If no summary is provided in the body, the narrator generates one from
    the narrative history.

    Returns:
        {"summary": "..."}
    """
    if session_id not in storage.game_sessions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")

    session = storage.game_sessions[session_id]
    campaign_id = session.get("campaign_id", "")
    campaign = storage.campaigns.get(campaign_id, {})

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

    storage.session_summaries[campaign_id] = summary
    return {"summary": summary}


@router.post("/world/generate")
async def generate_world(request: Request, body: WorldGenerateRequest) -> dict:
    """Generate a rich world context and store it in the campaign.

    Returns:
        {"world_context": "..."}
    """
    if body.campaign_id not in storage.campaigns:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    campaign = storage.campaigns[body.campaign_id]

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

    return {"world_context": world_context}


@router.post("/sessions/{session_id}/start-combat", response_model=GameStateResponse)
async def start_combat(session_id: str) -> GameStateResponse:
    """Start combat encounter in the session."""
    if session_id not in storage.game_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game session not found"
        )
    
    session = storage.game_sessions[session_id]
    session["current_phase"] = GamePhase.COMBAT.value
    session["combat_state"] = {
        "initiative_order": [],
        "current_turn_index": 0,
        "round_number": 1,
    }
    
    return GameStateResponse(**session)


@router.post("/sessions/{session_id}/end-combat", response_model=GameStateResponse)
async def end_combat(session_id: str) -> GameStateResponse:
    """End combat encounter in the session."""
    if session_id not in storage.game_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game session not found"
        )
    
    session = storage.game_sessions[session_id]
    session["current_phase"] = GamePhase.EXPLORATION.value
    session["combat_state"] = None
    
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


@router.get("/sessions/{session_id}/mood")
async def get_scene_mood(session_id: str) -> SceneMood:
    """Get the atmospheric mood of the current scene.

    Analyzes the current scene description and recent narrative to determine
    lighting, atmosphere, danger level, and suggested ambient sounds.
    """
    if session_id not in storage.game_sessions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")

    session = storage.game_sessions[session_id]
    scene = session.get("current_scene", "")
    # Include recent narrative for more context
    history = session.get("narrative_history", [])
    recent = " ".join(history[-4:]) if history else ""
    combined = f"{scene} {recent}"

    return _detect_mood(combined)


@router.get("/sessions/{session_id}/recap")
async def get_session_recap(session_id: str) -> dict:
    """Get the recap of the previous session for cinematic display.

    Returns the last session summary for the campaign so the frontend
    can show a dramatic "Previously on..." overlay.
    """
    if session_id not in storage.game_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game session not found",
        )

    session = storage.game_sessions[session_id]
    campaign_id = session.get("campaign_id", "")
    campaign = storage.campaigns.get(campaign_id, {})
    campaign_name = campaign.get("name", "Your Adventure")
    last_summary = storage.session_summaries.get(campaign_id, "")

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
async def generate_encounter(session_id: str, body: EncounterRequest) -> EncounterResponse:
    """Generate a random encounter based on party level and environment.
    
    Uses D&D 5e encounter building rules with CR-based enemy selection
    and XP threshold balancing.
    """
    if session_id not in storage.game_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game session not found"
        )
    
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
async def get_party_loot(session_id: str) -> dict:
    """Get the party's loot inventory."""
    if session_id not in storage.game_sessions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")
    session = storage.game_sessions[session_id]
    return {
        "items": session.get("party_loot", []),
        "gold": session.get("party_gold", 0),
    }


@router.post("/sessions/{session_id}/loot")
async def add_party_loot(session_id: str, body: AddLootRequest) -> dict:
    """Add loot items to the party inventory."""
    if session_id not in storage.game_sessions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")
    session = storage.game_sessions[session_id]
    if "party_loot" not in session:
        session["party_loot"] = []
    for item in body.items:
        session["party_loot"].append(item.model_dump())
    return {"items": session["party_loot"], "gold": session.get("party_gold", 0)}


@router.post("/sessions/{session_id}/gold")
async def update_party_gold(session_id: str, body: GoldTransactionRequest) -> dict:
    """Add or subtract gold from the party."""
    if session_id not in storage.game_sessions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found")
    session = storage.game_sessions[session_id]
    current = session.get("party_gold", 0)
    new_total = max(0, current + body.amount)
    session["party_gold"] = new_total
    return {"gold": new_total, "transaction": f"{'+' if body.amount >= 0 else ''}{body.amount} GP — {body.reason or 'adjustment'}"}
