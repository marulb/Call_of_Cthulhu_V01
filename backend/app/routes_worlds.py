"""
API routes for World entities.
Worlds are stored in the system database.
"""
from fastapi import APIRouter, HTTPException
from typing import List
from .models import World, WorldCreate, Change, Meta, EntityKind
from .database import get_system_db
from datetime import datetime
import uuid

router = APIRouter(prefix="/worlds", tags=["worlds"])


@router.get("", response_model=List[World])
async def list_worlds():
    """List all worlds."""
    db = get_system_db()
    worlds = await db.worlds.find().to_list(length=100)
    return worlds


@router.get("/{world_id}", response_model=World)
async def get_world(world_id: str):
    """Get a specific world by ID."""
    db = get_system_db()
    world = await db.worlds.find_one({"id": world_id})
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    return world


@router.post("", response_model=World)
async def create_world(world_data: WorldCreate):
    """Create a new world."""
    db = get_system_db()

    # Generate unique ID
    world_id = f"world-{uuid.uuid4().hex[:8]}"

    # Create world document
    world = World(
        id=world_id,
        kind=EntityKind.WORLD,
        name=world_data.name,
        ruleset=world_data.ruleset,
        description=world_data.description,
        meta=Meta(created_by=world_data.created_by),
        changes=[Change(by=world_data.created_by, type="created")]
    )

    # Insert into database
    await db.worlds.insert_one(world.dict())

    return world


@router.put("/{world_id}", response_model=World)
async def update_world(world_id: str, world_data: WorldCreate):
    """Update an existing world."""
    db = get_system_db()

    # Find existing world
    existing = await db.worlds.find_one({"id": world_id})
    if not existing:
        raise HTTPException(status_code=404, detail="World not found")

    # Update fields
    existing["name"] = world_data.name
    existing["ruleset"] = world_data.ruleset
    existing["description"] = world_data.description

    # Add change record
    existing["changes"].append(
        Change(by=world_data.created_by, at=datetime.utcnow(), type="updated").dict()
    )

    # Save to database
    await db.worlds.replace_one({"id": world_id}, existing)

    return World(**existing)


@router.delete("/{world_id}")
async def delete_world(world_id: str):
    """Delete a world."""
    db = get_system_db()

    result = await db.worlds.delete_one({"id": world_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="World not found")

    return {"message": "World deleted successfully"}
