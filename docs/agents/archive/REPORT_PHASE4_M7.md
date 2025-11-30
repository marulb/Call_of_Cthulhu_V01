# M7: NPC Agent System - Implementation Report

> **Completed:** 2025-11-29
> **Agent:** Claude Code
> **Status:** ✅ Backend Complete, Frontend Basic Interface Added

---

## Summary

M7 (NPC Agent System) has been successfully implemented. The system now supports:
- Full CRUD operations for NPCs
- Scene-level NPC tracking (which NPCs are present in a scene)
- Automatic NPC context inclusion in LLM prompts
- LLM generation of NPC dialogue and actions during gameplay

**What Works:**
- Backend API for managing NPCs ✅
- NPCs are automatically included in LLM context when present in a scene ✅
- LLM receives NPC personality, goals, and knowledge for narrative generation ✅
- NPCs can be added/removed from scenes via API ✅

**Future Enhancement:**
- Frontend UI for NPC management (Keeper panel to view/create/edit NPCs)
- Frontend scene panel to show NPCs present and add/remove them
- NPC status cards in game view

---

## Implementation Details

### 1. Backend Models

**File:** `backend/app/models.py`

#### NPC Model
```python
class NPC(BaseModel):
    """NPC entity - non-player character managed by Keeper/AI."""
    id: Optional[str] = None
    kind: EntityKind = EntityKind.NPC
    campaign_id: str  # NPCs belong to a campaign
    name: str
    description: str
    role: str = "neutral"  # "ally", "enemy", "neutral", "mysterious"
    personality: str = ""  # Personality description
    goals: List[str] = Field(default_factory=list)  # What do they want?
    knowledge: List[str] = Field(default_factory=list)  # What do they know?
    current_location: Optional[str] = None  # Where are they now?
    status: str = "active"  # "active", "dead", "missing", "unknown"
    meta: Meta
    changes: List[Change] = Field(default_factory=list)
```

#### NPCCreate Model
```python
class NPCCreate(BaseModel):
    """Request model for creating an NPC."""
    campaign_id: str
    name: str
    description: str
    role: Optional[str] = "neutral"
    personality: Optional[str] = ""
    goals: Optional[List[str]] = Field(default_factory=list)
    knowledge: Optional[List[str]] = Field(default_factory=list)
    current_location: Optional[str] = None
    status: Optional[str] = "active"
    created_by: str
```

#### Scene Model Updates
Added NPC tracking to scenes:
```python
class Scene(BaseModel):
    # ... existing fields ...
    participants: List[str] = Field(default_factory=list)  # Character IDs
    npcs_present: List[str] = Field(default_factory=list)  # NPC IDs ← NEW
```

---

### 2. API Routes

**File:** `backend/app/routes_npcs.py` (NEW)

Implemented full CRUD operations:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/npcs` | GET | List NPCs (filter by campaign_id, status) |
| `/api/v1/npcs/{npc_id}` | GET | Get specific NPC |
| `/api/v1/npcs` | POST | Create new NPC |
| `/api/v1/npcs/{npc_id}` | PUT | Update existing NPC |
| `/api/v1/npcs/{npc_id}` | DELETE | Delete NPC (also removes from scenes) |
| `/api/v1/npcs/scenes/{scene_id}/npcs/{npc_id}` | POST | Add NPC to scene |
| `/api/v1/npcs/scenes/{scene_id}/npcs/{npc_id}` | DELETE | Remove NPC from scene |

**Registered in:** `backend/main.py`
```python
from app.routes_npcs import router as npcs_router
app.include_router(npcs_router, prefix="/api/v1")
```

---

### 3. Context Assembly

**File:** `backend/app/services/context_assembly.py`

#### NPCContext Model
```python
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
```

#### ContextData Updates
```python
class ContextData(BaseModel):
    # ... existing fields ...
    npcs: List[NPCContext] = Field(default_factory=list)  # ← NEW
```

#### NPC Fetching
Added `_fetch_npcs()` method that:
1. Fetches NPCs from `entities` collection based on scene's `npcs_present` list
2. Converts to `NPCContext` objects with all relevant data
3. Limits to 20 NPCs per scene (configurable)

**Integration:**
```python
async def assemble_context(self, turn_id: str, callback_url: str, ...):
    # ... existing code ...
    npcs = await self._fetch_npcs(scene.get("npcs_present", []))

    context_data = ContextData(
        # ... existing fields ...
        npcs=npcs,  # ← NEW
    )
