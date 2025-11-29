# Agent Handoff Context

> **Purpose:** Quick briefing for AI agents to continue work
> **Last Updated:** 2025-11-29 19:25 UTC
> **Last Agent:** GitHub Copilot
> **Session:** Phase 4 Milestones M1-M5+M8 COMPLETE
> **Word Limit:** ~500 words

---

## Active Task

**📋 Current Task:** Phase 4 - Remaining: M6, M7
**Status:** ✅ M1, M2, M3, M4, M5, M8, M8b COMPLETE | 🟡 M6, M7 NOT STARTED
**Document:** `docs/agents/TASK_PHASE4_COMPLETE.md`
**Commits:**
- `5476c01` - M1+M3+M8 implementation
- `16481fa` - M4+M5+M8b (LLM summarization + markdown)
- `396854c` - M2 (Campaign milestones)

---

## Completed This Session

### M1: Realm/Campaign Settings ✅
- Added `RealmContext` to `context_assembly.py` with `setting.tone`, `setting.notes`
- `CampaignContext` now passes full `setting` dict (tone, goal, key_elements, story_elements)
- `DungeonMaster_Main.json` updated to include realm in `collected_data`
- `LLM_Synthesizer_SubWF.json` prompt now has REALM CONTEXT, CHAPTER CONTEXT, CURRENT SCENE sections

### M2: Campaign Milestones ✅
- Extended `CampaignCreate` model with `setting` dict and `generate_milestones` flag
- Added `milestones: List[str]` to `StoryArc` model
- Campaign creation route generates milestones via `LLMService` when requested
- Uses campaign tone, goal, story_elements for contextual milestone generation

### M3: Keeper Context Window ✅
- Previous turns already included in context (was done in Phase 3)
- Scene summary, chapter summary passed to LLM prompt
- Enhanced prompt building with full narrative hierarchy

### M4: Scene Summarization ✅
- Created `backend/app/services/llm.py` - Direct Ollama LLM service
- `summarize_scene()` generates markdown summary from turn history
- Called by transition service when scene closes

### M5: Chapter Summarization ✅
- `summarize_chapter()` generates markdown summary from scene summaries
- Called by transition service when chapter closes

### M8: Frontend Bug Fixes ✅
- **CharacterSheet close bug:** Autosave no longer triggers close (added `isAutosave` param)
- **CombatSection collapse:** Fixed v-for key that included `weapon.name` (caused re-render on type)
- **RelationshipsSection collapse:** Fixed v-for key that included `rel.object`

### M8b: Markdown Rendering ✅
- Installed `marked` package in frontend
- Created `frontend/src/composables/useMarkdown.ts` with XSS sanitization
- `SceneProgress.vue` renders narrative with v-html

---

## Known Issues (Remaining Phase 4)

1. ~~Keeper lacks context~~ ✅ FIXED - Now has realm/campaign/chapter/scene/previous turns
2. **No NPC support** - M6, M7 not started (Claude Code recommended)
3. ~~Frontend bugs~~ ✅ FIXED - All three bugs resolved

## New Files Created

- `backend/app/services/llm.py` - Direct LLM service for summarization/generation
- `frontend/src/composables/useMarkdown.ts` - Markdown parser utility

---

## First: Read the Instructions

**Before doing anything, read `/AGENTS.md`** — it contains:
- Documentation update rules
- Common commands
- Code style guidelines
- Handoff checklist

---

## What This Project Is

**Call of Cthulhu RPG Campaign Manager** - A web app for running tabletop RPG sessions with AI-powered narrative generation. Players submit actions, an AI "Keeper" generates story responses.

## Current Architecture (3 Layers)

1. **FastAPI Backend** (`backend/app/`)
   - Owns all entity CRUD (World → Realm → Campaign → Chapter → Scene → Turn)
   - MongoDB for persistence (Motor async driver)
   - Socket.IO for real-time player presence
   - Calls n8n webhooks for AI processing

2. **n8n Workflows** (`n8n_workflows/`)
   - `DungeonMaster_Main.json` - 6-node workflow (simplified)
   - `LLM_Synthesizer_SubWF.json` - Builds prompts, calls Ollama
   - `Prophet_Main.json` - Q&A assistant for rules/lore

3. **Vue Frontend** (`frontend/`) - Has bugs to fix

## The Problem

n8n workflows are doing too much:
- Complex context assembly (fetching campaign, scene, characters, lore)
- Business logic (scene/chapter creation decisions)
- Direct MongoDB writes (bypassing backend)
- Skill check detection and dice rolling

This creates:
- State sync issues (backend and n8n both write to MongoDB)
- No failure recovery (if n8n fails mid-workflow)
- Hard-to-maintain workflow complexity

## Key Files to Understand

