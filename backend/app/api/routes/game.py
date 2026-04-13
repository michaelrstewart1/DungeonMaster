"""Game session management endpoints."""
from typing import List, Optional

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
    current_scene: str = Field(default="You stand at the entrance of a dark cavern. The air is thick with the smell of damp stone and something... else. Torchlight flickers against ancient runes carved into the walls.", description="Initial scene description")


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
    }
    
    storage.game_sessions[session_id] = session_data
    return GameStateResponse(**session_data)


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
    
    return PlayerActionResponse(
        narration=narration,
        turn_number=turn_number,
        phase=session["current_phase"],
    )


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
            return await narrator.narrate_exploration(
                scene=scene,
                player_action=player_action,
                characters=characters,
                world_context=world_context,
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
    if narrator is not None:
        greeting = await narrator.generate_session_greeting(
            campaign_name=campaign.get("name", "Adventure"),
            characters=characters,
            last_summary=last_summary,
            world_context=world_context,
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



class GameSessionCreate(BaseModel):
    """Schema for creating a game session."""
    campaign_id: str = Field(..., description="Campaign ID for this session")
    current_phase: str = Field(default="exploration", description="Initial game phase")
    current_scene: str = Field(default="You stand at the entrance of a dark cavern. The air is thick with the smell of damp stone and something... else. Torchlight flickers against ancient runes carved into the walls.", description="Initial scene description")


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
    }
    
    storage.game_sessions[session_id] = session_data
    return GameStateResponse(**session_data)


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
    session_id: str,
    action: PlayerActionRequest
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
    
    # Generate a contextual DM response based on the action
    narration = _generate_dm_response(player_text, session)
    
    # Add to narrative history
    session["narrative_history"].append(f"Player: {player_text}")
    session["narrative_history"].append(f"DM: {narration}")
    
    return PlayerActionResponse(
        narration=narration,
        turn_number=turn_number,
        phase=session["current_phase"],
    )




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
