"""
API routes for Turn entities.
Turns represent player actions + Keeper responses.
"""
from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional
from pydantic import BaseModel
from .models import Turn, TurnCreate, Change, Meta, Reaction
from .database import get_gamerecords_db
from .config import (
    USE_ASYNC_TURN_PROCESSING,
    N8N_DUNGEONMASTER_WEBHOOK,
    N8N_DUNGEONMASTER_V2_WEBHOOK,
    BACKEND_BASE_URL
)
from .services import (
    ContextAssemblyService,
    SkillCheckService,
    TransitionService,
    ContextBundle
)
from datetime import datetime
import uuid
import httpx
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/turns", tags=["turns"])

# Legacy webhook URL for backwards compatibility
N8N_DUNGEONMASTER_WEBHOOK_URL = N8N_DUNGEONMASTER_WEBHOOK


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


# ============== PYDANTIC MODELS FOR NEW ENDPOINTS ==============

class TurnSubmitRequest(BaseModel):
    """Request model for turn submission."""
    session_id: str


class CallbackPayload(BaseModel):
    """Callback payload from n8n."""
    turn_id: str
    success: bool
    result: Optional[dict] = None
    error: Optional[str] = None
    metadata: Optional[dict] = None


# ============== TURN SUBMISSION ENDPOINTS ==============

@router.post("/{turn_id}/submit")
async def submit_turn(
    turn_id: str,
    request: TurnSubmitRequest = Body(...),
    submitted_by: str = "player"
):
    """
    Submit turn for AI processing via DungeonMaster.

    Uses feature flag to switch between sync (old) and async (new) processing.
    """
    if USE_ASYNC_TURN_PROCESSING:
        return await submit_turn_async(turn_id, request.session_id, submitted_by)
    else:
        return await submit_turn_sync(turn_id, submitted_by)


async def submit_turn_sync(turn_id: str, submitted_by: str):
    """
    Original synchronous turn submission (legacy mode).
    Blocks until n8n completes LLM processing.
    """
    db = get_gamerecords_db()

    # Get the turn first
    turn = await db.turns.find_one({"id": turn_id})
    if not turn:
        raise HTTPException(status_code=404, detail="Turn not found")

    # Update status to processing
    await db.turns.update_one(
        {"id": turn_id},
        {
            "$set": {"status": "processing"},
            "$push": {
                "changes": {
                    "by": submitted_by,
                    "at": datetime.utcnow(),
                    "type": "submitted"
                }
            }
        }
    )

    # Call DungeonMaster AI via n8n webhook
    try:
        payload = {"DungeonMaster": turn["actions"]}

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                N8N_DUNGEONMASTER_WEBHOOK_URL,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                n8n_data = response.json()
                
                # Extract description from n8n response
                description = n8n_data.get("output", n8n_data.get("body", ""))
                
                if not description and isinstance(n8n_data, dict):
                    description = (
                        n8n_data.get("text") or 
                        n8n_data.get("response") or 
                        n8n_data.get("description") or
                        "The Keeper observes in silence..."
                    )
                
                # Try to extract a summary
                summary = None
                if description:
                    sentences = description.split('. ')
                    if len(sentences) > 1:
                        summary = sentences[0] + '.'
                    elif len(description) > 100:
                        summary = description[:97] + '...'
                
                # Add reaction to turn
                reaction = Reaction(description=description, summary=summary)
                
                await db.turns.update_one(
                    {"id": turn_id},
                    {
                        "$set": {
                            "reaction": reaction.dict(),
                            "status": "completed"
                        },
                        "$push": {
                            "changes": {
                                "by": "DungeonMasterAI",
                                "at": datetime.utcnow(),
                                "type": "reaction_added"
                            }
                        }
                    }
                )
                
                return {
                    "message": "Turn processed successfully",
                    "turn_id": turn_id,
                    "reaction": reaction.dict()
                }
            else:
                # If n8n fails, mark as failed
                await db.turns.update_one(
                    {"id": turn_id},
                    {"$set": {"status": "failed"}}
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"DungeonMaster AI returned status {response.status_code}"
                )
                
    except httpx.TimeoutException:
        await db.turns.update_one(
            {"id": turn_id},
            {"$set": {"status": "failed"}}
        )
        raise HTTPException(
            status_code=504,
            detail="Request to DungeonMaster AI timed out"
        )
    except httpx.RequestError as e:
        await db.turns.update_one(
            {"id": turn_id},
            {"$set": {"status": "failed"}}
        )
        raise HTTPException(
            status_code=503,
            detail=f"Could not connect to DungeonMaster AI: {str(e)}"
        )
    except Exception as e:
        await db.turns.update_one(
            {"id": turn_id},
            {"$set": {"status": "failed"}}
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error processing turn: {str(e)}"
        )


