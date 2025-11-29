"""
API routes for Player entities.
Players are stored in the gamerecords database.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from .models import Change
from .database import get_gamerecords_db
from datetime import datetime
import uuid
from pydantic import BaseModel

router = APIRouter(prefix="/players", tags=["players"])


class Player(BaseModel):
    """Player model for database."""
    id: str
    name: str
    email: Optional[str] = None
    created_at: datetime
    last_login: datetime
    realms: List[str] = []  # Realm IDs the player is part of


class PlayerCreate(BaseModel):
    """Request model for creating/registering a player."""
    name: str
    email: Optional[str] = None


class PlayerResponse(BaseModel):
    """Response model for player data."""
    id: str
    name: str
    email: Optional[str] = None
    created_at: datetime
    last_login: datetime
    realms: List[str] = []


@router.get("", response_model=List[PlayerResponse])
async def list_players(search: Optional[str] = Query(None)):
    """List all players, optionally filtered by name search."""
    db = get_gamerecords_db()

    query = {}
    if search:
        query["name"] = {"$regex": search, "$options": "i"}  # Case-insensitive search

    players = await db.players.find(query).sort("name", 1).to_list(length=100)
    return players


@router.get("/{player_id}", response_model=PlayerResponse)
async def get_player(player_id: str):
    """Get a specific player by ID."""
    db = get_gamerecords_db()
    player = await db.players.find_one({"id": player_id})
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player


@router.get("/by-name/{player_name}", response_model=PlayerResponse)
async def get_player_by_name(player_name: str):
    """Get a player by name (case-insensitive)."""
    db = get_gamerecords_db()
    player = await db.players.find_one({
        "name": {"$regex": f"^{player_name}$", "$options": "i"}
    })
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player


@router.post("", response_model=PlayerResponse)
async def create_or_get_player(player_data: PlayerCreate):
    """Create a new player or return existing one if name already exists (case-insensitive)."""
    db = get_gamerecords_db()

    # Check if player already exists (case-insensitive)
    existing = await db.players.find_one({
        "name": {"$regex": f"^{player_data.name}$", "$options": "i"}
    })
    if existing:
        # Update last login
        existing["last_login"] = datetime.utcnow()
        await db.players.replace_one({"id": existing["id"]}, existing)
        return PlayerResponse(**existing)

    # Create new player
    player_id = f"player-{uuid.uuid4().hex[:8]}"
    now = datetime.utcnow()

    player = Player(
        id=player_id,
        name=player_data.name,
        email=player_data.email,
        created_at=now,
        last_login=now,
        realms=[]
    )

    await db.players.insert_one(player.dict())

    return PlayerResponse(**player.dict())


@router.put("/{player_id}", response_model=PlayerResponse)
async def update_player(player_id: str, player_data: PlayerCreate):
    """Update an existing player."""
    db = get_gamerecords_db()

    existing = await db.players.find_one({"id": player_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Player not found")

    # Update fields
    existing["name"] = player_data.name
    if player_data.email:
        existing["email"] = player_data.email
    existing["last_login"] = datetime.utcnow()

    await db.players.replace_one({"id": player_id}, existing)

    return PlayerResponse(**existing)


@router.delete("/{player_id}")
async def delete_player(player_id: str):
    """Delete a player."""
    db = get_gamerecords_db()

    result = await db.players.delete_one({"id": player_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Player not found")

    return {"message": "Player deleted successfully"}
