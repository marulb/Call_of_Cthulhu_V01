"""
API routes for Character entities (PCs).
Characters are stored in the gamerecords database in the entities collection.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from .models import Character, CharacterCreate, Change, Meta, EntityKind, Controller
from .database import get_gamerecords_db
from datetime import datetime
import uuid

router = APIRouter(prefix="/characters", tags=["characters"])


@router.get("", response_model=List[Character])
async def list_characters(
    realm_id: Optional[str] = Query(None),
    player: Optional[str] = Query(None)
):
    """List characters, optionally filtered by realm_id and/or player name."""
    db = get_gamerecords_db()

    query = {"kind": EntityKind.PC.value}
    if realm_id:
        query["realm_id"] = realm_id
    if player:
        query["controller.owner"] = player

    characters = await db.entities.find(query).to_list(length=100)
    return characters


@router.get("/{character_id}", response_model=Character)
async def get_character(character_id: str):
    """Get a specific character by ID."""
    db = get_gamerecords_db()
    character = await db.entities.find_one({"id": character_id, "kind": EntityKind.PC.value})
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character


@router.post("", response_model=Character)
async def create_character(character_data: CharacterCreate):
    """Create a new character."""
    db = get_gamerecords_db()

    # Generate unique IDs
    character_id = f"char-{uuid.uuid4().hex[:8]}"
    character_uid = f"uid-{uuid.uuid4().hex}"

    # Create character document
    character = Character(
        id=character_id,
        uid=character_uid,
        kind=EntityKind.PC,
        type=character_data.type,
        name=character_data.name,
        realm_id=character_data.realm_id,
        description=character_data.description,
        controller=Controller(
            owner=character_data.owner,
            mode="player",
            agent="human"
        ),
        data=character_data.data if character_data.data else None,
        ooc_notes=character_data.ooc_notes or "",
        profile_completed=character_data.profile_completed or False,
        meta=Meta(created_by=character_data.created_by),
        changes=[Change(by=character_data.created_by, type="created")]
    )

    # Insert into database
    await db.entities.insert_one(character.dict())

    # Update realm's characters list
    await db.realms.update_one(
        {"id": character_data.realm_id},
        {"$addToSet": {"characters": character_id}}
    )

    return character


@router.put("/{character_id}", response_model=Character)
async def update_character(character_id: str, character_data: CharacterCreate):
    """Update an existing character."""
    db = get_gamerecords_db()

    # Find existing character
    existing = await db.entities.find_one({"id": character_id, "kind": EntityKind.PC.value})
    if not existing:
        raise HTTPException(status_code=404, detail="Character not found")

    # Update fields
    existing["name"] = character_data.name
    existing["type"] = character_data.type
    existing["description"] = character_data.description

    # Update character sheet data if provided
    if character_data.data is not None:
        existing["data"] = character_data.data.dict()

    # Update ooc_notes if provided
    if character_data.ooc_notes is not None:
        existing["ooc_notes"] = character_data.ooc_notes

    # Update profile_completed if provided
    if character_data.profile_completed is not None:
        existing["profile_completed"] = character_data.profile_completed

    # Add change record
    existing["changes"].append(
        Change(by=character_data.created_by, at=datetime.utcnow(), type="updated").dict()
    )

    # Save to database
    await db.entities.replace_one({"id": character_id}, existing)

    return Character(**existing)


@router.delete("/{character_id}")
async def delete_character(character_id: str):
    """Delete a character."""
    db = get_gamerecords_db()

    # Get character to find realm_id
    character = await db.entities.find_one({"id": character_id, "kind": EntityKind.PC.value})
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    # Remove from realm's characters list
    await db.realms.update_one(
        {"id": character["realm_id"]},
        {"$pull": {"characters": character_id}}
    )

    # Delete character
    result = await db.entities.delete_one({"id": character_id})

    return {"message": "Character deleted successfully"}