async def submit_turn_async(turn_id: str, session_id: str, submitted_by: str = "player"):
    """
    New async turn submission with callback pattern.

    Steps:
    1. Validate turn and update status
    2. Assemble context bundle
    3. Detect and roll skill checks
    4. Call n8n webhook (fire-and-forget)
    5. Return immediately with 202 Accepted
    """
    db = get_gamerecords_db()

    # Get turn
    turn = await db.turns.find_one({"id": turn_id})
    if not turn:
        raise HTTPException(status_code=404, detail="Turn not found")

    # Get scene to find session_id
    scene_id = turn.get("scene_id")
    scene = await db.scenes.find_one({"id": scene_id})
    if not scene:
        raise HTTPException(status_code=400, detail="Turn's scene not found")

    # Update status to processing
    await db.turns.update_one(
        {"id": turn_id},
        {
            "$set": {"status": "processing"},
            "$push": {
                "changes": {
                    "by": submitted_by,
                    "at": datetime.utcnow(),
                    "type": "submitted"
                }
            }
        }
    )

    # Emit Socket.IO event
    from .socketio_manager import emit_turn_processing
    await emit_turn_processing(session_id, turn_id)

    # Assemble context bundle
    try:
        context_service = ContextAssemblyService()
        skill_service = SkillCheckService()

        # Detect and roll skill checks
        characters_data = await _fetch_turn_characters(turn)
        skill_checks = skill_service.detect_skill_checks(
            turn.get("actions", []),
            characters_data
        )
        skill_results = await skill_service.roll_skill_checks(
            skill_checks,
            characters_data
        )

        # Build callback URL - must match the actual endpoint path
        callback_url = f"{BACKEND_BASE_URL}/api/v1/turns/internal/{turn_id}/complete"

        # Assemble full context
        context_bundle = await context_service.assemble_context(
            turn_id=turn_id,
            callback_url=callback_url,
            skill_checks=skill_results
        )

        # Call n8n webhook (fire-and-forget)
        await _call_n8n_async(context_bundle)

        logger.info(f"Turn {turn_id} submitted for async processing")

    except Exception as e:
        logger.error(f"Error assembling context for turn {turn_id}: {e}")
        # Mark turn as failed
        await db.turns.update_one(
            {"id": turn_id},
            {"$set": {"status": "failed", "error": str(e)}}
        )
        raise HTTPException(status_code=500, detail=f"Failed to process turn: {str(e)}")

    # Return immediately with 202 Accepted
    return {
        "turn_id": turn_id,
        "status": "processing",
        "message": "Turn submitted for processing"
    }


async def _fetch_turn_characters(turn: dict):
    """Fetch characters for a turn."""
    from .services.context_assembly import CharacterContext, CharacterSkill, CharacterStats

    db = get_gamerecords_db()

    # Get scene to find participants
    scene_id = turn.get("scene_id")
    scene = await db.scenes.find_one({"id": scene_id})
    if not scene:
        return []

    character_ids = scene.get("participants", [])
    if not character_ids:
        return []

    # Fetch characters
    cursor = db.characters.find({"id": {"$in": character_ids}})
    char_docs = await cursor.to_list(length=10)

    # Convert to CharacterContext objects
    characters = []
    for char in char_docs:
        char_data = char.get("data", {})
        skills = []

        # Extract skills
        for skill_name, skill_data in char_data.get("skills", {}).items():
            if isinstance(skill_data, dict):
                value_str = skill_data.get("reg", "0")
                try:
                    value = int(value_str) if value_str else 0
                except (ValueError, TypeError):
                    value = 0

                if value > 0:
                    skills.append(CharacterSkill(name=skill_name, value=value))

        investigator = char_data.get("investigator", {})
        characters.append(CharacterContext(
            id=char.get("id", ""),
            name=char.get("name", "Unknown"),
            occupation=investigator.get("occupation") if isinstance(investigator, dict) else None,
            age=investigator.get("age") if isinstance(investigator, dict) else None,
            skills=skills,
            stats=None,
            conditions=[]
        ))

    return characters


