"""
Context assembly service for turn processing.

Assembles complete context bundles including:
- Campaign, chapter, scene data
- Previous turns for continuity
- Character data with stats
- Lore context from Qdrant RAG
- Pre-rolled skill checks
"""
import logging
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from ..database import get_gamerecords_db

logger = logging.getLogger(__name__)


# ============== Context Bundle Models ==============

class RealmContext(BaseModel):
    """Realm context for LLM - provides overall tone/notes."""
    id: str
    name: str
    setting: Optional[Dict[str, Any]] = None  # tone, notes


class CampaignContext(BaseModel):
    """Campaign context for LLM."""
    id: str
    name: str
    setting: Optional[Dict[str, Any]] = None  # Full setting dict: tone, goal, key_elements, etc.
    story_arc: Optional[Dict[str, Any]] = None  # Full story_arc dict: tagline, chapters, etc.


class ChapterContext(BaseModel):
    """Chapter context for LLM."""
    id: str
    name: str
    summary: Optional[str] = None
    order: Optional[int] = 1


class SceneContext(BaseModel):
    """Scene context for LLM."""
    id: str
    name: str
    location: Optional[str] = None
    summary: Optional[str] = None
    status: str = "active"
    participants: List[str] = Field(default_factory=list)
    turn_count: int = 0  # Number of completed turns in this scene
    pacing_phase: str = "establishment"  # establishment, unease, investigation, revelation, resolution


class TurnSummary(BaseModel):
    """Summary of a previous turn for context."""
    order: int
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    reaction: Optional[Dict[str, Any]] = None


class CharacterSkill(BaseModel):
    """Simplified character skill for context."""
    name: str
    value: int


class CharacterStats(BaseModel):
    """Simplified character stats for context."""
    sanity: Dict[str, int] = Field(default_factory=dict)
    hp: Dict[str, int] = Field(default_factory=dict)
    mp: Dict[str, int] = Field(default_factory=dict)


class CharacterContext(BaseModel):
    """Character context for LLM."""
    id: str
    name: str
    occupation: Optional[str] = None
    age: Optional[str] = None
    pronoun: Optional[str] = None
    birthplace: Optional[str] = None
    residence: Optional[str] = None
    backstory: Optional[str] = None  # Summarized backstory for DM context
    skills: List[CharacterSkill] = Field(default_factory=list)
    stats: Optional[CharacterStats] = None
    conditions: List[str] = Field(default_factory=list)
    ai_controlled: bool = False
    ai_personality: Optional[str] = None


class LoreChunk(BaseModel):
    """Lore context from RAG."""
    source: str
    content: str
    relevance_score: float = 0.0


class NPCContext(BaseModel):
    """NPC context for LLM."""
    id: str
    name: str
    description: str
    role: str = "neutral"
    personality: str = ""
    goals: List[str] = Field(default_factory=list)
    knowledge: List[str] = Field(default_factory=list)
    current_location: Optional[str] = None
    status: str = "active"


class SkillCheckContext(BaseModel):
    """Pre-rolled skill check result for context."""
    character_id: str
    character_name: str
    skill_name: str
    skill_value: int
    difficulty: str = "Regular"
    rolled: int = 0
    target_regular: int = 0
    target_hard: int = 0
    target_extreme: int = 0
    success_level: str = "Failure"
    success: bool = False
    formatted: str = ""


class CurrentTurnActions(BaseModel):
    """Current turn actions to process."""
    order: int
    actions: List[Dict[str, Any]] = Field(default_factory=list)


class ContextData(BaseModel):
    """Complete context data bundle."""
    realm: Optional[RealmContext] = None
    campaign: Optional[CampaignContext] = None
    chapter: Optional[ChapterContext] = None
    scene: Optional[SceneContext] = None
    previous_turns: List[TurnSummary] = Field(default_factory=list)
    characters: List[CharacterContext] = Field(default_factory=list)
    npcs: List[NPCContext] = Field(default_factory=list)
    lore_context: List[LoreChunk] = Field(default_factory=list)
    skill_checks: List[SkillCheckContext] = Field(default_factory=list)


class ContextBundle(BaseModel):
    """
    Complete context bundle sent to n8n for LLM processing.

    Matches the schema expected by DungeonMaster_Main workflow.
    """
    turn_id: str
    callback_url: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context: ContextData
    actions: List[Dict[str, Any]] = Field(default_factory=list)  # Top-level for n8n workflow


