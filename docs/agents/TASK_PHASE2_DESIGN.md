# Task: Phase 2 - Design Hybrid Architecture for DungeonMaster Refactoring

## Setup
Read these files first (in order):
1. `AGENTS.md` — agent instructions and documentation update rules
2. `docs/agents/HANDOFF_CONTEXT.md` — current project state
3. `docs/architecture/FRICTION_POINTS.md` — problems to solve
4. `docs/architecture/DATA_FLOW.md` — current data flow

Then read the workflow to refactor:
- `n8n_workflows/DungeonMaster_Main.json`

---

## Context: Key Design Decisions (Already Made)

### Scene/Chapter Creation: Fully Automated
- **Scene** = storage container for turns, summarized for compact context
- **Scene transition** = triggered by turn reaction (location change, e.g., new room)
- **Chapter** = major scene changes with time gaps (city A → city B, building A → building B, major story beats)
- **Turn reaction** triggers new scene/chapter creation — no human confirmation needed
- **Campaign** provides story guidance (not yet implemented)

### Processing Model: Async
- Turn submission returns immediately with `turn_id`
- Backend processes asynchronously
- Frontend polls or receives webhook/socket callback when complete
- **Target latency:** Up to a few minutes acceptable (Ollama LLM calls)

---

## Your Task

**Goal:** Design a refactoring plan that:
1. Moves context assembly and MongoDB writes to FastAPI backend
2. Simplifies n8n to ONLY orchestrate LLM calls
3. Implements async turn processing with callback

### Activate Extended Thinking
This is a complex architecture task. Use extended/deep thinking mode.

---

## Phase 2A: Analysis

Map the current `DungeonMaster_Main.json` workflow:
1. List every node and its purpose
2. Categorize each node as:
   - **MOVE TO BACKEND** — context fetching, MongoDB writes, business logic
   - **KEEP IN N8N** — LLM orchestration, prompt building
   - **REMOVE** — redundant or overcomplicated

---

## Phase 2B: Design

Write to `docs/architecture/REFACTORING_PLAN.md`:

### 1. Current State
- Node-by-node breakdown of DungeonMaster workflow
- What each node does and why it's problematic

### 2. Target Architecture

```
Frontend
   │
   ▼ POST /turns/{id}/submit
Backend
   │
   ├─► Assemble context (campaign, scene, characters, lore)
   ├─► Detect skill checks (backend service or LLM call)
   ├─► Call n8n webhook with COMPLETE context bundle
   │
   ▼
n8n (simplified)
   │
   ├─► LLM call: Generate narrative
   ├─► LLM call: Detect scene/chapter transition (optional)
   │
   ▼ POST callback to backend
Backend
   │
   ├─► Write turn.reaction to MongoDB
   ├─► Create new scene/chapter if triggered
   ├─► Notify frontend via Socket.IO
   │
   ▼
Frontend receives update
```

### 3. New Backend Endpoints

Design these new endpoints:

| Endpoint | Purpose |
|----------|---------|
| `POST /turns/{id}/submit` | Start async processing, return immediately |
| `POST /internal/turns/{id}/complete` | Callback from n8n with LLM result |
| `GET /context/turn/{turn_id}` | Assemble full context bundle for n8n |

### 4. Simplified n8n Workflow

The new DungeonMaster workflow should have ~5-8 nodes max:
1. Webhook receive
2. (Optional) Pre-process/validate
3. LLM call: Generate narrative
4. (Optional) LLM call: Detect transitions
5. Callback to backend

### 5. Context Bundle Schema

Define what the backend sends to n8n:

```json
{
  "turn_id": "turn-xxx",
  "callback_url": "http://backend:8000/internal/turns/turn-xxx/complete",
  "context": {
    "campaign": { "name": "...", "story_arc": "...", "setting": "..." },
    "chapter": { "name": "...", "summary": "..." },
    "scene": { "name": "...", "summary": "...", "location": "..." },
    "previous_turns": [ /* last N turns with summaries */ ],
    "characters": [ /* involved characters with stats */ ],
    "lore": [ /* RAG results from Qdrant */ ],
    "skill_checks": [ /* pre-rolled results if any */ ]
  },
  "actions": [ /* player actions for this turn */ ]
}
```

### 6. Scene/Chapter Transition Logic

Define when transitions occur:
- **New Scene:** Location change, significant time skip, dramatic event
- **New Chapter:** Major location change (city/building), long time gap, story milestone

Who decides? Options:
- A) LLM detects in narrative and returns `{ "transition": "scene" | "chapter" | null }`
- B) Backend detects keywords in LLM response
- C) Separate LLM call for transition detection

Recommend one approach.

### 7. Migration Steps

Ordered implementation plan:
1. Create backend context assembly service
2. Create callback endpoint
3. Modify turn submission to async
4. Simplify n8n workflow
5. Add Socket.IO notifications
6. Test end-to-end
7. Remove old n8n nodes

### 8. Risk Assessment

What could break? How to mitigate?

---

## Deliverables

1. **`docs/architecture/REFACTORING_PLAN.md`** — Full design document
2. **`docs/decisions/ADR-001-hybrid-architecture.md`** — Decision record for async + backend-owns-writes
3. **Update `docs/agents/HANDOFF_CONTEXT.md`** — Summary of what you designed

---

## Constraints

- ✅ Backend owns ALL MongoDB writes
- ✅ Backend assembles ALL context
- ✅ n8n only does LLM orchestration
- ✅ Async processing with callback
- ✅ Scene/chapter creation is automated (no confirmation)
- ❌ Don't implement code yet — design only
- ❌ Don't modify existing files except docs

---

## Begin

1. Read the files listed above
2. Analyze DungeonMaster_Main.json
3. Ask any clarifying questions
4. Then write the design documents
