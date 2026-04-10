"""Campaign management endpoints."""
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, HTTPException, status

from app.models.schemas import CampaignCreate, CampaignResponse
from app.api import storage

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CampaignResponse)
async def create_campaign(campaign: CampaignCreate) -> CampaignResponse:
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
    
    storage.campaigns[campaign_id] = campaign_data
    return CampaignResponse(**campaign_data)


@router.get("", response_model=List[CampaignResponse])
async def list_campaigns() -> List[CampaignResponse]:
    """List all campaigns."""
    return [CampaignResponse(**campaign) for campaign in storage.campaigns.values()]


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: str) -> CampaignResponse:
    """Get a specific campaign by ID."""
    if campaign_id not in storage.campaigns:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    
    return CampaignResponse(**storage.campaigns[campaign_id])


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(campaign_id: str, campaign_update: CampaignCreate) -> CampaignResponse:
    """Update a campaign."""
    if campaign_id not in storage.campaigns:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    
    campaign = storage.campaigns[campaign_id]
    campaign.update({
        "name": campaign_update.name,
        "description": campaign_update.description,
        "character_ids": campaign_update.character_ids,
        "world_state": campaign_update.world_state,
        "dm_settings": campaign_update.dm_settings,
        "updated_at": datetime.now(timezone.utc),
    })
    
    return CampaignResponse(**campaign)


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(campaign_id: str) -> None:
    """Delete a campaign."""
    if campaign_id not in storage.campaigns:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    
    del storage.campaigns[campaign_id]