| Priority | File | Why |
|----------|------|-----|
| 1 | `routes_turns.py` | The handoff point: backend → n8n |
| 2 | `DungeonMaster_Main.json` | The complex workflow to simplify |
| 3 | `models.py` | All entity definitions |
| 4 | `socketio_manager.py` | Real-time layer |

## Phase 2 Goal

Design a **hybrid architecture** where:
- Backend owns ALL state changes (MongoDB writes)
- Backend provides a "context bundle" API for n8n
- n8n focuses ONLY on LLM orchestration
- Skill checks, scene creation → backend services

## Friction Points (Top 3)

1. **Dual MongoDB writes** - Both backend and n8n write independently
2. **Scene/chapter creation in n8n** - Should be backend business logic
3. **Complex context assembly in n8n** - 7+ nodes doing what one backend endpoint could do

## How to Continue

1. Read `docs/architecture/ARCHITECTURE_OVERVIEW.md` for full details
2. Read `docs/architecture/FRICTION_POINTS.md` for all identified issues
3. Phase 2 will produce `docs/architecture/REFACTORING_PLAN.md`

## Commands to Run

```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Full stack (Docker)
docker-compose up
```

## What Was Completed

### Phase 3 Step 3 REDO: LLM Synthesizer Enhancement ✅ (Just Completed)

Created `LLM_Synthesizer_SubWF_v2.json` with transition detection capability.

**Reason:** Original Step 3 changes were lost/corrupted - file had JSON syntax error

**What Was Created:**
- ✅ `LLM_Synthesizer_SubWF_v2.json` (173 lines, +66 from original)
- ✅ Enhanced DungeonMaster system prompt with transition detection rules
- ✅ Added JSON mode to Ollama call for dungeonmaster agent
- ✅ Enhanced Extract Answer node to parse structured JSON output
- ✅ Graceful fallback if JSON parsing fails
- ✅ Validated with `python3 -m json.tool` - PASSES

**Key Enhancements:**
1. **Transition Detection Rules:**
   - NEW SCENE: Location change within building, time skip <1 day, dramatic event
   - NEW CHAPTER: Major location change, time skip >1 day, story milestone
   - NO TRANSITION: Same location/timeframe, dialogue, combat in progress

2. **Structured Output:**
   ```json
   {
     "narrative": "...",
     "summary": "...",
     "transition": {
       "type": "scene/chapter/none",
       "reason": "...",
       "suggested_name": "...",
       "suggested_description": "..."
     },
     "requires_input": false,
     "interaction_type": "DISCOVERY"
   }
   ```

3. **Backward Compatibility:**
   - Prophet agent unchanged (simple Q&A format)
   - Only dungeonmaster agent uses JSON mode

**Report:** `docs/agents/reports/REPORT_PHASE3_STEP3_REDO.md`

---

### Phase 3 Step 5: End-to-End Integration Testing ✅ UNBLOCKED

Testing framework created. Ready for manual execution with v2 workflows.

**Status:** Blocker removed - LLM_Synthesizer_SubWF_v2.json created and validated

**What Was Done:**
- ✅ Code review of backend async implementation (routes_turns.py)
- ✅ Validation of DungeonMaster_Main_v2.json (valid JSON)
- ✅ Validation of LLM_Synthesizer_SubWF_v2.json (valid JSON) - FIXED
- ✅ Created comprehensive testing framework and manual test protocol
- ✅ Identified implementation gaps and recommendations

**Tests Ready for Execution (manual):**
- Test 1: Backend mock callback
- Test 2: n8n workflow import (v2 workflows)
- Test 3: n8n webhook test
- Test 4: Full E2E flow
- Test 5: Scene transition detection
- Tests 6-8: Optional tests

**Manual Testing Protocol:**
- 6-phase testing approach (~3.5 hours)
- Infrastructure validation → Import v2 workflows → Backend testing → E2E testing
- Complete debug commands and environment checklist

**Implementation Status:**
- Backend: ✅ Excellent - async callback pattern well-implemented
- DungeonMaster_Main_v2: ✅ Valid JSON, ready to import
- LLM_Synthesizer_SubWF_v2: ✅ Valid JSON, ready to import

**Reports:**
- `docs/agents/reports/REPORT_PHASE3_STEP5.md` (testing framework)
- `docs/agents/reports/REPORT_PHASE3_STEP3_REDO.md` (blocker resolution)

**Next Action:** Import v2 workflows to n8n, execute manual testing protocol

---

### Phase 3 Step 4: DungeonMaster v2 Workflow ✅

Created simplified DungeonMaster Main v2 workflow (82% node reduction).

