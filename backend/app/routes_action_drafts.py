"""
API routes for ActionDraft entities.
ActionDrafts are temporary UI state for current turn (cleared after submission).
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from .models import ActionDraft, ActionDraftCreate
from .database import get_gamerecords_db
from datetime import datetime
import uuid

router = APIRouter(prefix="/action-drafts", tags=["action-drafts"])


@router.get("", response_model=List[ActionDraft])
async def list_action_drafts(
    session_id: Optional[str] = Query(None),
    player_id: Optional[str] = Query(None)
):
    """List action drafts, optionally filtered by session or player."""
    db = get_gamerecords_db()

    query = {}
    if session_id:
        query["session_id"] = session_id
    if player_id:
        query["player_id"] = player_id

    drafts = await db.action_drafts.find(query).sort("order", 1).to_list(length=1000)
    return drafts


@router.get("/{draft_id}", response_model=ActionDraft)
async def get_action_draft(draft_id: str):
    """Get a specific action draft by ID."""
    db = get_gamerecords_db()
    draft = await db.action_drafts.find_one({"id": draft_id})
    if not draft:
        raise HTTPException(status_code=404, detail="Action draft not found")
    return draft


@router.post("", response_model=ActionDraft)
async def create_action_draft(draft_data: ActionDraftCreate):
    """Create a new action draft."""
    db = get_gamerecords_db()

    draft_id = f"draft-{uuid.uuid4().hex[:8]}"

    draft = ActionDraft(
        id=draft_id,
        session_id=draft_data.session_id,
        player_id=draft_data.player_id,
        character_id=draft_data.character_id,
        speak=draft_data.speak,
        act=draft_data.act,
        appearance=draft_data.appearance,
        emotion=draft_data.emotion,
        ooc=draft_data.ooc,
        order=draft_data.order,
        ready=draft_data.ready
    )

    await db.action_drafts.insert_one(draft.dict())

    return draft


@router.put("/{draft_id}", response_model=ActionDraft)
async def update_action_draft(draft_id: str, draft_data: ActionDraftCreate):
    """Update an existing action draft."""
    db = get_gamerecords_db()

    existing = await db.action_drafts.find_one({"id": draft_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Action draft not found")

    # Update all fields
    existing["speak"] = draft_data.speak
    existing["act"] = draft_data.act
    existing["appearance"] = draft_data.appearance
    existing["emotion"] = draft_data.emotion
    existing["ooc"] = draft_data.ooc
    existing["order"] = draft_data.order
    existing["ready"] = draft_data.ready
    existing["updated_at"] = datetime.utcnow()

    await db.action_drafts.replace_one({"id": draft_id}, existing)

    return ActionDraft(**existing)


@router.patch("/{draft_id}/ready")
async def toggle_ready(draft_id: str, ready: bool):
    """Toggle ready state for action draft."""
    db = get_gamerecords_db()

    result = await db.action_drafts.update_one(
        {"id": draft_id},
        {
            "$set": {
                "ready": ready,
                "updated_at": datetime.utcnow()
            }
        }
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Action draft not found")

    return {"message": f"Ready state updated to {ready}"}


@router.patch("/{draft_id}/order")
async def update_order(draft_id: str, order: int):
    """Update order/position of action draft."""
    db = get_gamerecords_db()

    result = await db.action_drafts.update_one(
        {"id": draft_id},
        {
            "$set": {
                "order": order,
                "updated_at": datetime.utcnow()
            }
        }
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Action draft not found")

    return {"message": "Order updated successfully"}


@router.delete("/{draft_id}")
async def delete_action_draft(draft_id: str):
    """Delete an action draft."""
    db = get_gamerecords_db()

    result = await db.action_drafts.delete_one({"id": draft_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Action draft not found")

    return {"message": "Action draft deleted successfully"}


@router.delete("/session/{session_id}/clear")
async def clear_session_drafts(session_id: str):
    """Clear all action drafts for a session (after turn submission)."""
    db = get_gamerecords_db()

    result = await db.action_drafts.delete_many({"session_id": session_id})

    return {
        "message": f"Cleared {result.deleted_count} action drafts",
        "count": result.deleted_count
    }
