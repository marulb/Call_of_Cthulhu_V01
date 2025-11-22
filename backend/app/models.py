"""
Pydantic models for game entities based on data.md schema.
All entities track changes with timestamp and player name.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class EntityKind(str, Enum):
    """Entity type classification."""
    WORLD = "world"
    REALM = "realm"
    CAMPAIGN = "campaign"
    CHAPTER = "chapter"
    SCENE = "scene"
    TURN = "turn"
    SESSION = "session"
    PC = "pc"  # Player character
    NPC = "npc"
    BEAST = "beast"
    OBJECT = "object"
    LOCATION = "location"


class CampaignStatus(str, Enum):
    """Campaign status options."""
    PLANNING = "planning"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"


class Change(BaseModel):
    """Change tracking for audit trail."""
    by: str
    at: datetime = Field(default_factory=datetime.utcnow)
    type: Optional[str] = None


class Meta(BaseModel):
    """Metadata for entity creation."""
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============== NARRATIVE LAYER MODELS ==============

class World(BaseModel):
    """World entity - defines ruleset and lore."""
    id: Optional[str] = None
    kind: EntityKind = EntityKind.WORLD
    name: str
    ruleset: Optional[str] = None
    description: Optional[str] = None
    meta: Meta
    changes: List[Change] = Field(default_factory=list)

    class Config:
        use_enum_values = True


class Player(BaseModel):
    """Player reference within a realm."""
    id: str
    name: str


class Realm(BaseModel):
    """Realm entity - player group within a world."""
    id: Optional[str] = None
    kind: EntityKind = EntityKind.REALM
    world_id: str
    name: str
    description: Optional[str] = None
    players: List[Player] = Field(default_factory=list)
    characters: List[str] = Field(default_factory=list)  # Character IDs
    campaigns: List[str] = Field(default_factory=list)  # Campaign IDs
    meta: Meta
    changes: List[Change] = Field(default_factory=list)
    setting: Optional[Dict[str, Any]] = None

    class Config:
        use_enum_values = True


class StoryArc(BaseModel):
    """Story arc structure for campaigns."""
    tagline: Optional[str] = None
    chapters: List[str] = Field(default_factory=list)  # Chapter IDs


class Campaign(BaseModel):
    """Campaign entity - story arc within a realm."""
    id: Optional[str] = None
    kind: EntityKind = EntityKind.CAMPAIGN
    realm_id: str
    name: str
    description: Optional[str] = None
    status: CampaignStatus = CampaignStatus.PLANNING
    story_arc: Optional[StoryArc] = None
    setting: Optional[Dict[str, Any]] = None
    meta: Meta
    changes: List[Change] = Field(default_factory=list)

    class Config:
        use_enum_values = True


class Controller(BaseModel):
    """Controller configuration for entities."""
    owner: str  # player name or "gm"
    mode: str  # "player", "gm", "ai"
    agent: Optional[str] = None  # "human" or agent name


class Character(BaseModel):
    """Character entity (PC) - belongs to realm."""
    id: Optional[str] = None
    uid: Optional[str] = None  # Unique character ID
    kind: EntityKind = EntityKind.PC
    type: Optional[str] = "investigator"
    name: str
    realm_id: str
    description: Optional[str] = None
    controller: Controller
    data: Dict[str, Any] = Field(default_factory=dict)  # Character sheet, stats, etc.
    meta: Meta
    visibility: str = "realm"
    changes: List[Change] = Field(default_factory=list)

    class Config:
        use_enum_values = True


# ============== SESSION LAYER MODELS ==============

class Attendance(BaseModel):
    """Session attendance tracking."""
    players_present: List[str] = Field(default_factory=list)
    players_absent: List[str] = Field(default_factory=list)


class StoryLinks(BaseModel):
    """Links to narrative elements covered in session."""
    chapters: List[str] = Field(default_factory=list)
    scenes: List[str] = Field(default_factory=list)
    active_chapter_index: Optional[int] = None
    active_scene_index: Optional[int] = None


class Chapter(BaseModel):
    """Chapter entity - AI-managed narrative arc within campaign."""
    id: Optional[str] = None
    kind: EntityKind = EntityKind.CHAPTER
    campaign_id: str
    name: str
    description: Optional[str] = None
    summary: Optional[str] = None  # AI-generated summary
    scenes: List[str] = Field(default_factory=list)  # Scene IDs
    status: str = "active"  # active, completed
    meta: Meta
    changes: List[Change] = Field(default_factory=list)

    class Config:
        use_enum_values = True


class Scene(BaseModel):
    """Scene entity - AI-managed story segment within chapter."""
    id: Optional[str] = None
    kind: EntityKind = EntityKind.SCENE
    chapter_id: str
    name: str
    description: Optional[str] = None
    summary: Optional[str] = None  # AI-generated summary
    turns: List[str] = Field(default_factory=list)  # Turn IDs
    status: str = "active"  # active, completed
    meta: Meta
    changes: List[Change] = Field(default_factory=list)

    class Config:
        use_enum_values = True


class Action(BaseModel):
    """Individual action within a turn."""
    actor_id: str  # Character ID
    controller_owner: str  # Player ID
    speak: Optional[str] = None
    act: Optional[str] = None
    appearance: Optional[str] = None
    emotion: Optional[str] = None
    ooc: Optional[str] = None  # Out-of-character notes
    meta: Dict[str, Any] = Field(default_factory=dict)  # ready, resolved flags


class Reaction(BaseModel):
    """Keeper's response to turn actions."""
    description: str  # Scene narrative from Keeper AI
    summary: Optional[str] = None  # AI-generated summary for context


