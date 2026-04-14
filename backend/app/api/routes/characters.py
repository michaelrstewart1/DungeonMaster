"""Character management endpoints."""
import json
import os
import urllib.parse
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.models.schemas import (
    CharacterCreate,
    CharacterImportRequest,
    CharacterResponse,
    CharacterUpdate,
)
from app.api import storage
from app.config import settings

# D&D 5e XP thresholds by level (index 0 = level 1, index 19 = level 20)
XP_THRESHOLDS: list[int] = [
    0, 300, 900, 2700, 6500, 14000, 23000, 34000, 48000, 64000,
    85000, 100000, 120000, 140000, 165000, 195000, 225000, 265000, 305000, 355000,
]

PORTRAITS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "generated_portraits",
)

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


@router.post("/{character_id}/generate-portrait", response_model=CharacterResponse)
async def generate_portrait(character_id: str) -> CharacterResponse:
    """Generate a DALL-E portrait for a character."""
    if character_id not in storage.characters:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")

    if not settings.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Portrait generation is not configured: missing OpenAI API key",
        )

    character = storage.characters[character_id]
    race = character.get("race", "human")
    class_name = character.get("class_name", "adventurer")

    prompt = (
        f"head-and-shoulders fantasy character portrait, {race} {class_name}, "
        "detailed face, dramatic lighting, dark fantasy digital painting, "
        "blurred background, no text, no watermark"
    )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "dall-e-3",
                    "prompt": prompt,
                    "n": 1,
                    "size": "1024x1024",
                    "response_format": "url",
                },
            )
            resp.raise_for_status()
            image_url = resp.json()["data"][0]["url"]

            # Download the generated image
            image_resp = await client.get(image_url)
            image_resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenAI API error: {exc.response.status_code} - {exc.response.text}",
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to reach OpenAI API: {exc}",
        )

    os.makedirs(PORTRAITS_DIR, exist_ok=True)
    filename = f"{character_id}.png"
    filepath = os.path.join(PORTRAITS_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(image_resp.content)

    character["portrait_url"] = f"/api/portraits/{filename}"
    return CharacterResponse(**character)


# ============================================================================
# XP / Progression
# ============================================================================

class AwardXPRequest(BaseModel):
    """Body for the award-xp endpoint."""
    xp: int = Field(..., gt=0, description="XP to award (must be positive)")
    reason: str = Field(..., min_length=1, description="Reason for the XP award")


class AwardXPResponse(BaseModel):
    """Response for the award-xp endpoint."""
    character: CharacterResponse
    leveled_up: bool
    new_level: Optional[int] = None


class Milestone(BaseModel):
    """A progression milestone."""
    level: int
    label: str
    reached: bool


class ProgressionResponse(BaseModel):
    """Response for the progression endpoint."""
    level: int
    xp: int
    xp_to_next: int
    xp_progress_pct: float
    milestones: List[Milestone]


def _level_for_xp(xp: int) -> int:
    """Return the level a character should be at for a given XP total."""
    level = 1
    for i in range(1, len(XP_THRESHOLDS)):
        if xp >= XP_THRESHOLDS[i]:
            level = i + 1
        else:
            break
    return min(level, 20)


def _xp_to_next_level(level: int, xp: int) -> int:
    """XP remaining until the next level. Returns 0 at level 20."""
    if level >= 20:
        return 0
    return XP_THRESHOLDS[level] - xp


def _xp_progress_pct(level: int, xp: int) -> float:
    """Percentage progress toward next level (0-100). 100 at level 20."""
    if level >= 20:
        return 100.0
    current_threshold = XP_THRESHOLDS[level - 1]
    next_threshold = XP_THRESHOLDS[level]
    span = next_threshold - current_threshold
    if span <= 0:
        return 100.0
    progress = xp - current_threshold
    return round(min(progress / span * 100, 100.0), 2)


# Class feature milestones (simplified – key levels with notable features)
_MILESTONES = [
    (4, "Ability Score Improvement"),
    (5, "Extra Attack / 3rd-level Spells"),
    (8, "Ability Score Improvement"),
    (12, "Ability Score Improvement"),
    (16, "Ability Score Improvement"),
    (19, "Ability Score Improvement"),
    (20, "Capstone Feature"),
]


@router.post("/{character_id}/award-xp", response_model=AwardXPResponse)
async def award_xp(character_id: str, body: AwardXPRequest) -> AwardXPResponse:
    """Award XP to a character and check for level-up."""
    if character_id not in storage.characters:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")

    character = storage.characters[character_id]
    old_level = character.get("level", 1)

    current_xp = character.get("experience_points", 0)
    character["experience_points"] = current_xp + body.xp

    new_level = _level_for_xp(character["experience_points"])
    leveled_up = new_level > old_level
    if leveled_up:
        character["level"] = new_level

    return AwardXPResponse(
        character=CharacterResponse(**character),
        leveled_up=leveled_up,
        new_level=new_level if leveled_up else None,
    )


@router.get("/{character_id}/progression", response_model=ProgressionResponse)
async def get_progression(character_id: str) -> ProgressionResponse:
    """Get XP progression info for a character."""
    if character_id not in storage.characters:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")

    character = storage.characters[character_id]
    level = character.get("level", 1)
    xp = character.get("experience_points", 0)

    milestones = [
        Milestone(level=mlvl, label=mlabel, reached=level >= mlvl)
        for mlvl, mlabel in _MILESTONES
    ]

    return ProgressionResponse(
        level=level,
        xp=xp,
        xp_to_next=_xp_to_next_level(level, xp),
        xp_progress_pct=_xp_progress_pct(level, xp),
        milestones=milestones,
    )


# ============================================================================
# JSON Export
# ============================================================================


@router.get("/{character_id}/export")
async def export_character(character_id: str) -> JSONResponse:
    """Export a character as a downloadable JSON file."""
    if character_id not in storage.characters:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")

    character = storage.characters[character_id]
    char_name = character.get("name", "character").replace(" ", "_").lower()

    return JSONResponse(
        content=character,
        headers={
            "Content-Disposition": f'attachment; filename="{char_name}.json"',
        },
    )


# ============================================================================
# Pollinations.ai Portrait Generation (free, no API key)
# ============================================================================

GENERATED_PORTRAITS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "generated_portraits",
)