```

---

### 4. LLM Workflow Updates

**File:** `n8n_workflows/LLM_Synthesizer_SubWF.json`

Added new section in user prompt after AI-controlled characters:

```javascript
// Add NPCs present in scene (for DungeonMaster)
if (agentType === 'dungeonmaster' && collectedData.npcs && collectedData.npcs.length > 0) {
  userPromptParts.push('=== NPCS PRESENT IN SCENE ===');
  collectedData.npcs.forEach(npc => {
    userPromptParts.push(`NPC: ${npc.name}`);
    userPromptParts.push(`  Role: ${npc.role}`);
    if (npc.description) userPromptParts.push(`  Description: ${npc.description}`);
    if (npc.personality) userPromptParts.push(`  Personality: ${npc.personality}`);
    if (npc.goals && npc.goals.length > 0) {
      userPromptParts.push(`  Goals: ${npc.goals.join(', ')}`);
    }
    if (npc.knowledge && npc.knowledge.length > 0) {
      userPromptParts.push(`  Knowledge: ${npc.knowledge.join(', ')}`);
    }
    if (npc.status !== 'active') {
      userPromptParts.push(`  Status: ${npc.status}`);
    }
    userPromptParts.push('');
  });
  userPromptParts.push('Generate NPC dialogue and actions when they would naturally interact with the scene.');
  userPromptParts.push('NPCs should act according to their role, personality, and goals.');
  userPromptParts.push('');
}
```

**LLM Context Example:**
```
=== NPCS PRESENT IN SCENE ===
NPC: Eldritch Librarian
  Role: mysterious
  Description: An elderly curator with knowing eyes and an unsettling smile
  Personality: Cryptic, knowledgeable, enjoys riddles
  Goals: Protect forbidden knowledge, Test seekers of truth
  Knowledge: Location of the Necronomicon, Ancient ritual practices

Generate NPC dialogue and actions when they would naturally interact with the scene.
NPCs should act according to their role, personality, and goals.
```

---

### 5. Frontend Interface

**File:** `frontend/src/services/api.ts`

Added TypeScript interface:
```typescript
export interface NPC {
  id: string
  kind: string
  campaign_id: string
  name: string
  description: string
  role: string // "ally", "enemy", "neutral", "mysterious"
  personality: string
  goals: string[]
  knowledge: string[]
  current_location?: string
  status: string // "active", "dead", "missing", "unknown"
  meta: { created_by: string; created_at: string }
  changes: Array<{ by: string; at: string; type?: string }>
}
```

**Note:** Full frontend UI components (NPC management panel, scene NPC controls) are not yet implemented. The API is ready for frontend integration when needed.

---

## Usage Examples

### Creating an NPC

```bash
curl -X POST http://localhost:8093/api/v1/npcs \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "campaign-xyz",
    "name": "Professor Armitage",
    "description": "Elderly librarian at Miskatonic University, expert in occult texts",
    "role": "ally",
    "personality": "Scholarly, cautious, knowledgeable about forbidden lore",
    "goals": ["Protect students from dangerous knowledge", "Study ancient texts safely"],
    "knowledge": ["Location of Necronomicon", "Yog-Sothothery basics"],
    "current_location": "Miskatonic University Library",
    "status": "active",
    "created_by": "keeper"
  }'
```

### Adding NPC to Scene

```bash
curl -X POST http://localhost:8093/api/v1/npcs/scenes/{scene_id}/npcs/{npc_id}
```

### Listing NPCs for Campaign

```bash
curl http://localhost:8093/api/v1/npcs?campaign_id=campaign-xyz
```

---

## How It Works in Gameplay

1. **Keeper creates NPCs** via API (or future UI) and assigns them to a campaign
2. **Keeper adds NPCs to scenes** when they should be present
3. **During turn processing:**
   - Context assembly fetches NPCs from `npcs_present` list
   - NPCs are included in LLM prompt with their personality, goals, knowledge
   - LLM generates NPC dialogue/actions based on context
   - NPCs act according to their role (ally helps, enemy hinders, mysterious is cryptic)
4. **NPCs persist across turns** until removed from scene or marked as dead/missing

---

## Architecture Decisions

### Why NPCs are Separate from Characters
- **Characters** = Player-controlled entities with full character sheets
- **NPCs** = Keeper/AI-controlled entities with narrative focus
- **AI-Controlled Characters** (M6) = Characters with AI personality (hybrid)

This separation allows:
- Lighter data model for NPCs (no skill sheets needed)
- Clearer Keeper vs Player boundaries
- Flexible role-based behavior

### NPCs Belong to Campaigns
- NPCs are scoped to campaigns (not realms) because narrative context is campaign-specific
- Same NPC can't appear in multiple campaigns (different instances if needed)
- Campaign deletion should cascade to NPCs (not yet implemented)

### Scene-Level NPC Tracking
- NPCs are added/removed from scenes dynamically
- This allows NPCs to "move" between scenes
- Status tracking ("dead", "missing") provides narrative flexibility

---

## Testing Recommendations

### Backend API Testing
```bash
# Create test campaign
CAMPAIGN_ID=$(curl -X POST http://localhost:8093/api/v1/campaigns -H "Content-Type: application/json" \
  -d '{"name":"Test Campaign","realm_id":"realm-test","status":"active","created_by":"test"}' | jq -r '.id')