class Turn(BaseModel):
    """Turn entity - player actions + Keeper response."""
    id: Optional[str] = None
    kind: EntityKind = EntityKind.TURN
    scene_id: str
    order: int  # Turn number in scene
    actions: List[Action] = Field(default_factory=list)
    reaction: Optional[Reaction] = None  # Keeper's narrative response
    status: str = "draft"  # draft, ready_for_agents, processing, completed
    meta: Meta
    changes: List[Change] = Field(default_factory=list)

    class Config:
        use_enum_values = True


class ActionDraft(BaseModel):
    """Temporary action draft for UI state (cleared after turn submission)."""
    id: Optional[str] = None
    session_id: str
    player_id: str
    character_id: str
    speak: Optional[str] = None
    act: Optional[str] = None
    appearance: Optional[str] = None
    emotion: Optional[str] = None
    ooc: Optional[str] = None
    order: int = 0
    ready: bool = False
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Session(BaseModel):
    """Session entity - real-world play instance."""
    id: Optional[str] = None
    kind: EntityKind = EntityKind.SESSION
    realm_id: str
    campaign_id: str
    session_number: int
    master_player_id: Optional[str] = None  # Player ID of current master
    attendance: Attendance
    story_links: Optional[StoryLinks] = None
    notes: Optional[str] = None
    meta: Meta
    changes: List[Change] = Field(default_factory=list)

    class Config:
        use_enum_values = True


# ============== REQUEST/RESPONSE MODELS ==============

class WorldCreate(BaseModel):
    """Request model for creating a world."""
    name: str
    ruleset: Optional[str] = None
    description: Optional[str] = None
    created_by: str


class RealmCreate(BaseModel):
    """Request model for creating a realm."""
    world_id: str
    name: str
    description: Optional[str] = None
    created_by: str


class CampaignCreate(BaseModel):
    """Request model for creating a campaign."""
    realm_id: str
    name: str
    description: Optional[str] = None
    status: CampaignStatus = CampaignStatus.PLANNING
    created_by: str


class CharacterCreate(BaseModel):
    """Request model for creating a character."""
    realm_id: str
    name: str
    type: Optional[str] = "investigator"
    description: Optional[str] = None
    owner: str  # Player name
    created_by: str


class SessionCreate(BaseModel):
    """Request model for creating a session."""
    realm_id: str
    campaign_id: str
    session_number: int
    master_player_id: Optional[str] = None
    players_present: List[str]
    players_absent: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    created_by: str


class ChapterCreate(BaseModel):
    """Request model for creating a chapter (AI-managed)."""
    campaign_id: str
    name: str
    description: Optional[str] = None
    created_by: str = "KeeperAI"


class SceneCreate(BaseModel):
    """Request model for creating a scene (AI-managed)."""
    chapter_id: str
    name: str
    description: Optional[str] = None
    created_by: str = "KeeperAI"


class TurnCreate(BaseModel):
    """Request model for creating a turn."""
    scene_id: str
    order: int
    actions: List[Action] = Field(default_factory=list)
    created_by: str


class ActionDraftCreate(BaseModel):
    """Request model for creating/updating action draft."""
    session_id: str
    player_id: str
    character_id: str
    speak: Optional[str] = None
    act: Optional[str] = None
    appearance: Optional[str] = None
    emotion: Optional[str] = None
    ooc: Optional[str] = None
    order: int = 0
    ready: bool = False
