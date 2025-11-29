"""
API routes for Campaign entities.
Campaigns are stored in the gamerecords database.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from .models import Campaign, CampaignCreate, Change, Meta, EntityKind, StoryArc
from .database import get_gamerecords_db
from .services.llm import llm_service
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.get("", response_model=List[Campaign])
async def list_campaigns(realm_id: Optional[str] = Query(None)):
    """List campaigns, optionally filtered by realm_id."""
    db = get_gamerecords_db()

    query = {}
    if realm_id:
        query["realm_id"] = realm_id

    campaigns = await db.campaigns.find(query).to_list(length=100)
    return campaigns


@router.get("/{campaign_id}", response_model=Campaign)
async def get_campaign(campaign_id: str):
    """Get a specific campaign by ID."""
    db = get_gamerecords_db()
    campaign = await db.campaigns.find_one({"id": campaign_id})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.post("", response_model=Campaign)
async def create_campaign(campaign_data: CampaignCreate):
    """Create a new campaign, optionally generating story milestones via LLM."""
    db = get_gamerecords_db()

    # Generate unique ID
    campaign_id = f"campaign-{uuid.uuid4().hex[:8]}"

    # Generate milestones if requested
    milestones = []
    if campaign_data.generate_milestones and campaign_data.setting:
        try:
            logger.info(f"Generating milestones for campaign '{campaign_data.name}'")
            milestones = await llm_service.generate_campaign_milestones(
                campaign_name=campaign_data.name,
                setting=campaign_data.setting,
                num_milestones=5
            )
            logger.info(f"Generated {len(milestones)} milestones")
        except Exception as e:
            logger.warning(f"Failed to generate milestones: {e}")
            # Continue without milestones

    # Build story_arc with milestones
    story_arc = StoryArc(
        tagline=campaign_data.setting.get("goal") if campaign_data.setting else None,
        chapters=[],
        milestones=milestones if milestones else None
    )

    # Create campaign document
    campaign = Campaign(
        id=campaign_id,
        kind=EntityKind.CAMPAIGN,
        realm_id=campaign_data.realm_id,
        name=campaign_data.name,
        description=campaign_data.description,
        status=campaign_data.status,
        setting=campaign_data.setting,
        story_arc=story_arc if (story_arc.tagline or milestones) else None,
        meta=Meta(created_by=campaign_data.created_by),
        changes=[Change(by=campaign_data.created_by, type="created")]
    )

    # Insert into database
    await db.campaigns.insert_one(campaign.dict())

    # Update realm's campaigns list
    await db.realms.update_one(
        {"id": campaign_data.realm_id},
        {"$addToSet": {"campaigns": campaign_id}}
    )

    return campaign


@router.put("/{campaign_id}", response_model=Campaign)
async def update_campaign(campaign_id: str, campaign_data: CampaignCreate):
    """Update an existing campaign."""
    db = get_gamerecords_db()

    # Find existing campaign
    existing = await db.campaigns.find_one({"id": campaign_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Update fields
    existing["name"] = campaign_data.name
    existing["description"] = campaign_data.description
    existing["status"] = campaign_data.status

    # Add change record
    existing["changes"].append(
        Change(by=campaign_data.created_by, at=datetime.utcnow(), type="updated").dict()
    )

    # Save to database
    await db.campaigns.replace_one({"id": campaign_id}, existing)

    return Campaign(**existing)


@router.delete("/{campaign_id}")
async def delete_campaign(campaign_id: str):
    """Delete a campaign."""
    db = get_gamerecords_db()

    # Get campaign to find realm_id
    campaign = await db.campaigns.find_one({"id": campaign_id})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Remove from realm's campaigns list
    await db.realms.update_one(
        {"id": campaign["realm_id"]},
        {"$pull": {"campaigns": campaign_id}}
    )

    # Delete campaign
    result = await db.campaigns.delete_one({"id": campaign_id})

    return {"message": "Campaign deleted successfully"}