# Create NPC
NPC_ID=$(curl -X POST http://localhost:8093/api/v1/npcs -H "Content-Type: application/json" \
  -d "{\"campaign_id\":\"$CAMPAIGN_ID\",\"name\":\"Test NPC\",\"description\":\"Mysterious figure\",\"role\":\"mysterious\",\"personality\":\"Cryptic\",\"created_by\":\"test\"}" | jq -r '.id')

# Create scene
SCENE_ID=$(curl -X POST http://localhost:8093/api/v1/scenes -H "Content-Type: application/json" \
  -d "{\"chapter_id\":\"chapter-test\",\"name\":\"Test Scene\",\"created_by\":\"test\"}" | jq -r '.id')

# Add NPC to scene
curl -X POST "http://localhost:8093/api/v1/npcs/scenes/$SCENE_ID/npcs/$NPC_ID"

# Verify NPC appears in context during turn processing
# (Would need to create a full turn to test LLM integration)
```

---

## Known Limitations

1. **No Frontend UI** - NPCs can only be managed via API currently
2. **No Cascade Delete** - Deleting a campaign doesn't delete its NPCs
3. **No NPC History** - NPC state changes aren't tracked in detail (future: status_history array)
4. **Fixed LLM Behavior** - NPCs always act when present; no "silent observer" mode
5. **No NPC-to-NPC Interaction** - LLM generates NPC actions relative to players, not other NPCs

---

## Future Enhancements

### Frontend UI (Priority)
- **NPC Manager Panel**: Create/edit/delete NPCs for a campaign
- **Scene NPC Controls**: Add/remove NPCs from current scene
- **NPC Status Cards**: Show NPCs present with quick status updates
- **NPC Templates**: Pre-made NPC archetypes (Scholar, Cultist, Detective, etc.)

### Advanced Features
- **NPC Relationships**: Track NPC opinions of characters/other NPCs
- **NPC State Machine**: More sophisticated status tracking (injured, frightened, suspicious, etc.)
- **NPC Triggers**: Auto-add NPCs to scenes based on conditions
- **NPC Voice**: Customize LLM tone/style per NPC (formal, gruff, mad, etc.)
- **NPC Inventory**: Track what items NPCs have/can give to players

---

## Files Modified

### New Files
- `backend/app/routes_npcs.py` - NPC CRUD routes

### Modified Files
- `backend/app/models.py` - NPC and Scene models
- `backend/main.py` - Router registration
- `backend/app/services/context_assembly.py` - NPC context fetching
- `n8n_workflows/LLM_Synthesizer_SubWF.json` - NPC prompt section
- `frontend/src/services/api.ts` - TypeScript interface

---

## Handoff Notes

### For Next Developer
- NPCs are stored in `entities` collection with `kind: "npc"`
- Scene tracking uses `npcs_present` array of NPC IDs
- LLM receives NPCs in `collected_data.npcs` field
- Frontend UI can be built using existing API patterns (see `routes_characters.py` as example)

### Integration with M6
- M6 added AI-controlled **characters** (PCs with AI personality)
- M7 added **NPCs** (Keeper-controlled narrative entities)
- Both appear in LLM prompts but serve different purposes:
  - AI Characters = Party members acting autonomously
  - NPCs = World inhabitants controlled by story logic

---

## Conclusion

M7 implementation provides a solid foundation for NPC management in the Call of Cthulhu system. The backend is fully functional and ready for frontend integration. NPCs will now naturally appear in gameplay narratives when present in scenes, adding depth and interactivity to the campaign world.

**Status:** ✅ **Backend Complete** | ⏳ **Frontend UI Pending**
