# Friction Points

> **Last Updated:** 2024-11-29  
> **Status:** Phase 1 - Observations Only  
> **Note:** These are observations, NOT recommendations. Solutions will be designed in Phase 2.

---

## 1. Dual MongoDB Write Paths

**Location:** `routes_turns.py` + `DungeonMaster_Main.json`

**Observation:** Both the backend AND n8n write to MongoDB independently.
- Backend creates the turn, updates status
- n8n writes the reaction directly to MongoDB
- Backend then reads the result back

**Why this is friction:**
- Race conditions possible
- No transactional guarantee
- State can desync if n8n write succeeds but response fails

---

## 2. n8n Handles Scene/Chapter Creation Logic

**Location:** `DungeonMaster_Main.json` nodes: "Need Scene Creation?", "Create Chapter", "Insert Scene to MongoDB"

**Observation:** The decision to create new scenes/chapters happens inside n8n, not the backend.

**Why this is friction:**
- Business logic split across systems
- Backend doesn't know scene creation is happening until after the fact
- Frontend must refetch to see new scenes

---

## 3. Context Assembly in n8n is Complex

**Location:** `DungeonMaster_Main.json` nodes: "Prepare Campaign Fetch", "Fetch Campaign", "Prepare Scene Fetch", "Fetch Scene", "Prepare Lore Query", "Fetch Lore", "Merge Collected Data"

**Observation:** n8n fetches campaign, scene, characters, and lore in separate nodes, then merges them.

**Why this is friction:**
- 7+ nodes just for data gathering
- n8n is doing what a backend service layer should do
- Duplicates logic that backend already has access to

---

## 4. Skill Check Detection in Workflow

**Location:** `DungeonMaster_Main.json` nodes: "Detect Skill Checks", "Parse Detected Skills", "Has Skill Checks?", "Match Skills to Characters", "Roll Skill Checks"

**Observation:** n8n parses player action text to detect skill mentions and rolls dice.

**Why this is friction:**
- Text parsing logic in a workflow is fragile
- Could be a backend service with proper validation
- Skill definitions are likely in MongoDB but fetched redundantly

---

## 5. No State Recovery if n8n Fails Mid-Workflow

**Location:** `routes_turns.py` lines 70-180

**Observation:** If n8n fails partway through (e.g., after creating a scene but before generating narrative), there's no rollback.

**Why this is friction:**
- Turn stuck in "processing" state
- Orphaned scene may exist
- No retry mechanism

---

## 6. Webhook Timeout Risk

**Location:** `routes_turns.py` line 89: `timeout=60.0`

**Observation:** Backend waits 60 seconds for n8n response. LLM generation can be slow.

**Why this is friction:**
- Frontend has no progress indication
- If timeout occurs, turn marked as "failed"
- No async/callback pattern

---

## 7. Socket.IO State is Ephemeral

**Location:** `socketio_manager.py` line 18: `active_sessions: Dict[str, Dict[str, str]] = {}`

**Observation:** Player presence is stored in Python memory, not persisted.

**Why this is friction:**
- Backend restart = all players appear offline
- No reconnection state
- Session must be "rejoined" manually

---

## 8. ActionDraft Lifecycle Unclear

**Location:** `routes_action_drafts.py`

**Observation:** ActionDrafts are temporary UI state, but there's no automatic cleanup trigger.

**Why this is friction:**
- `clear_session_drafts` exists but unclear when it's called
- Orphaned drafts may accumulate
- No TTL or automatic expiry

---

## 9. Prophet vs DungeonMaster Overlap

**Location:** `Prophet_Main.json` and `DungeonMaster_Main.json`

**Observation:** Both workflows fetch similar context (characters, scenes) and call LLM Synthesizer.

**Why this is friction:**
- Duplicated context-building logic
- Could share a common context service
- Different entry points for similar operations

---

## 10. Response Format Variance

**Location:** `routes_turns.py` lines 108-118

**Observation:** Backend tries multiple keys to extract n8n response: `output`, `body`, `text`, `response`, `description`

**Why this is friction:**
- n8n response format is inconsistent
- Defensive parsing required
- No contract/schema enforcement

---

## Summary Table

| # | Friction Point | Severity | Category |
|---|---------------|----------|----------|
| 1 | Dual MongoDB write paths | High | State sync |
| 2 | Scene/chapter creation in n8n | Medium | Logic split |
| 3 | Complex context assembly | Medium | Complexity |
| 4 | Skill check detection in workflow | Medium | Logic split |
| 5 | No state recovery on failure | High | Reliability |
| 6 | Webhook timeout risk | Medium | Reliability |
| 7 | Ephemeral Socket.IO state | Low | Reliability |
| 8 | ActionDraft lifecycle unclear | Low | Cleanup |
| 9 | Prophet/DungeonMaster overlap | Low | Duplication |
| 10 | Response format variance | Medium | Contract |

---

## Questions for Clarification

Before Phase 2, please clarify:

1. **Is the 60-second timeout acceptable?** Or should we move to async callbacks?
2. **Should scene/chapter creation remain AI-driven?** Or should backend control this?
3. **Is there a preference for where skill check logic lives?** (Backend service vs n8n vs LLM)
4. **What's the expected player count per session?** (Affects Socket.IO scaling)
