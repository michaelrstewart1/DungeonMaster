"""Map state management endpoints."""
from typing import List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.models.schemas import MapCreate, MapResponse
from app.api import storage

router = APIRouter(prefix="/maps", tags=["maps"])


class TokenPositionUpdate(BaseModel):
    """Schema for moving a token."""
    x: int = Field(..., ge=0, description="X coordinate")
    y: int = Field(..., ge=0, description="Y coordinate")


class FogOfWarUpdate(BaseModel):
    """Schema for updating fog of war."""
    revealed: List[List[int]] = Field(..., description="List of [x, y] coordinates to reveal")


@router.get("/{session_id}", response_model=MapResponse)
async def get_map_state(session_id: str) -> MapResponse:
    """Get current map state for a game session."""
    if session_id not in storage.maps:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map not found"
        )
    
    map_data = storage.maps[session_id]
    return MapResponse(**map_data)


@router.put("/{session_id}", response_model=MapResponse)
async def update_map_state(session_id: str, map_create: MapCreate) -> MapResponse:
    """Update entire map state (create or replace)."""
    map_data = map_create.model_dump()
    map_data["id"] = session_id
    storage.maps[session_id] = map_data
    return MapResponse(**map_data)


@router.patch("/{session_id}/tokens/{token_id}/position", response_model=MapResponse)
async def move_token(
    session_id: str,
    token_id: str,
    position: TokenPositionUpdate
) -> MapResponse:
    """Move a single token to a new position."""
    if session_id not in storage.maps:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map not found"
        )
    
    map_data = storage.maps[session_id]
    
    # Find the token
    token = None
    for t in map_data["token_positions"]:
        if t["entity_id"] == token_id:
            token = t
            break
    
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found"
        )
    
    # Validate bounds
    if position.x >= map_data["width"] or position.y >= map_data["height"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token position out of bounds"
        )
    
    # Update position
    token["x"] = position.x
    token["y"] = position.y
    
    return MapResponse(**map_data)


@router.post("/{session_id}/fog", response_model=MapResponse)
async def update_fog_of_war(
    session_id: str,
    fog_update: FogOfWarUpdate
) -> MapResponse:
    """Update fog of war by revealing cells."""
    if session_id not in storage.maps:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map not found"
        )
    
    map_data = storage.maps[session_id]
    
    # Reveal cells
    for x, y in fog_update.revealed:
        if 0 <= x < map_data["width"] and 0 <= y < map_data["height"]:
            map_data["fog_of_war"][y][x] = False
    
    return MapResponse(**map_data)
