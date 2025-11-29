# Agent Handoff Context

> **Purpose:** Quick briefing for AI agents to continue work
> **Last Updated:** 2025-11-29
> **Last Agent:** Claude Code
> **Session:** Phase 3 Step 1 Complete - Backend Services Created
> **Word Limit:** ~500 words

---

## Active Task

**📋 Current Task:** Phase 3 Step 2 - Backend Endpoints (Ready to Start)
**Status:** Step 1 complete, paused for review before Step 2
**Goal:** Create new async turn submission and callback endpoints

---

## First: Read the Instructions

**Before doing anything, read `/AGENTS.md`** — it contains:
- Documentation update rules
- Common commands
- Code style guidelines
- Handoff checklist

---

## What This Project Is

**Call of Cthulhu RPG Campaign Manager** - A web app for running tabletop RPG sessions with AI-powered narrative generation. Players submit actions, an AI "Dungeon Master" generates story responses.

## Current Architecture (3 Layers)

1. **FastAPI Backend** (`backend/app/`)
   - Owns all entity CRUD (World → Realm → Campaign → Chapter → Scene → Turn)
   - MongoDB for persistence (Motor async driver)
   - Socket.IO for real-time player presence
   - Calls n8n webhooks for AI processing

2. **n8n Workflows** (`n8n_workflows/`)
   - `DungeonMaster_Main.json` - Processes player turns, generates narrative
   - `Prophet_Main.json` - Q&A assistant for rules/lore
   - Sub-workflows: Dice rolling, MongoDB queries, RAG (Qdrant), LLM calls (Ollama)

3. **Vue Frontend** (`frontend/`) - Out of scope for this refactor

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

### Phase 3 Step 1: Backend Services ✅ (Just Completed)

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