async def _call_n8n_async(context_bundle: ContextBundle):
    """Fire-and-forget call to n8n webhook."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Use model_dump with mode='json' to serialize datetime objects
            await client.post(
                N8N_DUNGEONMASTER_V2_WEBHOOK,
                json=context_bundle.model_dump(mode='json'),
                headers={"Content-Type": "application/json"}
            )
    except Exception as e:
        logger.error(f"Failed to call n8n webhook: {e}")
        # Don't raise - n8n will retry via callback


# ============== CALLBACK ENDPOINT ==============

@router.post("/internal/{turn_id}/complete")
async def complete_turn_callback(turn_id: str, payload: CallbackPayload):
    """
    Callback endpoint for n8n to deliver LLM results.

    Called by n8n after narrative generation completes.
    """
    db = get_gamerecords_db()

    logger.info(f"Received callback for turn {turn_id}, success={payload.success}")

    # Get turn
    turn = await db.turns.find_one({"id": turn_id})
    if not turn:
        raise HTTPException(status_code=404, detail="Turn not found")

    # Validate turn is in processing state
    if turn.get("status") != "processing":
        logger.warning(f"Turn {turn_id} not in processing state (status={turn.get('status')})")
        # Allow anyway, but log warning

    # Get scene to find session_id
    scene_id = turn.get("scene_id")
    scene = await db.scenes.find_one({"id": scene_id})
    session_id = None

    # Find session_id from scene/chapter/campaign
    if scene:
        chapter_id = scene.get("chapter_id")
        if chapter_id:
            chapter = await db.chapters.find_one({"id": chapter_id})
            if chapter:
                campaign_id = chapter.get("campaign_id")
                # Get session from campaign (simplified - in production, get active session)
                sessions = await db.sessions.find({"campaign_id": campaign_id}).to_list(length=1)
                if sessions:
                    session_id = sessions[0].get("id")

    if not payload.success:
        # Mark turn as failed
        await db.turns.update_one(
            {"id": turn_id},
            {
                "$set": {
                    "status": "failed",
                    "error": payload.error or "Unknown error from n8n"
                }
            }
        )

        if session_id:
            from .socketio_manager import emit_turn_failed
            await emit_turn_failed(session_id, turn_id, payload.error or "Processing failed")

        return {"status": "failed", "turn_id": turn_id}

    # Extract result
    result = payload.result or {}
    narrative = result.get("narrative", "")
    summary = result.get("summary")
    transition_data = result.get("transition")

    # Write reaction to turn
    reaction = Reaction(description=narrative, summary=summary)

    await db.turns.update_one(
        {"id": turn_id},
        {
            "$set": {
                "reaction": reaction.dict(),
                "status": "completed"
            },
            "$push": {
                "changes": {
                    "by": "DungeonMasterAI",
                    "at": datetime.utcnow(),
                    "type": "reaction_added"
                }
            }
        }
    )

    # Process transition if present
    new_scene_id = scene_id
    new_chapter_id = scene.get("chapter_id") if scene else None

    if transition_data and transition_data.get("type") != "none":
        try:
            transition_service = TransitionService()
            transition_info = transition_service.parse_transition_from_llm({"transition": transition_data})

            if scene and scene.get("chapter_id"):
                chapter = await db.chapters.find_one({"id": scene["chapter_id"]})
                campaign_id = chapter.get("campaign_id") if chapter else None

                transition_result = await transition_service.process_transition(
                    transition_info=transition_info,
                    turn_id=turn_id,
                    current_scene_id=scene_id,
                    current_chapter_id=scene["chapter_id"],
                    campaign_id=campaign_id,
                    created_by="DungeonMasterAI"
                )

                if transition_result.transition_occurred:
                    new_scene_id = transition_result.new_scene_id or scene_id
                    new_chapter_id = transition_result.new_chapter_id or scene.get("chapter_id")

                    # Emit transition events
                    if session_id:
                        if transition_result.transition_type == "scene":
                            from .socketio_manager import emit_scene_created
                            await emit_scene_created(session_id, {
                                "scene_id": new_scene_id,
                                "name": transition_result.scene_name,
                                "chapter_id": new_chapter_id
                            })
                        elif transition_result.transition_type == "chapter":
                            from .socketio_manager import emit_chapter_created
                            await emit_chapter_created(session_id, {
                                "chapter_id": new_chapter_id,
                                "name": transition_result.chapter_name
                            }, {
                                "scene_id": new_scene_id,
                                "name": transition_result.scene_name
                            })

        except Exception as e:
            logger.error(f"Error processing transition for turn {turn_id}: {e}")
            # Continue anyway - narrative was saved

    # Emit completion event
    if session_id:
        from .socketio_manager import emit_turn_completed
        await emit_turn_completed(session_id, turn_id, reaction.dict(), new_scene_id)

    logger.info(f"Turn {turn_id} completed successfully")

    return {
        "status": "completed",
        "turn_id": turn_id,
        "scene_id": new_scene_id,
        "chapter_id": new_chapter_id
    }


# ============== STATUS ENDPOINT ==============

@router.get("/{turn_id}/status")
async def get_turn_status(turn_id: str):
    """Get current processing status of a turn (for polling)."""
    db = get_gamerecords_db()

    turn = await db.turns.find_one({"id": turn_id})
    if not turn:
        raise HTTPException(status_code=404, detail="Turn not found")

    return {
        "turn_id": turn_id,
        "status": turn.get("status", "unknown"),
        "has_reaction": turn.get("reaction") is not None,
        "error": turn.get("error")
    }


# ============== LEGACY ENDPOINTS ==============

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