async def _generate_pollinations_portrait(character_id: str, character: dict) -> str:
    """Generate a portrait using the free Pollinations.ai API."""
    race = character.get("race", "human")
    class_name = character.get("class_name", "adventurer")
    subrace = character.get("subrace", "")
    name = character.get("name", "adventurer")

    race_desc = f"{subrace} {race}" if subrace else race
    prompt = (
        f"dark fantasy portrait of a {race_desc} {class_name}, "
        f"detailed face, dramatic lighting, digital painting, "
        f"blurred background, no text, no watermark"
    )

    encoded = urllib.parse.quote(prompt)
    seed = abs(hash(f"{character_id}-{name}")) % 99999
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&seed={seed}&nologo=true"

    async with httpx.AsyncClient(timeout=180.0) as client:
        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        image_data = resp.content

        if len(image_data) < 1000:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Portrait generation returned too-small image",
            )

    os.makedirs(GENERATED_PORTRAITS_DIR, exist_ok=True)
    filename = f"{character_id}.jpg"
    filepath = os.path.join(GENERATED_PORTRAITS_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(image_data)

    return f"/api/portraits/{filename}"


@router.post("/{character_id}/generate-portrait-free", response_model=CharacterResponse)
async def generate_portrait_free(character_id: str) -> CharacterResponse:
    """Generate a free portrait using Pollinations.ai (no API key required)."""
    if character_id not in storage.characters:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")

    character = storage.characters[character_id]

    try:
        portrait_url = await _generate_pollinations_portrait(character_id, character)
        character["portrait_url"] = portrait_url
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Portrait generation failed: {exc}",
        )

    return CharacterResponse(**character)


# ── AI Character Detail Generation ──────────────────────────────