**File Created:**
- **DungeonMaster_Main_v2.json** (6 nodes, down from 34)
  - Webhook: `/coc_dungeonmaster_v2`
  - Workflow: Receive context bundle → Validate → Prepare LLM input → Call LLM Synthesizer SubWF → Format callback → POST to backend
  - Async callback pattern (no 60s blocking)
  - Pure LLM orchestration (no MongoDB writes)

**What Was Removed:**
- Scene/chapter creation (6 nodes) → Backend TransitionService
- Turn creation (3 nodes) → Turn exists before n8n called
- Skill check logic (8 nodes) → Backend SkillCheckService
- Context assembly (7 nodes) → Backend ContextAssemblyService
- MongoDB writes (3 nodes) → Backend owns all writes
- Context preservation (9 nodes) → Not needed with upfront context

**Integration:**
- Input: Pre-assembled context bundle from backend
- Output: Callback to `POST /api/v1/internal/turns/{turn_id}/complete`
- LLM: Uses enhanced LLM Synthesizer from Step 3

**Documentation:**
- Updated `n8n_workflows/README.md` with v2 description and tests
- Marked v1 as "Legacy - 34 nodes"
- Added backend environment variable configuration

**Report:** `docs/agents/reports/REPORT_PHASE3_STEP4.md`

---

### Phase 3 Step 3: LLM Synthesizer Enhancement ✅

Enhanced the LLM Synthesizer n8n sub-workflow for transition detection.

**File Modified:**
- **LLM_Synthesizer_SubWF.json** (~120 lines changed)
  - Enhanced dungeonmaster system prompt with transition detection rules
  - Added JSON mode for dungeonmaster agent (`format: 'json'`)
  - Implemented structured JSON parsing in Extract Answer node
  - Added graceful fallback for malformed JSON responses

**Transition Detection:**
- NEW SCENE: Location change within building, time skip < 1 day, dramatic event, discovery
- NEW CHAPTER: Major location change, time skip > 1 day, story milestone, tone shift
- NO TRANSITION: Continuing in same location/timeframe, dialogue, combat in progress

**Output Schema (DungeonMaster):**
```json
{
  "narrative": "...",
  "summary": "...",
  "transition": {
    "type": "scene OR chapter OR none",
    "reason": "...",
    "suggested_name": "...",
    "suggested_description": "..."
  },
  "requires_input": true/false,
  "interaction_type": "CHOICE|COMBAT|QUESTION|DISCOVERY|NONE"
}
```

**Documentation:**
- Updated `n8n_workflows/README.md` with schema and test examples
- Maintained backward compatibility with Prophet agent

**Report:** `docs/agents/reports/REPORT_PHASE3_STEP3.md`

---

### Phase 3 Step 2: Backend Endpoints ✅

Modified backend to add async turn processing with callback pattern.

**Files Modified:**
1. **routes_turns.py** (~400 lines added)
   - Modified `submit_turn()` endpoint with feature flag routing
   - Created `submit_turn_async()` - async turn submission (returns 202)
   - Created `complete_turn_callback()` - n8n callback handler
   - Created `get_turn_status()` - status polling endpoint
   - Integrated all three services from Step 1
   - Fire-and-forget webhook call to n8n

2. **socketio_manager.py** (~70 lines added)
   - `emit_turn_processing()` - Turn submitted event
   - `emit_turn_completed()` - Turn done event
   - `emit_turn_failed()` - Error event
   - `emit_scene_created()` - New scene event
   - `emit_chapter_created()` - New chapter event

**New Endpoints:**
- `POST /api/v1/turns/{turn_id}/submit` - Async submit (202 Accepted)
- `POST /api/v1/internal/turns/{turn_id}/complete` - n8n callback
- `GET /api/v1/turns/{turn_id}/status` - Status polling

**Architecture:**
- Backend returns 202 immediately (no 60s blocking)
- n8n calls back when LLM processing completes
- Socket.IO events notify frontend in real-time
- Feature flag `USE_ASYNC_TURN_PROCESSING` for gradual rollout

**Report:** `docs/agents/reports/REPORT_PHASE3_STEP2.md`

---

### Phase 3 Step 1: Backend Services ✅

Created three new backend services in `backend/app/services/`:

1. **context_assembly.py** (487 lines)
   - `ContextAssemblyService` class with `assemble_context()` method
   - Pydantic models matching REFACTORING_PLAN.md Section 5 schema
   - Fetches campaign, chapter, scene, previous turns, characters
   - Placeholder for Qdrant RAG integration
   - Size-limited context: max 5 previous turns, 10 characters, 3 lore chunks

2. **skill_check.py** (365 lines)
   - `SkillCheckService` class with regex-based skill detection
   - Keyword matching for 30+ Call of Cthulhu 7e skills
   - CoC 7e dice mechanics: d100 rolls with success levels
   - Success levels: Critical, Extreme, Hard, Regular, Failure, Fumble
   - Difficulty detection from action text (Regular, Hard, Extreme)

