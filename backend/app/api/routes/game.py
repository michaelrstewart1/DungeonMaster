"""Game session management endpoints."""
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
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
    """Schema for submitting a player action."""
    character_id: str = Field(..., description="Character ID")
    action: str = Field(..., description="Action description")


class PlayerActionResponse(BaseModel):
    """Response to a player action."""
    narration: str = Field(..., description="DM narration in response to the action")


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
    
    # Simple mock implementation: echo back the action with a prefix
    narration = f"Character {action.character_id} {action.action}. The DM responds..."
    
    # Add to narrative history
    session["narrative_history"].append(narration)
    
    return PlayerActionResponse(narration=narration)


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
