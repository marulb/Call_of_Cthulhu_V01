"""
API routes for Realm entities.
Realms are stored in the gamerecords database.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from .models import Realm, RealmCreate, Change, Meta, EntityKind, Player
from .database import get_gamerecords_db
from datetime import datetime
import uuid

router = APIRouter(prefix="/realms", tags=["realms"])


@router.get("", response_model=List[Realm])
async def list_realms(world_id: Optional[str] = Query(None)):
    """List realms, optionally filtered by world_id."""
    db = get_gamerecords_db()

    query = {}
    if world_id:
        query["world_id"] = world_id

    realms = await db.realms.find(query).to_list(length=100)
    return realms


@router.get("/{realm_id}", response_model=Realm)
async def get_realm(realm_id: str):
    """Get a specific realm by ID."""
    db = get_gamerecords_db()
    realm = await db.realms.find_one({"id": realm_id})
    if not realm:
        raise HTTPException(status_code=404, detail="Realm not found")
    return realm


@router.post("", response_model=Realm)
async def create_realm(realm_data: RealmCreate):
    """Create a new realm."""
    db = get_gamerecords_db()

    # Generate unique ID
    realm_id = f"realm-{uuid.uuid4().hex[:8]}"

    # Create player entry for creator
    creator_player = Player(
        id=f"player-{uuid.uuid4().hex[:8]}",
        name=realm_data.created_by
    )

    # Create realm document
    realm = Realm(
        id=realm_id,
        kind=EntityKind.REALM,
        world_id=realm_data.world_id,
        name=realm_data.name,
        description=realm_data.description,
        players=[creator_player],
        meta=Meta(created_by=realm_data.created_by),
        changes=[Change(by=realm_data.created_by, type="created")]
    )

    # Insert into database
    await db.realms.insert_one(realm.dict())

    return realm


@router.put("/{realm_id}", response_model=Realm)
async def update_realm(realm_id: str, realm_data: RealmCreate):
    """Update an existing realm."""
    db = get_gamerecords_db()

    # Find existing realm
    existing = await db.realms.find_one({"id": realm_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Realm not found")

    # Update fields
    existing["name"] = realm_data.name
    existing["description"] = realm_data.description

    # Add change record
    existing["changes"].append(
        Change(by=realm_data.created_by, at=datetime.utcnow(), type="updated").dict()
    )

    # Save to database
    await db.realms.replace_one({"id": realm_id}, existing)

    return Realm(**existing)


@router.delete("/{realm_id}")
async def delete_realm(realm_id: str):
    """Delete a realm."""
    db = get_gamerecords_db()

    result = await db.realms.delete_one({"id": realm_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Realm not found")

    return {"message": "Realm deleted successfully"}
