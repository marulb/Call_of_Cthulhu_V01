"""
API routes for NPC entities.
NPCs are stored in the gamerecords database in the entities collection.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from .models import NPC, NPCCreate, Change, Meta, EntityKind
from .database import get_gamerecords_db
from datetime import datetime
import uuid

router = APIRouter(prefix="/npcs", tags=["npcs"])


@router.get("", response_model=List[NPC])
async def list_npcs(
    campaign_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """List NPCs, optionally filtered by campaign_id and/or status."""
    db = get_gamerecords_db()

    query = {"kind": EntityKind.NPC.value}
    if campaign_id:
        query["campaign_id"] = campaign_id
    if status:
        query["status"] = status

    npcs = await db.entities.find(query).to_list(length=100)
    return npcs


@router.get("/{npc_id}", response_model=NPC)
async def get_npc(npc_id: str):
    """Get a specific NPC by ID."""
    db = get_gamerecords_db()
    npc = await db.entities.find_one({"id": npc_id, "kind": EntityKind.NPC.value})
    if not npc:
        raise HTTPException(status_code=404, detail="NPC not found")
    return npc


@router.post("", response_model=NPC)
async def create_npc(npc_data: NPCCreate):
    """Create a new NPC."""
    db = get_gamerecords_db()

    # Generate unique ID
    npc_id = f"npc-{uuid.uuid4().hex[:8]}"

    # Create NPC document
    npc = NPC(
        id=npc_id,
        kind=EntityKind.NPC,
        campaign_id=npc_data.campaign_id,
        name=npc_data.name,
        description=npc_data.description,
        role=npc_data.role or "neutral",
        personality=npc_data.personality or "",
        goals=npc_data.goals or [],
        knowledge=npc_data.knowledge or [],
        current_location=npc_data.current_location,
        status=npc_data.status or "active",
        meta=Meta(created_by=npc_data.created_by),
        changes=[Change(by=npc_data.created_by, type="created")]
    )

    # Insert into database
    await db.entities.insert_one(npc.dict())

    return npc


@router.put("/{npc_id}", response_model=NPC)
async def update_npc(npc_id: str, npc_data: NPCCreate):
    """Update an existing NPC."""
    db = get_gamerecords_db()

    # Find existing NPC
    existing = await db.entities.find_one({"id": npc_id, "kind": EntityKind.NPC.value})
    if not existing:
        raise HTTPException(status_code=404, detail="NPC not found")

    # Update fields
    existing["name"] = npc_data.name
    existing["description"] = npc_data.description
    existing["role"] = npc_data.role or "neutral"
    existing["personality"] = npc_data.personality or ""
    existing["goals"] = npc_data.goals or []
    existing["knowledge"] = npc_data.knowledge or []
    existing["current_location"] = npc_data.current_location
    existing["status"] = npc_data.status or "active"

    # Add change record
    existing["changes"].append(
        Change(by=npc_data.created_by, at=datetime.utcnow(), type="updated").dict()
    )

    # Save to database
    await db.entities.replace_one({"id": npc_id}, existing)

    return NPC(**existing)


@router.delete("/{npc_id}")
async def delete_npc(npc_id: str):
    """Delete an NPC."""
    db = get_gamerecords_db()

    # Get NPC to verify it exists
    npc = await db.entities.find_one({"id": npc_id, "kind": EntityKind.NPC.value})
    if not npc:
        raise HTTPException(status_code=404, detail="NPC not found")

    # Remove NPC from any scenes
    await db.scenes.update_many(
        {"npcs_present": npc_id},
        {"$pull": {"npcs_present": npc_id}}
    )

    # Delete NPC
    await db.entities.delete_one({"id": npc_id})

    return {"message": "NPC deleted successfully"}


@router.post("/scenes/{scene_id}/npcs/{npc_id}")
async def add_npc_to_scene(scene_id: str, npc_id: str):
    """Add an NPC to a scene."""
    db = get_gamerecords_db()

    # Verify NPC exists
    npc = await db.entities.find_one({"id": npc_id, "kind": EntityKind.NPC.value})
    if not npc:
        raise HTTPException(status_code=404, detail="NPC not found")

    # Verify scene exists
    scene = await db.scenes.find_one({"id": scene_id})
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    # Add NPC to scene (if not already there)
    result = await db.scenes.update_one(
        {"id": scene_id},
        {"$addToSet": {"npcs_present": npc_id}}
    )

    return {"message": "NPC added to scene", "npc_id": npc_id, "scene_id": scene_id}


@router.delete("/scenes/{scene_id}/npcs/{npc_id}")
async def remove_npc_from_scene(scene_id: str, npc_id: str):
    """Remove an NPC from a scene."""
    db = get_gamerecords_db()

    # Remove NPC from scene
    result = await db.scenes.update_one(
        {"id": scene_id},
        {"$pull": {"npcs_present": npc_id}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Scene not found or NPC not in scene")

    return {"message": "NPC removed from scene", "npc_id": npc_id, "scene_id": scene_id}
