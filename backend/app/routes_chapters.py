"""
API routes for Chapter entities.
Chapters are AI-managed narrative arcs within campaigns.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from .models import Chapter, ChapterCreate, Change, Meta
from .database import get_gamerecords_db
from datetime import datetime
import uuid

router = APIRouter(prefix="/chapters", tags=["chapters"])


@router.get("", response_model=List[Chapter])
async def list_chapters(campaign_id: Optional[str] = Query(None)):
    """List all chapters, optionally filtered by campaign."""
    db = get_gamerecords_db()

    query = {}
    if campaign_id:
        query["campaign_id"] = campaign_id

    chapters = await db.chapters.find(query).sort("meta.created_at", 1).to_list(length=100)
    return chapters


@router.get("/{chapter_id}", response_model=Chapter)
async def get_chapter(chapter_id: str):
    """Get a specific chapter by ID."""
    db = get_gamerecords_db()
    chapter = await db.chapters.find_one({"id": chapter_id})
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return chapter


@router.post("", response_model=Chapter)
async def create_chapter(chapter_data: ChapterCreate):
    """Create a new chapter (typically called by Keeper AI)."""
    db = get_gamerecords_db()

    chapter_id = f"chapter-{uuid.uuid4().hex[:8]}"

    chapter = Chapter(
        id=chapter_id,
        campaign_id=chapter_data.campaign_id,
        name=chapter_data.name,
        description=chapter_data.description,
        meta=Meta(created_by=chapter_data.created_by),
        changes=[Change(by=chapter_data.created_by, type="created")]
    )

    await db.chapters.insert_one(chapter.dict())

    # Add chapter ID to campaign's chapters array
    await db.campaigns.update_one(
        {"id": chapter_data.campaign_id},
        {"$push": {"chapters": chapter_id}}
    )

    return chapter


@router.put("/{chapter_id}", response_model=Chapter)
async def update_chapter(chapter_id: str, chapter_data: ChapterCreate):
    """Update an existing chapter."""
    db = get_gamerecords_db()

    existing = await db.chapters.find_one({"id": chapter_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # Update fields
    existing["name"] = chapter_data.name
    if chapter_data.description:
        existing["description"] = chapter_data.description

    # Add change record
    existing["changes"].append({
        "by": chapter_data.created_by,
        "at": datetime.utcnow(),
        "type": "updated"
    })

    await db.chapters.replace_one({"id": chapter_id}, existing)

    return Chapter(**existing)


@router.patch("/{chapter_id}/status")
async def update_chapter_status(chapter_id: str, status: str, updated_by: str = "KeeperAI"):
    """Update chapter status (active/completed)."""
    db = get_gamerecords_db()

    result = await db.chapters.update_one(
        {"id": chapter_id},
        {
            "$set": {"status": status},
            "$push": {
                "changes": {
                    "by": updated_by,
                    "at": datetime.utcnow(),
                    "type": f"status_changed_to_{status}"
                }
            }
        }
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Chapter not found")

    return {"message": f"Chapter status updated to {status}"}


@router.delete("/{chapter_id}")
async def delete_chapter(chapter_id: str):
    """Delete a chapter."""
    db = get_gamerecords_db()

    # Get chapter to find campaign_id
    chapter = await db.chapters.find_one({"id": chapter_id})
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # Remove chapter ID from campaign's chapters array
    await db.campaigns.update_one(
        {"id": chapter["campaign_id"]},
        {"$pull": {"chapters": chapter_id}}
    )

    # Delete chapter
    await db.chapters.delete_one({"id": chapter_id})

    return {"message": "Chapter deleted successfully"}
