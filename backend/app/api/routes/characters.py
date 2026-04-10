"""Character management endpoints."""
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.models.schemas import CharacterCreate, CharacterResponse, CharacterUpdate
from app.api import storage

router = APIRouter(prefix="/characters", tags=["characters"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CharacterResponse)
async def create_character(character: CharacterCreate) -> CharacterResponse:
    """Create a new character."""
    character_id = storage.generate_id()
    
    character_data = {
        "id": character_id,
        **character.model_dump(),
    }
    
    storage.characters[character_id] = character_data
    return CharacterResponse(**character_data)


@router.get("", response_model=List[CharacterResponse])
async def list_characters(campaign_id: Optional[str] = Query(None)) -> List[CharacterResponse]:
    """List all characters, optionally filtered by campaign."""
    characters = list(storage.characters.values())
    
    # Filter by campaign if provided
    if campaign_id:
        if campaign_id not in storage.campaigns:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
        
        campaign = storage.campaigns[campaign_id]
        character_ids_in_campaign = set(campaign["character_ids"])
        characters = [c for c in characters if c["id"] in character_ids_in_campaign]
    
    return [CharacterResponse(**character) for character in characters]


@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(character_id: str) -> CharacterResponse:
    """Get a specific character by ID."""
    if character_id not in storage.characters:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    
    return CharacterResponse(**storage.characters[character_id])


@router.put("/{character_id}", response_model=CharacterResponse)
async def update_character(character_id: str, character_update: CharacterUpdate) -> CharacterResponse:
    """Update a character (partial update supported)."""
    if character_id not in storage.characters:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    
    character = storage.characters[character_id]
    
    # Only update provided fields
    update_data = character_update.model_dump(exclude_unset=True)
    character.update(update_data)
    
    return CharacterResponse(**character)


@router.delete("/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character(character_id: str) -> None:
    """Delete a character."""
    if character_id not in storage.characters:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    
    del storage.characters[character_id]
