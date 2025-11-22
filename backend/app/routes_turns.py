"""
API routes for Turn entities.
Turns represent player actions + Keeper responses.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from .models import Turn, TurnCreate, Change, Meta, Reaction
from .database import get_gamerecords_db
from datetime import datetime
import uuid

router = APIRouter(prefix="/turns", tags=["turns"])


@router.get("", response_model=List[Turn])
async def list_turns(scene_id: Optional[str] = Query(None)):
    """List all turns, optionally filtered by scene."""
    db = get_gamerecords_db()

    query = {}
    if scene_id:
        query["scene_id"] = scene_id

    turns = await db.turns.find(query).sort("order", 1).to_list(length=1000)
    return turns


@router.get("/{turn_id}", response_model=Turn)
async def get_turn(turn_id: str):
    """Get a specific turn by ID."""
    db = get_gamerecords_db()
    turn = await db.turns.find_one({"id": turn_id})
    if not turn:
        raise HTTPException(status_code=404, detail="Turn not found")
    return turn


@router.post("", response_model=Turn)
async def create_turn(turn_data: TurnCreate):
    """Create a new turn."""
    db = get_gamerecords_db()

    turn_id = f"turn-{uuid.uuid4().hex[:8]}"

    turn = Turn(
        id=turn_id,
        scene_id=turn_data.scene_id,
        order=turn_data.order,
        actions=turn_data.actions,
        status="draft",
        meta=Meta(created_by=turn_data.created_by),
        changes=[Change(by=turn_data.created_by, type="created")]
    )

    await db.turns.insert_one(turn.dict())

    # Add turn ID to scene's turns array
    await db.scenes.update_one(
        {"id": turn_data.scene_id},
        {"$push": {"turns": turn_id}}
    )

    return turn


@router.post("/{turn_id}/submit")
async def submit_turn(turn_id: str, submitted_by: str):
    """Submit turn for AI processing."""
    db = get_gamerecords_db()

    result = await db.turns.update_one(
        {"id": turn_id},
        {
            "$set": {"status": "ready_for_agents"},
            "$push": {
                "changes": {
                    "by": submitted_by,
                    "at": datetime.utcnow(),
                    "type": "submitted"
                }
            }
        }
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Turn not found")

    # TODO: Trigger Keeper AI processing here
    # For now, return success
    return {"message": "Turn submitted for processing", "turn_id": turn_id}


@router.patch("/{turn_id}/reaction")
async def add_reaction(turn_id: str, description: str, summary: Optional[str] = None):
    """Add Keeper's reaction to turn (called by AI)."""
    db = get_gamerecords_db()

    reaction = Reaction(description=description, summary=summary)

    result = await db.turns.update_one(
        {"id": turn_id},
        {
            "$set": {
                "reaction": reaction.dict(),
                "status": "completed"
            },
            "$push": {
                "changes": {
                    "by": "KeeperAI",
                    "at": datetime.utcnow(),
                    "type": "reaction_added"
                }
            }
        }
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Turn not found")

    return {"message": "Reaction added successfully"}


@router.put("/{turn_id}", response_model=Turn)
async def update_turn(turn_id: str, turn_data: TurnCreate):
    """Update an existing turn (draft status only)."""
    db = get_gamerecords_db()

    existing = await db.turns.find_one({"id": turn_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Turn not found")

    if existing.get("status") != "draft":
        raise HTTPException(status_code=400, detail="Can only update draft turns")

    # Update fields
    existing["actions"] = [action.dict() if hasattr(action, 'dict') else action for action in turn_data.actions]

    # Add change record
    existing["changes"].append({
        "by": turn_data.created_by,
        "at": datetime.utcnow(),
        "type": "updated"
    })

    await db.turns.replace_one({"id": turn_id}, existing)

    return Turn(**existing)


@router.delete("/{turn_id}")
async def delete_turn(turn_id: str):
    """Delete a turn (draft status only)."""
    db = get_gamerecords_db()

    # Get turn to check status and find scene_id
    turn = await db.turns.find_one({"id": turn_id})
    if not turn:
        raise HTTPException(status_code=404, detail="Turn not found")

    if turn.get("status") != "draft":
        raise HTTPException(status_code=400, detail="Can only delete draft turns")

    # Remove turn ID from scene's turns array
    await db.scenes.update_one(
        {"id": turn["scene_id"]},
        {"$pull": {"turns": turn_id}}
    )

    # Delete turn
    await db.turns.delete_one({"id": turn_id})

    return {"message": "Turn deleted successfully"}