# ============== Context Assembly Service ==============

class ContextAssemblyService:
    """Service for assembling complete context bundles."""

    def __init__(self):
        """Initialize the context assembly service."""
        self.max_previous_turns = 5  # Limit context window
        self.max_characters = 10  # Limit to scene participants
        self.max_lore_chunks = 3  # Top N most relevant chunks

    async def assemble_context(
        self,
        turn_id: str,
        callback_url: str,
        skill_checks: Optional[List[SkillCheckContext]] = None
    ) -> ContextBundle:
        """
        Assemble complete context bundle for a turn.

        Args:
            turn_id: ID of the turn being processed
            callback_url: Backend callback URL for n8n
            skill_checks: Pre-rolled skill check results (optional)

        Returns:
            Complete ContextBundle ready for n8n

        Raises:
            ValueError: If turn not found or missing required data
        """
        logger.info(f"Assembling context for turn {turn_id}")

        db = get_gamerecords_db()

        # Fetch the turn
        turn = await db.turns.find_one({"id": turn_id})
        if not turn:
            raise ValueError(f"Turn {turn_id} not found")

        scene_id = turn.get("scene_id")
        if not scene_id:
            raise ValueError(f"Turn {turn_id} has no scene_id")

        # Fetch scene
        scene = await db.scenes.find_one({"id": scene_id})
        if not scene:
            logger.warning(f"Scene {scene_id} not found")
            scene = {}

        # Fetch chapter
        chapter_id = scene.get("chapter_id")
        chapter = None
        if chapter_id:
            chapter = await db.chapters.find_one({"id": chapter_id})

        # Fetch campaign
        campaign_id = chapter.get("campaign_id") if chapter else None
        campaign = None
        if campaign_id:
            campaign = await db.campaigns.find_one({"id": campaign_id})

        # Fetch realm (for overall tone/setting)
        realm_id = campaign.get("realm_id") if campaign else None
        realm = None
        if realm_id:
            realm = await db.realms.find_one({"id": realm_id})

        # Assemble context components
        realm_ctx = await self._assemble_realm_context(realm)
        campaign_ctx = await self._assemble_campaign_context(campaign)
        chapter_ctx = await self._assemble_chapter_context(chapter)
        scene_ctx = await self._assemble_scene_context(scene)
        previous_turns = await self._fetch_previous_turns(scene_id, turn.get("order", 1))
        characters = await self._fetch_characters(scene.get("participants", []))
        npcs = await self._fetch_npcs(scene.get("npcs_present", []))
        lore_chunks = await self._fetch_lore_context(turn.get("actions", []))

        # Build context bundle
        context_data = ContextData(
            realm=realm_ctx,
            campaign=campaign_ctx,
            chapter=chapter_ctx,
            scene=scene_ctx,
            previous_turns=previous_turns,
            characters=characters,
            npcs=npcs,
            lore_context=lore_chunks,
            skill_checks=skill_checks or []
        )

        # Get actions from turn for top-level actions field
        turn_actions = turn.get("actions", [])

        bundle = ContextBundle(
            turn_id=turn_id,
            callback_url=callback_url,
            context=context_data,
            actions=turn_actions  # Top-level for n8n workflow compatibility
        )

        logger.info(
            f"Context assembled: {len(characters)} characters, "
            f"{len(npcs)} NPCs, "
            f"{len(previous_turns)} previous turns, "
            f"{len(lore_chunks)} lore chunks, "
            f"{len(skill_checks or [])} skill checks"
        )

        return bundle

    async def _assemble_realm_context(
        self,
        realm: Optional[Dict[str, Any]]
    ) -> Optional[RealmContext]:
        """Extract realm context from MongoDB document."""
        if not realm:
            return None

        return RealmContext(
            id=realm.get("id", ""),
            name=realm.get("name", "Untitled Realm"),
            setting=realm.get("setting") if isinstance(realm.get("setting"), dict) else None
        )

    async def _assemble_campaign_context(
        self,
        campaign: Optional[Dict[str, Any]]
    ) -> Optional[CampaignContext]:
        """Extract campaign context from MongoDB document."""
        if not campaign:
            return None

        return CampaignContext(
            id=campaign.get("id", ""),
            name=campaign.get("name", "Untitled Campaign"),
            setting=campaign.get("setting") if isinstance(campaign.get("setting"), dict) else None,
            story_arc=campaign.get("story_arc") if isinstance(campaign.get("story_arc"), dict) else None
        )

    async def _assemble_chapter_context(
        self,
        chapter: Optional[Dict[str, Any]]
    ) -> Optional[ChapterContext]:
        """Extract chapter context from MongoDB document."""
        if not chapter:
            return None

        return ChapterContext(
            id=chapter.get("id", ""),
            name=chapter.get("name", "Untitled Chapter"),
            summary=chapter.get("summary"),
            order=chapter.get("order", 1)
        )

    async def _assemble_scene_context(
        self,
        scene: Optional[Dict[str, Any]]
    ) -> Optional[SceneContext]:
        """Extract scene context from MongoDB document."""
        if not scene:
            return None

        # Count completed turns in this scene
        scene_id = scene.get("id", "")
        turn_count = await self._count_scene_turns(scene_id)
        pacing_phase = self._determine_pacing_phase(turn_count)

        return SceneContext(
            id=scene_id,
            name=scene.get("name", "Untitled Scene"),
            location=scene.get("description"),  # Using description as location
            summary=scene.get("summary"),
            status=scene.get("status", "active"),
            participants=scene.get("participants", []),
            turn_count=turn_count,
            pacing_phase=pacing_phase
        )

    async def _count_scene_turns(self, scene_id: str) -> int:
        """Count completed turns in a scene."""
        if not scene_id:
            return 0
        
        db = get_gamerecords_db()
        count = await db.turns.count_documents({
            "scene_id": scene_id,
            "status": "completed"
        })
        return count

    def _determine_pacing_phase(self, turn_count: int) -> str:
        """
        Determine pacing phase based on turn count.
        
        Phases (from DUNGEONMASTER_AGENT.md):
        - establishment: turns 1-5 (mundane, introductions)
        - unease: turns 6-15 (subtle wrongness, hints)
        - investigation: turns 16-35 (clues, stakes)
        - revelation: turns 36-45 (horror manifests)
        - resolution: turns 46+ (consequences)
        """
        if turn_count <= 5:
            return "establishment"
        elif turn_count <= 15:
            return "unease"
        elif turn_count <= 35:
            return "investigation"
        elif turn_count <= 45:
            return "revelation"
        else:
            return "resolution"

    async def _fetch_previous_turns(
        self,
        scene_id: str,
        current_turn_order: int
    ) -> List[TurnSummary]:
        """
        Fetch previous turns in the scene for context continuity.

        Limited to last N turns to keep context size manageable.
        """
        db = get_gamerecords_db()

        # Fetch turns before current one
        cursor = db.turns.find({
            "scene_id": scene_id,
            "order": {"$lt": current_turn_order}
        }).sort("order", -1).limit(self.max_previous_turns)

        turns_list = await cursor.to_list(length=self.max_previous_turns)

        # Reverse to get chronological order
        turns_list.reverse()

        summaries = []
        for turn_doc in turns_list:
            reaction = turn_doc.get("reaction")
            summaries.append(TurnSummary(
                order=turn_doc.get("order", 0),
                actions=turn_doc.get("actions", []),
                reaction={
                    "description": reaction.get("description", "") if reaction else "",
                    "summary": reaction.get("summary", "") if reaction else ""
                } if reaction else None
            ))

        return summaries

    async def _fetch_characters(
        self,
        character_ids: List[str]
    ) -> List[CharacterContext]:
        """
        Fetch character data for participants in the scene.

        Extracts relevant skills, stats, and background info for LLM context.
        """
        if not character_ids:
            return []

        db = get_gamerecords_db()

        # Limit to max characters
        limited_ids = character_ids[:self.max_characters]

        # Query entities collection for player characters (kind: "pc")
        cursor = db.entities.find({"id": {"$in": limited_ids}, "kind": "pc"})
        char_docs = await cursor.to_list(length=self.max_characters)

        characters = []
        for char in char_docs:
            # Extract skills from character sheet
            skills = []
            char_data = char.get("data", {})
            char_skills = char_data.get("skills", {})

            for skill_name, skill_data in char_skills.items():
                if isinstance(skill_data, dict):
                    value_str = skill_data.get("reg", "0")
                    try:
                        value = int(value_str) if value_str else 0
                    except (ValueError, TypeError):
                        value = 0

                    if value > 0:  # Only include skills with values
                        skills.append(CharacterSkill(name=skill_name, value=value))

            # Extract stats
            investigator = char_data.get("investigator", {})
            hp_data = char_data.get("hit_points", {})
            mp_data = char_data.get("magic_points", {})
            sanity_data = char_data.get("sanity", {})

            stats = CharacterStats(
                hp={
                    "current": self._parse_int(hp_data.get("current", 0)),
                    "max": self._parse_int(hp_data.get("max", 0))
                },
                mp={
                    "current": self._parse_int(mp_data.get("current", 0)),
                    "max": self._parse_int(mp_data.get("max", 0))
                },
                sanity={
                    "current": self._parse_int(sanity_data.get("current", 0)),
                    "max": self._parse_int(sanity_data.get("max", 0))
                }
            )

            # Extract conditions
            status = char_data.get("status", {})
            conditions = []
            if status.get("temporary_insanity"):
                conditions.append("Temporary Insanity")
            if status.get("indefinite_insanity"):
                conditions.append("Indefinite Insanity")
            if status.get("major_wound"):
                conditions.append("Major Wound")
            if status.get("unconscious"):
                conditions.append("Unconscious")
            if status.get("dying"):
                conditions.append("Dying")

            # Extract background info for DM context
            backstory_data = char_data.get("story", {}).get("backstory", {})
            backstory_summary = self._summarize_backstory(backstory_data)

            characters.append(CharacterContext(
                id=char.get("id", ""),
                name=char.get("name", "Unknown"),
                occupation=investigator.get("occupation") if isinstance(investigator, dict) else None,
                age=investigator.get("age") if isinstance(investigator, dict) else None,
                pronoun=investigator.get("pronoun") if isinstance(investigator, dict) else None,
                birthplace=investigator.get("birthplace") if isinstance(investigator, dict) else None,
                residence=investigator.get("residence") if isinstance(investigator, dict) else None,
                backstory=backstory_summary,
                skills=skills,
                stats=stats,
                conditions=conditions,
                ai_controlled=char.get("ai_controlled", False),
                ai_personality=char.get("ai_personality")
            ))

        return characters

    def _summarize_backstory(self, backstory: Dict[str, Any]) -> Optional[str]:
        """
        Summarize character backstory for DM context.
        
        Combines key backstory fields into a concise summary (max 300 chars).
        """
        if not backstory:
            return None
        
        parts = []
        
        # Personal description - most relevant
        if backstory.get("personal_description"):
            parts.append(backstory["personal_description"][:100])
        
        # Traits - personality characteristics
        if backstory.get("traits"):
            parts.append(f"Traits: {backstory['traits'][:80]}")
        
        # Ideology - motivations
        if backstory.get("ideology_beliefs"):
            parts.append(f"Beliefs: {backstory['ideology_beliefs'][:80]}")
        
        if not parts:
            return None
        
        summary = " | ".join(parts)
        return summary[:300] if summary else None

    async def _fetch_npcs(
        self,
        npc_ids: List[str]
    ) -> List[NPCContext]:
        """
        Fetch NPC data for NPCs present in the scene.

        Returns simplified NPC context for LLM.
        """
        if not npc_ids:
            return []

        db = get_gamerecords_db()

        # Fetch NPCs from entities collection
        cursor = db.entities.find({"id": {"$in": npc_ids}, "kind": "npc"})
        npc_docs = await cursor.to_list(length=20)  # Max 20 NPCs per scene

        npcs = []
        for npc in npc_docs:
            npcs.append(NPCContext(
                id=npc.get("id", ""),
                name=npc.get("name", "Unknown"),
                description=npc.get("description", ""),
                role=npc.get("role", "neutral"),
                personality=npc.get("personality", ""),
                goals=npc.get("goals", []),
                knowledge=npc.get("knowledge", []),
                current_location=npc.get("current_location"),
                status=npc.get("status", "active")
            ))

        return npcs

    def _parse_int(self, value: Any) -> int:
        """Safely parse integer from various types."""
        try:
            if isinstance(value, (int, float)):
                return int(value)
            if isinstance(value, str):
                return int(value) if value else 0
            return 0
        except (ValueError, TypeError):
            return 0

    async def _fetch_lore_context(
        self,
        actions: List[Dict[str, Any]]
    ) -> List[LoreChunk]:
        """
        Fetch relevant lore from Qdrant based on player actions.

        TODO: Implement Qdrant integration for RAG.
        For now, returns empty list.
        """
        # Placeholder for Qdrant integration
        # This will be implemented when Qdrant service is available
        logger.debug("Lore context fetch not yet implemented (Qdrant integration pending)")
        return []
