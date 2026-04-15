"""Campaign management endpoints."""
import random
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.schemas import CampaignCreate, CampaignResponse
from app.api import storage
import app.repository as repo

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

# Pool of evocative campaign names the randomizer can pick from
_RANDOM_NAMES = [
    "The Shattered Crown",
    "Ashes of the Old Gods",
    "The Forgotten Sea",
    "Blood and Shadow",
    "The Sunken Throne",
    "Echoes of Valdris",
    "The Long Night",
    "Masks of the Deceiver",
    "Where the Light Ends",
    "The Iron Covenant",
    "Grave of Empires",
    "The Hollow Court",
    "Tide of Ravens",
    "The Last Lantern",
    "Children of the Fallen Star",
]

_TONES = ["dark_fantasy", "gritty", "comedic", "storybook"]

_TONE_LABELS = {
    "dark_fantasy": "Dark Fantasy",
    "gritty": "Gritty Realism",
    "comedic": "Comedic Adventure",
    "storybook": "Storybook Wonder",
}


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CampaignResponse)
async def create_campaign(campaign: CampaignCreate, db: AsyncSession = Depends(get_db)) -> CampaignResponse:
    """Create a new campaign."""
    campaign_id = storage.generate_id()
    now = datetime.now(timezone.utc)
    
    campaign_data = {
        "id": campaign_id,
        "name": campaign.name,
        "description": campaign.description,
        "character_ids": campaign.character_ids,
        "world_state": campaign.world_state,
        "dm_settings": campaign.dm_settings,
        "created_at": now,
        "updated_at": now,
    }
    
    await repo.save_campaign(db, campaign_data)
    return CampaignResponse(**campaign_data)


@router.post("/randomize", status_code=status.HTTP_201_CREATED, response_model=CampaignResponse)
async def randomize_campaign(request: Request, db: AsyncSession = Depends(get_db)) -> CampaignResponse:
    """Create a fully randomized campaign with AI-generated world and story."""
    campaign_id = storage.generate_id()
    now = datetime.now(timezone.utc)

    name = random.choice(_RANDOM_NAMES)
    tone = random.choice(_TONES)
    tone_label = _TONE_LABELS[tone]

    narrator = getattr(request.app.state, "narrator", None)
    world_context = ""
    if narrator is not None:
        try:
            world_context = await narrator.generate_world(
                theme=tone,
                setting="",
                campaign_name=name,
                hooks=[],
            )
        except Exception:
            pass

    if not world_context:
        fallbacks = {
            "dark_fantasy": (
                f"The realm of {name.split()[0]} is shrouded in perpetual twilight. "
                "Ancient evils stir beneath crumbling cities, and the line between the "
                "living and the dead grows thinner each season."
            ),
            "gritty": (
                f"In the war-torn lands of {name.split()[0]}, no throne stays warm for long. "
                "Mercenaries, refugees, and desperate folk eke out survival while empires "
                "grind each other to dust."
            ),
            "comedic": (
                f"The wonderfully chaotic realm of {name.split()[0]} is home to bickering "
                "gods, incompetent villains, and taverns that are never where you left them. "
                "Somehow, you've been called to save it."
            ),
            "storybook": (
                f"Once upon a time, in the enchanted lands of {name.split()[0]}, magic "
                "was everywhere — in the songs of rivers, the whispers of old trees, and "
                "the hearts of brave adventurers who dared to dream."
            ),
        }
        world_context = fallbacks.get(tone, fallbacks["dark_fantasy"])

    campaign_data = {
        "id": campaign_id,
        "name": name,
        "description": f"A {tone_label} adventure. The DM has chosen your fate — embrace the unknown.",
        "character_ids": [],
        "world_state": {
            "context": world_context,
            "theme": tone,
            "setting": "",
        },
        "dm_settings": {"tone": tone},
        "created_at": now,
        "updated_at": now,
    }

    await repo.save_campaign(db, campaign_data)
    return CampaignResponse(**campaign_data)


@router.get("", response_model=List[CampaignResponse])
async def list_campaigns(db: AsyncSession = Depends(get_db)) -> List[CampaignResponse]:
    """List all campaigns."""
    campaigns = await repo.list_campaigns(db)
    return [CampaignResponse(**c) for c in campaigns]


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: str, db: AsyncSession = Depends(get_db)) -> CampaignResponse:
    """Get a specific campaign by ID."""
    campaign = await repo.get_campaign(db, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return CampaignResponse(**campaign)


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(campaign_id: str, campaign_update: CampaignCreate, db: AsyncSession = Depends(get_db)) -> CampaignResponse:
    """Update a campaign."""
    existing = await repo.get_campaign(db, campaign_id)
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    
    existing.update({
        "name": campaign_update.name,
        "description": campaign_update.description,
        "character_ids": campaign_update.character_ids,
        "world_state": campaign_update.world_state,
        "dm_settings": campaign_update.dm_settings,
        "updated_at": datetime.now(timezone.utc),
    })
    
    saved = await repo.save_campaign(db, existing)
    return CampaignResponse(**saved)


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(campaign_id: str, db: AsyncSession = Depends(get_db)) -> None:
    """Delete a campaign."""
    deleted = await repo.delete_campaign(db, campaign_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
