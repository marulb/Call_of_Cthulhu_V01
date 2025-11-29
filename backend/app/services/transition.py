"""
Scene/chapter transition service.

Processes LLM-detected transitions and creates new scenes/chapters.
Implements automated scene/chapter creation logic from REFACTORING_PLAN.md Section 6.
"""
import logging
import uuid
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel
from datetime import datetime

from ..database import get_gamerecords_db
from ..models import Scene, Chapter, Change, Meta

logger = logging.getLogger(__name__)


# ============== Transition Models ==============

class TransitionInfo(BaseModel):
    """Transition information from LLM response."""
    type: Literal["none", "scene", "chapter"]
    reason: Optional[str] = None
    suggested_name: Optional[str] = None


class TransitionResult(BaseModel):
    """Result of transition processing."""
    transition_occurred: bool
    transition_type: Optional[Literal["scene", "chapter"]] = None
    new_scene_id: Optional[str] = None
    new_chapter_id: Optional[str] = None
    scene_name: Optional[str] = None
    chapter_name: Optional[str] = None


# ============== Transition Service ==============

class TransitionService:
    """Service for handling scene/chapter transitions."""

    def __init__(self):
        """Initialize the transition service."""
        pass

    def parse_transition_from_llm(
        self,
        llm_response: Dict[str, Any]
    ) -> TransitionInfo:
        """
        Parse transition information from LLM structured output.

        Expected LLM response format:
        {
            "transition": {
                "type": "none" | "scene" | "chapter",
                "reason": "explanation",
                "suggested_name": "name for new scene/chapter"
            }
        }
        """
        transition_data = llm_response.get("transition", {})

        if not isinstance(transition_data, dict):
            logger.warning("LLM response missing transition data, defaulting to 'none'")
            return TransitionInfo(type="none")

        transition_type = transition_data.get("type", "none")

        # Validate type
        if transition_type not in ["none", "scene", "chapter"]:
            logger.warning(f"Invalid transition type '{transition_type}', defaulting to 'none'")
            transition_type = "none"

        return TransitionInfo(
            type=transition_type,
            reason=transition_data.get("reason"),
            suggested_name=transition_data.get("suggested_name")
        )

    async def process_transition(
        self,
        transition_info: TransitionInfo,
        turn_id: str,
        current_scene_id: str,
        current_chapter_id: str,
        campaign_id: str,
        created_by: str = "DungeonMasterAI"
    ) -> TransitionResult:
        """
        Process a transition by creating new scene/chapter if needed.

        Args:
            transition_info: Parsed transition from LLM
            turn_id: ID of the turn that triggered transition
            current_scene_id: Current scene ID
            current_chapter_id: Current chapter ID
            campaign_id: Campaign ID
            created_by: Who triggered the transition

        Returns:
            TransitionResult with new scene/chapter IDs if created
        """
        if transition_info.type == "none":
            return TransitionResult(transition_occurred=False)

        if transition_info.type == "scene":
            return await self._create_new_scene(
                current_chapter_id=current_chapter_id,
                current_scene_id=current_scene_id,
                turn_id=turn_id,
                suggested_name=transition_info.suggested_name,
                reason=transition_info.reason,
                created_by=created_by
            )

        if transition_info.type == "chapter":
            return await self._create_new_chapter(
                campaign_id=campaign_id,
                current_scene_id=current_scene_id,
                turn_id=turn_id,
                suggested_name=transition_info.suggested_name,
                reason=transition_info.reason,
                created_by=created_by
            )

        return TransitionResult(transition_occurred=False)

    async def _create_new_scene(
        self,
        current_chapter_id: str,
        current_scene_id: str,
        turn_id: str,
        suggested_name: Optional[str],
        reason: Optional[str],
        created_by: str
    ) -> TransitionResult:
        """
        Create a new scene in the current chapter.

        Steps:
        1. Close current scene (mark as completed, add summary)
        2. Create new scene
        3. Add new scene to chapter's scenes array
        """
        logger.info(
            f"Creating new scene in chapter {current_chapter_id} "
            f"(triggered by turn {turn_id})"
        )

        db = get_gamerecords_db()

        # Generate new scene ID
        scene_id = f"scene-{uuid.uuid4().hex[:8]}"

        # Get current scene for context
        current_scene = await db.scenes.find_one({"id": current_scene_id})
        if not current_scene:
            logger.error(f"Current scene {current_scene_id} not found")
            raise ValueError(f"Scene {current_scene_id} not found")

        # Close current scene
        await self._close_scene(current_scene_id, reason or "Scene transition")

        # Get chapter to determine participants
        chapter = await db.chapters.find_one({"id": current_chapter_id})

        # Create new scene
        scene_name = suggested_name or "Untitled Scene"

        new_scene = Scene(
            id=scene_id,
            chapter_id=current_chapter_id,
            name=scene_name,
            description=f"Transition from previous scene. Reason: {reason or 'Not specified'}",
            summary="Scene in progress",
            turns=[],  # Empty turns list
            status="active",
            meta=Meta(created_by=created_by),
            changes=[Change(by=created_by, type="created")]
        )

        # If current scene had participants, carry them over
        if current_scene.get("participants"):
            new_scene.dict()["participants"] = current_scene["participants"]

        # Insert new scene
        await db.scenes.insert_one(new_scene.dict())

        # Add scene to chapter's scenes array
        await db.chapters.update_one(
            {"id": current_chapter_id},
            {"$push": {"scenes": scene_id}}
        )

        logger.info(f"Created new scene {scene_id} ({scene_name})")

        return TransitionResult(
            transition_occurred=True,
            transition_type="scene",
            new_scene_id=scene_id,
            scene_name=scene_name
        )

    async def _create_new_chapter(
        self,
        campaign_id: str,
        current_scene_id: str,
        turn_id: str,
        suggested_name: Optional[str],
        reason: Optional[str],
        created_by: str
    ) -> TransitionResult:
        """
        Create a new chapter (and initial scene).

        Steps:
        1. Close current scene
        2. Close current chapter (mark as completed)
        3. Create new chapter
        4. Create initial scene in new chapter
        5. Add new chapter to campaign's chapters array
        """
        logger.info(
            f"Creating new chapter in campaign {campaign_id} "
            f"(triggered by turn {turn_id})"
        )

        db = get_gamerecords_db()

        # Generate IDs
        chapter_id = f"chapter-{uuid.uuid4().hex[:8]}"
        scene_id = f"scene-{uuid.uuid4().hex[:8]}"

        # Get current scene for context
        current_scene = await db.scenes.find_one({"id": current_scene_id})
        if not current_scene:
            logger.error(f"Current scene {current_scene_id} not found")
            raise ValueError(f"Scene {current_scene_id} not found")

        # Close current scene
        await self._close_scene(current_scene_id, reason or "Chapter transition")

        # Get and close current chapter
        current_chapter_id = current_scene.get("chapter_id")
        if current_chapter_id:
            await self._close_chapter(current_chapter_id, reason or "Chapter transition")

        # Get campaign to determine next chapter order
        campaign = await db.campaigns.find_one({"id": campaign_id})
        if not campaign:
            logger.error(f"Campaign {campaign_id} not found")
            raise ValueError(f"Campaign {campaign_id} not found")

        # Determine chapter order
        existing_chapters = campaign.get("story_arc", {}).get("chapters", [])
        chapter_order = len(existing_chapters) + 1

        # Create new chapter
        chapter_name = suggested_name or "Untitled Chapter"

        new_chapter = Chapter(
            id=chapter_id,
            campaign_id=campaign_id,
            name=chapter_name,
            description=f"New chapter. Reason: {reason or 'Not specified'}",
            summary="Chapter in progress",
            scenes=[scene_id],  # Initial scene
            status="active",
            meta=Meta(created_by=created_by),
            changes=[Change(by=created_by, type="created")]
        )

        # Add order field if it exists in the model
        chapter_dict = new_chapter.dict()
        chapter_dict["order"] = chapter_order

        # Insert new chapter
        await db.chapters.insert_one(chapter_dict)

        # Create initial scene in new chapter
        new_scene = Scene(
            id=scene_id,
            chapter_id=chapter_id,
            name="Opening Scene",
            description=f"Opening scene of {chapter_name}",
            summary="Scene in progress",
            turns=[],
            status="active",
            meta=Meta(created_by=created_by),
            changes=[Change(by=created_by, type="created")]
        )

        # Carry over participants from previous scene
        if current_scene.get("participants"):
            new_scene.dict()["participants"] = current_scene["participants"]

        # Insert new scene
        await db.scenes.insert_one(new_scene.dict())

        # Add chapter to campaign (update story_arc.chapters array)
        await db.campaigns.update_one(
            {"id": campaign_id},
            {"$push": {"story_arc.chapters": chapter_id}}
        )

        logger.info(
            f"Created new chapter {chapter_id} ({chapter_name}) "
            f"with initial scene {scene_id}"
        )

        return TransitionResult(
            transition_occurred=True,
            transition_type="chapter",
            new_chapter_id=chapter_id,
            new_scene_id=scene_id,
            chapter_name=chapter_name,
            scene_name="Opening Scene"
        )

    async def _close_scene(self, scene_id: str, reason: str):
        """Mark a scene as completed."""
        db = get_gamerecords_db()

        # Generate summary from scene turns (simplified)
        scene = await db.scenes.find_one({"id": scene_id})
        if not scene:
            return

        turn_count = len(scene.get("turns", []))
        summary = f"{scene.get('name', 'Scene')} completed. {turn_count} turns. {reason}"

        await db.scenes.update_one(
            {"id": scene_id},
            {
                "$set": {
                    "status": "completed",
                    "summary": summary
                },
                "$push": {
                    "changes": {
                        "by": "DungeonMasterAI",
                        "at": datetime.utcnow(),
                        "type": "completed"
                    }
                }
            }
        )

        logger.info(f"Closed scene {scene_id}")

    async def _close_chapter(self, chapter_id: str, reason: str):
        """Mark a chapter as completed."""
        db = get_gamerecords_db()

        # Generate summary from chapter scenes (simplified)
        chapter = await db.chapters.find_one({"id": chapter_id})
        if not chapter:
            return

        scene_count = len(chapter.get("scenes", []))
        summary = f"{chapter.get('name', 'Chapter')} completed. {scene_count} scenes. {reason}"

        await db.chapters.update_one(
            {"id": chapter_id},
            {
                "$set": {
                    "status": "completed",
                    "summary": summary
                },
                "$push": {
                    "changes": {
                        "by": "DungeonMasterAI",
                        "at": datetime.utcnow(),
                        "type": "completed"
                    }
                }
            }
        )

        logger.info(f"Closed chapter {chapter_id}")
