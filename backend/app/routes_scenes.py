"""
API routes for Scene entities.
Scenes are AI-managed story segments within chapters.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from .models import Scene, SceneCreate, Change, Meta
from .database import get_gamerecords_db
from datetime import datetime
import uuid

router = APIRouter(prefix="/scenes", tags=["scenes"])


@router.get("", response_model=List[Scene])
async def list_scenes(chapter_id: Optional[str] = Query(None)):
    """List all scenes, optionally filtered by chapter."""
    db = get_gamerecords_db()

    query = {}
    if chapter_id:
        query["chapter_id"] = chapter_id

    scenes = await db.scenes.find(query).sort("meta.created_at", 1).to_list(length=100)
    return scenes


@router.get("/{scene_id}", response_model=Scene)
async def get_scene(scene_id: str):
    """Get a specific scene by ID."""
    db = get_gamerecords_db()
    scene = await db.scenes.find_one({"id": scene_id})
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    return scene


@router.post("", response_model=Scene)
async def create_scene(scene_data: SceneCreate):
    """Create a new scene (typically called by Keeper AI)."""
    db = get_gamerecords_db()

    scene_id = f"scene-{uuid.uuid4().hex[:8]}"

    scene = Scene(
        id=scene_id,
        chapter_id=scene_data.chapter_id,
        name=scene_data.name,
        description=scene_data.description,
        meta=Meta(created_by=scene_data.created_by),
        changes=[Change(by=scene_data.created_by, type="created")]
    )

    await db.scenes.insert_one(scene.dict())

    # Add scene ID to chapter's scenes array
    await db.chapters.update_one(
        {"id": scene_data.chapter_id},
        {"$push": {"scenes": scene_id}}
    )

    return scene


@router.put("/{scene_id}", response_model=Scene)
async def update_scene(scene_id: str, scene_data: SceneCreate):
    """Update an existing scene."""
    db = get_gamerecords_db()

    existing = await db.scenes.find_one({"id": scene_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Scene not found")

    # Update fields
    existing["name"] = scene_data.name
    if scene_data.description:
        existing["description"] = scene_data.description

    # Add change record
    existing["changes"].append({
        "by": scene_data.created_by,
        "at": datetime.utcnow(),
        "type": "updated"
    })

    await db.scenes.replace_one({"id": scene_id}, existing)

    return Scene(**existing)


@router.patch("/{scene_id}/status")
async def update_scene_status(scene_id: str, status: str, updated_by: str = "KeeperAI"):
    """Update scene status (active/completed)."""
    db = get_gamerecords_db()

    result = await db.scenes.update_one(
        {"id": scene_id},
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
        raise HTTPException(status_code=404, detail="Scene not found")

    return {"message": f"Scene status updated to {status}"}


@router.delete("/{scene_id}")
async def delete_scene(scene_id: str):
    """Delete a scene."""
    db = get_gamerecords_db()

    # Get scene to find chapter_id
    scene = await db.scenes.find_one({"id": scene_id})
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    # Remove scene ID from chapter's scenes array
    await db.chapters.update_one(
        {"id": scene["chapter_id"]},
        {"$pull": {"scenes": scene_id}}
    )

    # Delete scene
    await db.scenes.delete_one({"id": scene_id})

    return {"message": "Scene deleted successfully"}