3. **transition.py** (369 lines)
   - `TransitionService` class for scene/chapter creation
   - `parse_transition_from_llm()` - extracts transition from LLM response
   - `process_transition()` - creates new scenes/chapters
   - Automated scene closing with summaries
   - Carries over participants to new scenes

4. **config.py** (58 lines)
   - Feature flag: `USE_ASYNC_TURN_PROCESSING` (default: False)
   - Environment-based configuration
   - Context assembly limits (turns, characters, lore chunks)
   - Service URLs (n8n webhooks, backend callbacks)

5. **services/__init__.py** (20 lines)
   - Exports all services and models

**Files Created:**
- ✅ `backend/app/services/__init__.py`
- ✅ `backend/app/services/context_assembly.py`
- ✅ `backend/app/services/skill_check.py`
- ✅ `backend/app/services/transition.py`
- ✅ `backend/app/config.py`

**Code Quality:**
- All services use async/await for MongoDB operations
- Pydantic models with type hints
- Comprehensive logging with `logging.getLogger(__name__)`
- Error handling with meaningful messages
- Follows existing backend code patterns

---

### Phase 2A: Analysis ✅
- Analyzed all 34 nodes in `DungeonMaster_Main.json`
- Categorized nodes: 22 MOVE, 7 KEEP, 9 REMOVE
- Identified 6 critical architectural issues
- Documented in `REFACTORING_PLAN.md` (Current State section)

### Phase 2B: Design ✅
- Designed async callback architecture (backend → n8n → backend callback)
- Defined 3 new backend endpoints (submit, callback, status)
- Simplified n8n workflow to 5-6 nodes (down from 34)
- Created context bundle schema (15-30 KB payload)
- Chose LLM-driven scene/chapter transitions
- Wrote 8-step migration plan (10-15 dev days)
- Risk assessment: 8 risks identified, all mitigated

### Phase 2C: Documentation ✅
- Created `ADR-001-hybrid-architecture.md` with decision rationale
- Updated `HANDOFF_CONTEXT.md` (this file)

## Key Files Created/Modified

| File | Type | Content |
|------|------|---------|
| `docs/architecture/REFACTORING_PLAN.md` | Design | Complete architecture design (Sections 1-8) |
| `docs/decisions/ADR-001-hybrid-architecture.md` | ADR | Decision record for hybrid architecture |
| `docs/agents/HANDOFF_CONTEXT.md` | Handoff | Updated with Phase 2 summary |

## Key Design Decisions

1. **Async Callback Pattern:** Backend returns immediately, n8n calls back when done
2. **Backend Owns ALL Writes:** MongoDB writes ONLY happen in backend
3. **Backend Assembles Context:** n8n receives pre-assembled context bundle
4. **LLM-Driven Transitions:** Scene/chapter detection in narrative generation (Option A)
5. **5-6 Node Workflow:** Simplified n8n to just LLM orchestration

## Architecture Summary

**Before (Current):**
```
Frontend → Backend (blocks 60s) → n8n (34 nodes: data fetch, logic, writes, LLM) → Backend → Frontend
```

**After (Target):**
```
Frontend → Backend (returns in 100ms) → n8n (6 nodes: LLM only) → Backend callback → Socket.IO → Frontend
```

**What Moves to Backend:**
- Context assembly (campaign, scene, characters, lore)
- Skill check detection and rolling
- Scene/chapter creation
- ALL MongoDB writes

**What Stays in n8n:**
- LLM narrative generation
- Transition detection (enhanced prompt)
- Callback to backend

## Next Steps (Phase 3 - Implementation)

Follow the migration plan in `REFACTORING_PLAN.md` Section 7:

1. **Start Here:** Step 1 - Create backend services
   - `backend/app/services/context_assembly.py`
   - `backend/app/services/skill_check.py`
   - `backend/app/services/transition.py`

2. **Then:** Step 2 - Create new backend endpoints
   - `POST /api/v1/turns/{turn_id}/submit`
   - `POST /api/v1/internal/turns/{turn_id}/complete`
   - Add Socket.IO events

3. **Important:** Use feature flag `USE_ASYNC_TURN_PROCESSING` for gradual rollout

4. **Testing Strategy:** Build new system alongside old, validate with 10% traffic

## Questions Answered

✅ **Is 60-second webhook timeout acceptable?**
→ No. Moving to async callback pattern (no timeout)

✅ **Should scene creation remain AI-driven?**
→ Yes. LLM detects transitions during narrative generation

✅ **Where should skill check logic live?**
→ Backend service (SkillCheckService), with regex/keyword matching initially