class AIGenerateRequest(BaseModel):
    """Request body for AI character detail generation."""
    field: str = Field(..., description="Which field to generate: name, personality_traits, ideals, bonds, flaws, backstory, full")
    race: str = ""
    class_name: str = ""
    subrace: str = ""
    subclass: str = ""
    background: str = ""
    alignment: str = ""
    name: str = ""
    personality_traits: str = ""
    ideals: str = ""
    bonds: str = ""
    flaws: str = ""
    backstory: str = ""


class AIGenerateResponse(BaseModel):
    """Response with AI-generated content."""
    field: str
    value: str
    values: Optional[Dict[str, str]] = None


_FIELD_PROMPTS = {
    "name": "Generate a single creative fantasy name for a {race} {class_name}. Just the name, nothing else. Make it sound authentic to the race.",
    "personality_traits": "Write 1-2 personality traits (2 sentences max) for a {race} {class_name} with the {background} background named {name}. Be specific and flavorful. Just the traits, no labels.",
    "ideals": "Write one ideal (1 sentence) for a {race} {class_name} with a {background} background named {name} who is {alignment}. What principle drives them? Just the ideal, no labels.",
    "bonds": "Write one bond (1 sentence) for a {race} {class_name} with a {background} background named {name}. What person, place, or thing do they care about most? Just the bond, no labels.",
    "flaws": "Write one flaw (1 sentence) for a {race} {class_name} with a {background} background named {name}. What weakness or vice could get them in trouble? Just the flaw, no labels.",
    "backstory": "Write a short backstory (3-5 sentences) for a {race} {class_name} with the {background} background named {name} who is {alignment}. Personality: {personality_traits}. Ideal: {ideals}. Bond: {bonds}. Flaw: {flaws}. Make it vivid and adventure-ready.",
}


@router.post("/generate-details", response_model=AIGenerateResponse)
async def generate_character_details(req: AIGenerateRequest, request: Request) -> AIGenerateResponse:
    """Use the AI to generate character details like name, backstory, personality."""
    from app.services.llm.base import LLMMessage

    narrator = getattr(request.app.state, "narrator", None)
    if narrator is None or narrator.llm is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI generation requires an LLM provider. Configure OPENAI_API_KEY or another provider.",
        )

    llm = narrator.llm
    context = {
        "race": req.race or "human",
        "class_name": req.class_name or "fighter",
        "subrace": req.subrace or "",
        "subclass": req.subclass or "",
        "background": req.background or "folk hero",
        "alignment": req.alignment or "neutral",
        "name": req.name or "the character",
        "personality_traits": req.personality_traits or "(not yet defined)",
        "ideals": req.ideals or "(not yet defined)",
        "bonds": req.bonds or "(not yet defined)",
        "flaws": req.flaws or "(not yet defined)",
        "backstory": req.backstory or "(not yet defined)",
    }

    if req.field == "full":
        results: Dict[str, str] = {}
        fields_order = ["name", "personality_traits", "ideals", "bonds", "flaws", "backstory"]
        for f in fields_order:
            prompt = _FIELD_PROMPTS[f].format(**context)
            try:
                resp = await llm.generate([
                    LLMMessage(role="system", content="You are a D&D 5e character creation assistant. Be creative, concise, and flavorful. Output ONLY the requested content with no labels, quotes, or markdown."),
                    LLMMessage(role="user", content=prompt),
                ])
                results[f] = resp.content.strip().strip('"').strip("'")
                context[f] = results[f]
            except Exception:
                results[f] = ""
        return AIGenerateResponse(field="full", value="", values=results)
    else:
        if req.field not in _FIELD_PROMPTS:
            raise HTTPException(status_code=400, detail=f"Unknown field: {req.field}. Valid: {list(_FIELD_PROMPTS.keys())}")

        prompt = _FIELD_PROMPTS[req.field].format(**context)
        try:
            resp = await llm.generate([
                LLMMessage(role="system", content="You are a D&D 5e character creation assistant. Be creative, concise, and flavorful. Output ONLY the requested content with no labels, quotes, or markdown."),
                LLMMessage(role="user", content=prompt),
            ])
            return AIGenerateResponse(field=req.field, value=resp.content.strip().strip('"').strip("'"))
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"AI generation failed: {exc}")