"""Character management endpoints."""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.models.schemas import (
    CharacterCreate,
    CharacterImportRequest,
    CharacterResponse,
    CharacterUpdate,
)
from app.api import storage

router = APIRouter(prefix="/characters", tags=["characters"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CharacterResponse)
async def create_character(character: CharacterCreate) -> CharacterResponse:
    """Create a new character and optionally link to a campaign."""
    character_id = storage.generate_id()
    
    char_dict = character.model_dump()
    campaign_id = char_dict.pop("campaign_id", None)
    
    character_data = {
        "id": character_id,
        **char_dict,
    }
    
    storage.characters[character_id] = character_data
    
    # Link character to campaign if campaign_id provided
    if campaign_id and campaign_id in storage.campaigns:
        campaign = storage.campaigns[campaign_id]
        if character_id not in campaign["character_ids"]:
            campaign["character_ids"].append(character_id)
    
    return CharacterResponse(**character_data)


def _parse_r20_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse r20Exporter JSON format into CharacterCreate fields."""
    attribs = data.get("attribs", [])
    attrib_map: Dict[str, str] = {}
    for attr in attribs:
        name = attr.get("name", "")
        current = attr.get("current", "")
        if name and current:
            attrib_map[name] = current

    ability_scores = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
    result: Dict[str, Any] = {"name": data.get("name", "Unknown")}

    for ability in ability_scores:
        if ability in attrib_map:
            try:
                result[ability] = int(attrib_map[ability])
            except (ValueError, TypeError):
                pass

    if "race" in attrib_map:
        result["race"] = attrib_map["race"].strip().lower()

    if "base_level" in attrib_map:
        base_level = attrib_map["base_level"].strip()
        parts = base_level.rsplit(" ", 1)
        if len(parts) == 2:
            result["class_name"] = parts[0].strip().lower()
            try:
                result["level"] = int(parts[1])
            except (ValueError, TypeError):
                result["class_name"] = base_level.lower()
                result["level"] = 1
        else:
            result["class_name"] = base_level.lower()
            result["level"] = 1

    if "hp" in attrib_map:
        try:
            result["hp"] = int(attrib_map["hp"])
        except (ValueError, TypeError):
            pass

    if "ac" in attrib_map:
        try:
            result["ac"] = int(attrib_map["ac"])
        except (ValueError, TypeError):
            pass

    return result


def _parse_generic_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse generic flat JSON format into CharacterCreate fields."""
    result = dict(data)
    if "race" in result and isinstance(result["race"], str):
        result["race"] = result["race"].strip().lower()
    if "class_name" in result and isinstance(result["class_name"], str):
        result["class_name"] = result["class_name"].strip().lower()
    return result


@router.post("/import", status_code=status.HTTP_201_CREATED, response_model=CharacterResponse)
async def import_character(request: CharacterImportRequest) -> CharacterResponse:
    """Import a character from an external format (r20 or generic)."""
    if request.format == "r20":
        parsed = _parse_r20_data(request.data)
    else:
        parsed = _parse_generic_data(request.data)

    try:
        character = CharacterCreate(**parsed)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to create character from imported data: {exc}",
        )

    character_id = storage.generate_id()
    character_data = {"id": character_id, **character.model_dump()}
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
