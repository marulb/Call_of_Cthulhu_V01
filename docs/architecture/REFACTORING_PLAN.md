# Refactoring Plan: DungeonMaster Hybrid Architecture

> **Last Updated:** 2025-11-29
> **Status:** Phase 2A Complete - Analysis Only
> **Next Phase:** Phase 2B - Design Target Architecture

---

## Current State

### Overview

The `DungeonMaster_Main.json` workflow currently handles the entire turn processing lifecycle, from receiving player actions to generating narrative and writing results to MongoDB. It contains **34 nodes** performing tasks that span business logic, data fetching, LLM orchestration, and database writes.

**Fundamental Problem:** n8n is acting as both an orchestration layer AND a business logic layer, creating tight coupling and state synchronization issues.

### Node-by-Node Analysis

The workflow can be broken down into 7 functional phases:

#### Phase 1: Input & Initialization (Nodes 1-2)

| Node | Purpose | Category | Reasoning |
|------|---------|----------|-----------|
| **Webhook - DungeonMaster** | Receives POST request with player actions | **KEEP** | Entry point - n8n needs this to receive calls |
| **Parse Actions** | Extracts player actions, validates required fields, initializes workflow state | **MOVE** | Business logic validation should be in backend before calling n8n |

**Problems:**
- Validation happens AFTER the webhook is called, not before
- No way to return validation errors to frontend cleanly
- Initializes complex state (`collected_data`, `references`, `skill_checks`) that gets passed through entire workflow

---

#### Phase 2: Scene/Chapter Creation (Nodes 3-9)

| Node | Purpose | Category | Reasoning |
|------|---------|----------|-----------|
| **Need Scene Creation?** | Checks if `scene_id` is null | **REMOVE** | Backend should know this before calling n8n |
| **Prepare Chapter + Scene** | Generates IDs, builds chapter/scene documents | **MOVE** | Business logic for entity creation belongs in backend |
| **Create Chapter** | MongoDB insert for chapter | **MOVE** | Backend should own ALL MongoDB writes |
| **Merge Chapter Result** | Preserves context after chapter creation | **REMOVE** | Artifact of complex data passing pattern |
| **Prepare Scene Data** | Restores scene data from preserved context | **REMOVE** | Artifact of complex data passing pattern |
| **Insert Scene to MongoDB** | MongoDB insert for scene | **MOVE** | Backend should own ALL MongoDB writes |
| **Scene Created** | Restores original context after scene creation | **REMOVE** | Artifact of complex data passing pattern |
| **Use Existing Scene** | Pass-through node for existing scene path | **REMOVE** | Not needed if backend handles scene creation |

**Problems:**
- **6 nodes** just to create a chapter and scene
- Business logic decision ("should I create a scene?") happens in n8n
- MongoDB writes bypass backend entirely
- Complex context preservation pattern (`_original_context`, `_scene_data`) needed because data flows linearly through nodes
- Backend doesn't know new scenes exist until it queries MongoDB again
- No transactional guarantee - chapter could be created but scene could fail

---

#### Phase 3: Turn Creation (Nodes 10-11)

| Node | Purpose | Category | Reasoning |
|------|---------|----------|-----------|
| **Prepare Turn** | Generates turn ID, flattens turn document for MongoDB | **MOVE** | Turn should already exist before n8n is called |
| **Create Turn** | MongoDB insert for turn | **MOVE** | Backend should create the turn before calling n8n |
| **Turn Created** | Restores context after turn creation | **REMOVE** | Not needed if backend creates turn first |

**Problems:**
- Turn is created by n8n, but backend expects to own turn lifecycle
- Another context preservation pattern
- If workflow fails after this point, orphaned turn exists in "processing" state

---

#### Phase 4: Skill Check Processing (Nodes 12-17)

| Node | Purpose | Category | Reasoning |
|------|---------|----------|-----------|
| **Detect Skill Checks** | LLM call to analyze actions for skill check keywords | **MOVE/KEEP** | Could be backend service OR simplified LLM call |
| **Parse Detected Skills** | Parses JSON from LLM response | **MOVE/KEEP** | Depends on where skill detection lives |
| **Has Skill Checks?** | Branches workflow based on detection result | **REMOVE** | Not needed if backend pre-processes this |
| **Prepare Character Fetch** | Builds MongoDB query for characters | **MOVE** | Backend already has access to character data |
| **Fetch Characters** | Calls MongoDB Query SubWF | **MOVE** | Backend should assemble context |
| **Match Skills to Characters** | Joins detected skills with character stats | **MOVE** | Business logic - belongs in backend service |
| **Roll Skill Checks** | Calls Dice Roller SubWF | **MOVE** | Could be backend service with dice rolling library |
| **No Skill Checks Path** | Pass-through for no-checks branch | **REMOVE** | Not needed if backend pre-processes |

**Problems:**
- **8 nodes** for skill check logic
- Text parsing and matching logic in n8n is fragile
- Could be a reusable backend service: `SkillCheckService.detect_and_roll(actions, characters)`
- Branching adds complexity - parallel paths need to merge later
- LLM call for skill detection adds latency and cost (could use regex/keyword matching)

---

#### Phase 5: Context Assembly (Nodes 18-23)

| Node | Purpose | Category | Reasoning |
|------|---------|----------|-----------|
| **Prepare Campaign Fetch** | Builds MongoDB query for campaign | **MOVE** | Backend should assemble context |
| **Fetch Campaign** | Calls MongoDB Query SubWF | **MOVE** | Backend already has access to this data |
| **Prepare Scene Fetch** | Builds MongoDB query for scene | **MOVE** | Backend should assemble context |
| **Fetch Scene** | Calls MongoDB Query SubWF | **MOVE** | Backend already has access to this data |
| **Prepare Lore Query** | Builds Qdrant query from action text | **MOVE** | Backend should handle RAG queries |
| **Fetch Lore** | Calls Qdrant RAG SubWF | **MOVE** | Backend should handle RAG queries |
| **Merge Collected Data** | Combines all fetched data into single context object | **MOVE** | Backend should provide pre-assembled context bundle |

**Problems:**
- **7 nodes** just to gather context data
- n8n is calling sub-workflows to query MongoDB - duplicates backend's data access layer
- Each fetch requires a prepare node (boilerplate)
- Merge logic is complex and error-prone
- Backend ALREADY has this data or can fetch it efficiently
- No caching - refetches same campaign/scene data on every turn

---

#### Phase 6: LLM Generation (Nodes 24-26)

| Node | Purpose | Category | Reasoning |
|------|---------|----------|-----------|
| **Prepare LLM Input** | Formats context for LLM Synthesizer SubWF | **KEEP** | LLM orchestration is n8n's purpose |
| **Generate Scene Narrative** | Calls LLM Synthesizer SubWF (Ollama) | **KEEP** | Core LLM call - this is what n8n SHOULD do |
| **Restore After LLM** | Restores context after LLM call | **REMOVE** | Artifact of context preservation pattern |

**Problems:**
- Only **1 node** (Generate Scene Narrative) is actually doing the core job
- Preparation and restoration nodes are boilerplate
- If backend provided proper context bundle, preparation could be simpler

---

#### Phase 7: Post-Processing & Response (Nodes 27-34)

| Node | Purpose | Category | Reasoning |
|------|---------|----------|-----------|
| **Detect Interaction Needed** | LLM call to determine if narrative requires player input | **KEEP** | Valid LLM orchestration task |
| **Parse Interaction** | Parses interaction detection JSON | **KEEP** | Goes with detection node |
| **Prepare MongoDB Update** | Formats turn.reaction for database write | **MOVE** | Backend should handle data formatting |
| **Write Turn Reaction** | MongoDB update to turn document | **MOVE** | Backend should own ALL writes |
| **Restore Context** | Restores data for response formatting | **REMOVE** | Artifact of context preservation |
| **Format Response** | Builds final JSON response for webhook | **KEEP** | n8n needs to return result to backend |
| **Respond to Webhook** | Sends HTTP response back to backend | **KEEP** | Required to close webhook call |

**Problems:**
- MongoDB write bypasses backend
- No callback pattern - response must be synchronous
- If write fails, backend doesn't know
- Backend has to query MongoDB again to see the reaction

---

### Categorization Summary

| Category | Count | Nodes |
|----------|-------|-------|
| **MOVE TO BACKEND** | 22 | Business logic, data fetching, MongoDB writes, skill checks |
| **KEEP IN N8N** | 7 | Webhook handling, LLM calls, response formatting |
| **REMOVE** | 9 | Context preservation boilerplate, redundant branches |

**Total nodes:** 34 → **Target: 5-8 nodes**

---

### Critical Issues Identified

#### 1. State Synchronization Problems

**Issue:** Backend and n8n both write to MongoDB independently.

**Example Flow:**
1. Backend creates turn with `status: "processing"`
2. n8n creates chapter/scene (backend doesn't know)
3. n8n writes `turn.reaction` (backend doesn't know)
4. Backend receives response, updates `status: "completed"`
5. Backend has to query MongoDB to see what n8n wrote

**Risk:** If n8n write succeeds but HTTP response fails, backend thinks turn failed but reaction exists in database.

---

#### 2. No Transaction Guarantees

**Issue:** Scene/chapter/turn creation happens in sequence with no rollback.

**Failure Scenario:**
- Chapter created successfully
- Scene insert fails
- Chapter is orphaned
- Turn is never created
- Frontend gets generic error

**No recovery mechanism** - manual database cleanup required.

---

#### 3. Business Logic in Workflow

**Issue:** Decisions about WHAT to do (create scene, detect skills) happen in n8n, not backend.

**Examples:**
- "Should I create a new scene?" - n8n decides
- "Does this action need a skill check?" - n8n decides
- "What skill checks should I roll?" - n8n decides

**Problem:** Backend can't enforce business rules, audit decisions, or change logic without modifying n8n workflow.

---

#### 4. Context Assembly Complexity

**Issue:** 7 nodes + 3 sub-workflow calls just to gather data.

**What n8n fetches:**
- Campaign (MongoDB Query SubWF)
- Scene (MongoDB Query SubWF)
- Characters (MongoDB Query SubWF)
- Lore chunks (Qdrant RAG SubWF)
- Dice rolls (Dice Roller SubWF)

**Backend already has access to:**
- MongoDB (Motor driver)
- Qdrant (existing integration)
- Business logic layer

**Duplication:** n8n reimplements backend's data access layer in workflows.

---

#### 5. Context Preservation Pattern

**Issue:** 9 nodes exist ONLY to preserve and restore context as data flows linearly.

**Pattern:**
```javascript
// Prepare node
return [{ json: { ...data, _original_context: $json } }];

// Restore node
const original = $('Previous Node').first().json._original_context;
return [{ json: original }];
```

**Why this exists:** n8n nodes can't easily access arbitrary previous nodes' data, so context must be manually carried forward.

**Solution:** If backend provides complete context bundle upfront, this pattern disappears.

---

#### 6. No Async Processing

**Issue:** Backend waits 60 seconds for synchronous HTTP response.

**Current:**
```
Frontend → Backend (blocks) → n8n (blocks) → LLM (slow) → n8n → Backend → Frontend
```

**Timeout scenarios:**
- LLM generation takes > 60s
- Multiple skill checks slow down workflow
- Qdrant query is slow

**User experience:** Frontend shows loading spinner for up to 60 seconds with no progress indication.

---

### Why This Matters

The current architecture makes it **impossible** to:

1. Implement proper error handling and recovery
2. Add caching or optimization without modifying workflows
3. Change business logic without redeploying n8n
4. Audit or trace decision-making
5. Test turn processing without running full n8n stack
6. Scale horizontally (n8n becomes bottleneck)
7. Provide real-time progress updates to users

**Next Phase (2B):** Design target architecture that solves these issues by moving backend-appropriate logic out of n8n.

---

## 2. Target Architecture

### High-Level Flow

```
Frontend (Vue)
   │
   │ POST /api/v1/turns/{turn_id}/submit
   │ Response: { "turn_id": "...", "status": "processing" }
   │ (returns immediately)
   │
   ▼
Backend (FastAPI)
   │
   ├─► Validate turn is ready for submission
   ├─► Update turn.status = "processing"
   ├─► Assemble context bundle:
   │   ├─► Fetch campaign (MongoDB)
   │   ├─► Fetch chapter + scene (MongoDB)
   │   ├─► Fetch characters (MongoDB)
   │   ├─► Detect skill checks (SkillCheckService)
   │   ├─► Roll dice for detected checks (DiceRollerService)
   │   └─► Fetch lore (Qdrant RAG)
   │
   ├─► POST to n8n webhook (fire-and-forget)
   │   Payload: { turn_id, callback_url, context, actions }
   │
   └─► Return to frontend immediately

   ... (minutes pass, LLM processing) ...

n8n (Simplified DungeonMaster)
   │
   ├─► Receive context bundle
   ├─► Generate narrative (LLM call via Ollama)
   ├─► Detect scene/chapter transition (included in LLM response)
   │
   └─► POST to backend callback URL
       Payload: { turn_id, narrative, transition, metadata }

Backend (Callback Handler)
   │
   ├─► Receive LLM results
   ├─► Write turn.reaction to MongoDB
   ├─► Process transition if detected:
   │   ├─► Create new scene (if transition.type === "scene")
   │   └─► Create new chapter + scene (if transition.type === "chapter")
   │
   ├─► Update turn.status = "completed"
   ├─► Emit Socket.IO event: "turn_completed"
   │
   └─► Return 200 OK to n8n

Frontend (Socket.IO listener)
   │
   └─► Receive "turn_completed" event
       └─► Refresh turn display, show narrative
```

### Key Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| **Async callback pattern** | Allows frontend to remain responsive, supports long-running LLM calls (up to several minutes) |
| **Backend assembles context** | Single source of truth, eliminates duplication, enables caching |
| **Backend owns ALL writes** | Prevents state sync issues, enables transactions, allows auditing |
| **n8n only does LLM calls** | Simplifies workflows, makes them maintainable, focuses on core competency |
| **Scene/chapter creation automated** | LLM detects transitions during narrative generation, no user confirmation needed |
| **Socket.IO for notifications** | Real-time updates to all players in session without polling |

### What Changes

| Before (Current) | After (Target) |
|------------------|----------------|
| Backend waits 60s for n8n response | Backend returns immediately, n8n calls back when done |
| n8n creates scenes/chapters | Backend creates scenes/chapters based on LLM response |
| n8n fetches campaign/scene/characters | Backend sends pre-assembled context bundle |
| n8n writes turn.reaction to MongoDB | n8n returns data to backend, backend writes to MongoDB |
| n8n detects skill checks via LLM | Backend detects skill checks (regex/LLM), rolls dice |
| 34 nodes in workflow | 5-6 nodes in workflow |
| No progress indication | Frontend can show "AI is thinking..." message |

---

## 3. New Backend Endpoints

### 3.1 POST /api/v1/turns/{turn_id}/submit

**Purpose:** Async turn submission - starts processing and returns immediately

**Request:**
```json
POST /api/v1/turns/{turn_id}/submit
Content-Type: application/json

{
  "session_id": "session-xxx"
}
```

**Response:**
```json
HTTP 202 Accepted
{
  "turn_id": "turn-xxx",
  "status": "processing",
  "message": "Turn submitted for processing"
}
```

**Backend Logic:**
1. Validate turn exists and is in "ready" state
2. Validate all actions have required fields
3. Update `turn.status = "processing"`
4. Assemble context bundle (see section 5)
5. Call n8n webhook asynchronously (don't wait for response)
6. Return 202 Accepted to frontend

**Error Cases:**
- 404: Turn not found
- 400: Turn not in "ready" state
- 400: Invalid actions

---

### 3.2 POST /api/v1/internal/turns/{turn_id}/complete

**Purpose:** Callback endpoint for n8n to deliver LLM results

**Request:**
```json
POST /api/v1/internal/turns/{turn_id}/complete
Content-Type: application/json
X-N8N-Signature: <hmac-signature>  # Optional: for security

{
  "turn_id": "turn-xxx",
  "success": true,
  "result": {
    "narrative": "You descend into the dark basement...",
    "transition": {
      "type": "none" | "scene" | "chapter",
      "reason": "Players entered a new location",
      "suggested_name": "The Ritual Chamber"
    },
    "requires_input": true,
    "interaction_type": "CHOICE" | "COMBAT" | "QUESTION" | "DISCOVERY" | "NONE"
  },
  "metadata": {
    "llm_model": "gpt-oss:20b",
    "processing_time_ms": 4523
  }
}
```

**Response:**
```json
HTTP 200 OK
{
  "status": "completed",
  "turn_id": "turn-xxx",
  "scene_id": "scene-xxx",  # May be new scene if transition occurred
  "chapter_id": "chapter-xxx"  # May be new chapter if transition occurred
}
```

**Backend Logic:**
1. Validate turn exists and is in "processing" state
2. Validate callback signature (optional security)
3. Begin transaction:
   - Write `turn.reaction` to MongoDB
   - If `transition.type === "scene"`: Create new scene in current chapter
   - If `transition.type === "chapter"`: Create new chapter + new scene
   - Update `turn.status = "completed"`
   - Commit transaction
4. Emit Socket.IO events:
   - `turn_completed` to session room
   - `scene_created` if new scene (optional)
   - `chapter_created` if new chapter (optional)
5. Return 200 OK with scene/chapter IDs

**Error Cases:**
- 404: Turn not found
- 400: Turn not in "processing" state
- 500: Transaction failed (rollback)

---

### 3.3 GET /api/v1/turns/{turn_id}/status

**Purpose:** Optional polling endpoint for turn status (if Socket.IO unavailable)

**Response:**
```json
GET /api/v1/turns/{turn_id}/status

HTTP 200 OK
{
  "turn_id": "turn-xxx",
  "status": "ready" | "processing" | "completed" | "failed",
  "has_reaction": true,
  "error": null
}
```

**Note:** Primarily for debugging or clients without Socket.IO support.

---

## 4. Simplified n8n Workflow

### New DungeonMaster Workflow (5-6 nodes)

```
┌─────────────────────────┐
│ 1. Webhook Receive      │  Receives POST with context bundle + callback URL
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 2. Validate Context     │  Quick validation: required fields exist
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 3. Prepare LLM Prompt   │  Format context into LLM prompt with transition detection
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 4. Call LLM Synthesizer │  Main LLM call (Ollama via LLM Synthesizer SubWF)
│    SubWF                │  Returns: { narrative, transition, requires_input }
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 5. Format Callback      │  Prepare payload for backend callback
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 6. POST to Backend      │  Call callback_url with results
│    Callback             │
└─────────────────────────┘
```

### Node Descriptions

#### Node 1: Webhook Receive
- **Type:** `n8n-nodes-base.webhook`
- **Config:** POST, path: `coc_dungeonmaster_v2`, response mode: `responseNode`
- **Output:** Raw webhook payload

#### Node 2: Validate Context
- **Type:** `n8n-nodes-base.code`
- **Purpose:** Validate required fields exist
- **Logic:**
```javascript
const body = $json.body || $json;

// Validate required fields
if (!body.turn_id) throw new Error('Missing turn_id');
if (!body.callback_url) throw new Error('Missing callback_url');
if (!body.context) throw new Error('Missing context');

return [{ json: body }];
```

#### Node 3: Prepare LLM Prompt
- **Type:** `n8n-nodes-base.code`
- **Purpose:** Format context bundle into structured prompt for LLM Synthesizer
- **Output:** `{ agent_type: "dungeonmaster", collected_data: {...}, references: [...] }`

#### Node 4: Call LLM Synthesizer SubWF
- **Type:** `n8n-nodes-base.executeWorkflow`
- **Target:** `LLM Synthesizer SubWF` (existing)
- **Enhancement:** Update LLM Synthesizer prompt to include transition detection
- **Output:** `{ answer: "narrative", transition: {...}, requires_input: true }`

#### Node 5: Format Callback
- **Type:** `n8n-nodes-base.code`
- **Purpose:** Build callback payload
- **Logic:**
```javascript
const llmResult = $json;
const originalData = $('Webhook Receive').first().json;

return [{
  json: {
    url: originalData.callback_url,
    payload: {
      turn_id: originalData.turn_id,
      success: true,
      result: {
        narrative: llmResult.answer,
        transition: llmResult.transition || { type: "none" },
        requires_input: llmResult.requires_input || false,
        interaction_type: llmResult.interaction_type || "NONE"
      },
      metadata: {
        llm_model: llmResult.metadata?.model || "unknown",
        processing_time_ms: Date.now() - originalData.timestamp
      }
    }
  }
}];
```

#### Node 6: POST to Backend Callback
- **Type:** `n8n-nodes-base.httpRequest`
- **Method:** POST
- **URL:** `={{ $json.url }}`
- **Body:** `={{ JSON.stringify($json.payload) }}`
- **Timeout:** 10s (backend callback should be fast)

### Error Handling

Add an error workflow trigger:
- If any node fails, POST to `{callback_url}` with `{ success: false, error: "..." }`
- Backend marks turn as "failed" and notifies frontend

---

## 5. Context Bundle Schema

### What Backend Sends to n8n

```json
{
  "turn_id": "turn-abc123",
  "callback_url": "http://backend:8000/api/v1/internal/turns/turn-abc123/complete",
  "timestamp": "2025-11-29T10:30:00Z",

  "context": {
    "campaign": {
      "id": "campaign-xyz",
      "name": "The Haunting",
      "setting": "1920s Arkham, Massachusetts",
      "story_arc": "Investigate mysterious deaths at the Corbitt house",
      "themes": ["cosmic horror", "investigation", "sanity"]
    },

    "chapter": {
      "id": "chapter-001",
      "name": "The Old Corbitt House",
      "summary": "Investigators begin exploring the abandoned Corbitt estate after reports of strange noises and disappearances.",
      "order": 1
    },

    "scene": {
      "id": "scene-005",
      "name": "The Basement",
      "location": "Corbitt House - Basement Level",
      "summary": "A dark, musty basement with stone walls covered in strange symbols. The air is thick with decay.",
      "status": "in_progress",
      "participants": ["char-harrison", "char-martinez"]
    },

    "previous_turns": [
      {
        "order": 1,
        "actions": [
          {
            "actor_name": "Dr. Harrison",
            "speak": "I light my lantern and proceed down the stairs.",
            "act": "carefully descends with lantern raised"
          }
        ],
        "reaction": {
          "description": "You descend into darkness. The basement is larger than expected, with alcoves disappearing into shadow. Strange symbols cover the walls.",
          "summary": "Entered basement, discovered symbols"
        }
      }
    ],

    "characters": [
      {
        "id": "char-harrison",
        "name": "Dr. Marcus Harrison",
        "occupation": "Physician",
        "age": 42,
        "skills": [
          { "name": "Medicine", "value": 60 },
          { "name": "Spot Hidden", "value": 45 },
          { "name": "Library Use", "value": 40 },
          { "name": "Psychology", "value": 50 }
        ],
        "stats": {
          "sanity": { "current": 65, "max": 70 },
          "hp": { "current": 12, "max": 12 },
          "mp": { "current": 14, "max": 14 }
        },
        "conditions": []
      },
      {
        "id": "char-martinez",
        "name": "Detective Rosa Martinez",
        "occupation": "Police Detective",
        "age": 34,
        "skills": [
          { "name": "Firearms", "value": 55 },
          { "name": "Psychology", "value": 45 },
          { "name": "Spot Hidden", "value": 50 },
          { "name": "Listen", "value": 40 }
        ],
        "stats": {
          "sanity": { "current": 70, "max": 70 },
          "hp": { "current": 11, "max": 11 },
          "mp": { "current": 12, "max": 12 }
        },
        "conditions": []
      }
    ],

    "lore_context": [
      {
        "source": "Cthulhu Mythos - Elder Signs",
        "content": "Elder Signs are protective symbols used to ward against creatures of the Mythos. They appear as star-like patterns with specific geometric properties.",
        "relevance_score": 0.87
      },
      {
        "source": "Call of Cthulhu Rulebook - Basement Encounters",
        "content": "Basements in CoC often contain ritual chambers, summoning circles, or evidence of cult activity. Check for hidden passages.",
        "relevance_score": 0.72
      }
    ],

    "skill_checks": [
      {
        "character_id": "char-harrison",
        "character_name": "Dr. Harrison",
        "skill_name": "Spot Hidden",
        "skill_value": 45,
        "difficulty": "Regular",
        "rolled": 23,
        "target_regular": 45,
        "target_hard": 22,
        "target_extreme": 9,
        "success_level": "Hard Success",
        "success": true,
        "formatted": "Dr. Harrison rolled Spot Hidden: 23/45 (Hard Success)"
      }
    ]
  },

  "current_turn": {
    "order": 2,
    "actions": [
      {
        "actor_id": "char-harrison",
        "actor_name": "Dr. Harrison",
        "speak": "I examine the symbols more closely. Do they match anything I've read about?",
        "act": "approaches the wall and traces the symbols with his finger",
        "appearance": null,
        "emotion": "curious but wary"
      },
      {
        "actor_id": "char-martinez",
        "actor_name": "Detective Martinez",
        "speak": null,
        "act": "keeps her revolver ready and watches the shadows",
        "appearance": null,
        "emotion": "alert and tense"
      }
    ]
  }
}
```

### Field Descriptions

| Field | Purpose | Source |
|-------|---------|--------|
| `turn_id` | Unique turn identifier for callback | Generated by backend |
| `callback_url` | Where n8n POSTs results | Backend constructs |
| `timestamp` | When processing started | Backend |
| `context.campaign` | Story setting and arc | MongoDB: campaigns collection |
| `context.chapter` | Current story chapter | MongoDB: chapters collection |
| `context.scene` | Current scene details | MongoDB: scenes collection |
| `context.previous_turns` | Last 3-5 turns for continuity | MongoDB: turns collection (limited) |
| `context.characters` | Active characters with stats | MongoDB: characters collection |
| `context.lore_context` | Relevant rules/lore from RAG | Qdrant vector search |
| `context.skill_checks` | Pre-rolled dice results | Backend SkillCheckService |
| `current_turn.actions` | Player actions for this turn | MongoDB: turn.actions |

### Size Optimization

To keep payload size manageable:
- Limit `previous_turns` to last **5 turns** only
- Summarize older turns into chapter.summary
- Include only characters participating in current scene
- Limit lore_context to top **3 chunks** by relevance
- Omit null/empty fields

**Estimated payload size:** 15-30 KB (acceptable for webhook)

---

## 6. Scene/Chapter Transition Logic

### Decision: LLM-Driven Automated Transitions

**Chosen Approach:** Option A - LLM detects transition during narrative generation

**Why:**
- Most efficient (one LLM call, not two)
- LLM understands narrative context best
- Can use structured output for reliability
- No keyword parsing fragility

### Transition Criteria

#### New Scene Triggers
- **Location change** within same building/area (e.g., basement → first floor)
- **Time skip** less than 1 day (e.g., "several hours later")
- **Dramatic event** that shifts focus (combat ends, ritual completed)
- **Discovery** of significant location (hidden room, portal)

#### New Chapter Triggers
- **Major location change** (different building, different city)
- **Time skip** greater than 1 day (e.g., "three days later", "next week")
- **Story milestone** (defeat major enemy, complete investigation)
- **Tone shift** (investigation → combat arc, city → wilderness)

#### No Transition
- Continuing in same location and timeframe
- Dialogue or interaction in progress
- Combat in same scene

### LLM Prompt Enhancement

Update `LLM Synthesizer SubWF` prompt to include:

```
In addition to generating the narrative, determine if a scene or chapter transition is needed.

TRANSITION RULES:
- NEW SCENE: Location change within same area, time skip < 1 day, dramatic shift
- NEW CHAPTER: Major location change, time skip > 1 day, story milestone
- NONE: Continue in current scene

Return JSON:
{
  "narrative": "The full narrative response...",
  "transition": {
    "type": "none" | "scene" | "chapter",
    "reason": "Explanation for decision",
    "suggested_name": "Name for new scene/chapter (if applicable)"
  },
  "requires_input": true/false,
  "interaction_type": "CHOICE" | "COMBAT" | "QUESTION" | "DISCOVERY" | "NONE"
}
```

### Backend Processing

When backend receives callback:

```python
# Pseudo-code for transition handling

result = callback_payload["result"]
transition = result["transition"]

if transition["type"] == "scene":
    # Create new scene in current chapter
    new_scene = await scene_service.create_scene(
        chapter_id=current_chapter.id,
        name=transition["suggested_name"] or "Untitled Scene",
        summary="Scene in progress",
        participants=current_scene.participants
    )

    # Link turn to new scene
    await turn_service.update_scene(turn_id, new_scene.id)

    # Emit Socket.IO event
    await socketio.emit("scene_created", {
        "scene_id": new_scene.id,
        "scene_name": new_scene.name
    }, room=f"session:{session_id}")

elif transition["type"] == "chapter":
    # Create new chapter
    new_chapter = await chapter_service.create_chapter(
        campaign_id=current_campaign.id,
        name=transition["suggested_name"] or "Untitled Chapter",
        order=current_chapter.order + 1
    )

    # Create new scene in new chapter
    new_scene = await scene_service.create_scene(
        chapter_id=new_chapter.id,
        name="Opening Scene",
        participants=current_scene.participants
    )

    # Link turn to new scene
    await turn_service.update_scene(turn_id, new_scene.id)

    # Emit Socket.IO events
    await socketio.emit("chapter_created", {
        "chapter_id": new_chapter.id,
        "chapter_name": new_chapter.name,
        "scene_id": new_scene.id
    }, room=f"session:{session_id}")
```

### Validation & Safeguards

1. **LLM Override Protection**: Backend can reject transitions that don't make sense
   - e.g., Chapter transition after 1 turn is suspicious
   - Log for review if transition seems incorrect

2. **Manual Override**: Future feature - allow GM to manually trigger transitions

3. **Transition History**: Track transition decisions in metadata for auditing

---

## 7. Migration Steps

### Ordered Implementation Plan

#### Step 1: Create Backend Services (No n8n changes yet)
**Duration:** 2-3 days

1. **ContextAssemblyService** (`backend/app/services/context_assembly.py`)
   - `assemble_turn_context(turn_id) -> ContextBundle`
   - Fetches campaign, chapter, scene, characters
   - Calls Qdrant for lore context
   - Limits previous_turns to last 5

2. **SkillCheckService** (`backend/app/services/skill_check.py`)
   - `detect_skill_checks(actions, characters) -> List[SkillCheckDetection]`
   - Uses regex/keyword matching initially (can upgrade to LLM later)
   - `roll_skill_checks(detections) -> List[SkillCheckResult]`
   - Integrates dice rolling logic (port from Dice Roller SubWF)

3. **TransitionService** (`backend/app/services/transition.py`)
   - `create_scene(chapter_id, name, summary) -> Scene`
   - `create_chapter(campaign_id, name, order) -> Chapter`
   - Transaction handling for atomic creation

**Testing:** Unit tests for each service

---

#### Step 2: Create New Backend Endpoints (Still using old n8n workflow)
**Duration:** 2 days

1. Implement `POST /api/v1/turns/{turn_id}/submit`
   - Async version, calls OLD n8n workflow for now
   - Add feature flag: `USE_ASYNC_TURN_PROCESSING` (default: False)

2. Implement `POST /api/v1/internal/turns/{turn_id}/complete`
   - Callback handler
   - Initially does nothing (returns 200 OK)

3. Update Socket.IO events
   - Add `turn_processing` event
   - Add `turn_completed` event
   - Add `scene_created`, `chapter_created` events

**Testing:** Integration tests with old workflow

---

#### Step 3: Enhance LLM Synthesizer SubWF
**Duration:** 1 day

1. Update prompt to include transition detection
2. Modify output parser to extract `transition` field from JSON
3. Test with various narrative scenarios

**Testing:** Manual testing with different turn scenarios

---

#### Step 4: Build New Simplified DungeonMaster Workflow
**Duration:** 2 days

1. Create `DungeonMaster_Main_v2.json` (keep old workflow untouched)
2. Implement 6 nodes as designed (section 4)
3. Configure webhook path: `coc_dungeonmaster_v2`
4. Add error handling workflow

**Testing:**
- Test with mock context bundles
- Verify callback is called correctly
- Test error scenarios (LLM timeout, invalid context)

---

#### Step 5: End-to-End Integration Testing
**Duration:** 2-3 days

1. Enable feature flag `USE_ASYNC_TURN_PROCESSING=True` in dev environment
2. Test complete flow:
   - Submit turn → Processing → Callback → Completion
   - Verify Socket.IO events fire correctly
   - Test scene transitions
   - Test chapter transitions
   - Test skill checks
3. Load testing:
   - Submit 10 concurrent turns
   - Verify no race conditions
   - Monitor callback latency

**Acceptance Criteria:**
- ✅ Turn submission returns in < 100ms
- ✅ LLM callback received within 2 minutes (typical Ollama time)
- ✅ Scene transitions create correct MongoDB documents
- ✅ Socket.IO events received by frontend
- ✅ No orphaned turns in "processing" state

---

#### Step 6: Frontend Updates (If Needed)
**Duration:** 1 day

1. Update turn submission to handle async response
2. Show "AI is thinking..." loading state
3. Listen for Socket.IO `turn_completed` event
4. Display scene/chapter transitions in UI

---

#### Step 7: Production Cutover
**Duration:** 1 day

1. Deploy backend with feature flag OFF
2. Deploy new n8n workflow (inactive)
3. Monitor production for 24 hours
4. Enable feature flag for 10% of sessions (gradual rollout)
5. Monitor error rates, callback success rate
6. Gradually increase to 100% over 3 days

**Rollback Plan:**
- Disable feature flag → reverts to old workflow
- No data migration needed (both write same schema)

---

#### Step 8: Cleanup (After 1 Week Stable)
**Duration:** 1 day

1. Remove old `DungeonMaster_Main.json` workflow
2. Rename `DungeonMaster_Main_v2.json` → `DungeonMaster_Main.json`
3. Remove feature flag from code
4. Update documentation
5. Archive old workflow JSON for reference

---

## 8. Risk Assessment

### Risk 1: Callback URL Unreachable

**Scenario:** n8n completes LLM generation but cannot reach backend callback endpoint

**Impact:** HIGH - Turn stuck in "processing" state, narrative lost

**Mitigation:**
1. **n8n retry logic**: Exponential backoff (3 retries: 5s, 15s, 45s)
2. **n8n logging**: Log full callback payload to n8n execution logs
3. **Backend recovery endpoint**: `POST /api/v1/admin/turns/{turn_id}/recover`
   - Admin can manually paste n8n payload to complete turn
4. **Monitoring**: Alert if callback failure rate > 1%

**Detection:** Backend monitors "processing" turns older than 5 minutes

---

### Risk 2: n8n Processes Turn but Callback Fails After Retries

**Scenario:** Network partition, backend down during processing

**Impact:** MEDIUM - Narrative exists in n8n logs but not in database

**Mitigation:**
1. **n8n persistent storage**: Enable execution data retention (7 days)
2. **Manual recovery tool**: Script to replay failed callbacks from n8n execution history
3. **Dead letter queue**: Failed callbacks stored in Redis for later retry

**Detection:** Compare n8n execution count vs. completed turn count (daily reconciliation)

---

### Risk 3: Context Bundle Too Large

**Scenario:** Campaign with many characters, long turn history causes payload > 100 KB

**Impact:** LOW - Webhook may timeout or fail

**Mitigation:**
1. **Size limits**:
   - Max 5 previous turns
   - Max 10 characters (filter to scene participants only)
   - Max 3 lore chunks
2. **Compression**: gzip compress payload if > 50 KB
3. **Monitoring**: Log payload sizes, alert if approaching limits

**Detection:** Backend logs payload size before sending to n8n

---

### Risk 4: LLM Takes > 5 Minutes

**Scenario:** Complex narrative, slow Ollama response time

**Impact:** LOW - User frustration, but system handles it

**Mitigation:**
1. **Timeout**: Set n8n workflow timeout to 10 minutes (n8n setting)
2. **Frontend feedback**: Show elapsed time: "AI thinking for 2m 34s..."
3. **Cancel option**: Future feature - allow user to cancel turn processing
4. **Optimization**: Use faster LLM model for simple turns (Haiku vs. GPT-OSS)

**Detection:** Log LLM response times, analyze P95/P99 latency

---

### Risk 5: Scene Creation Fails After Narrative Generated

**Scenario:** MongoDB error during scene creation in callback handler

**Impact:** MEDIUM - Turn has narrative but no scene transition

**Mitigation:**
1. **Transaction**: Wrap scene creation + turn update in transaction
2. **Rollback**: If scene creation fails, don't write turn.reaction
3. **Retry**: Return 500 to n8n, trigger retry of entire callback
4. **Partial completion**: Alternative - write turn.reaction but mark transition as "failed"

**Detection:** Monitor MongoDB errors in callback handler

---

### Risk 6: Duplicate Turn Processing

**Scenario:** User double-clicks submit, or retry logic causes duplicate

**Impact:** LOW - Wasted LLM cost, potential duplicate narratives

**Mitigation:**
1. **Status check**: Reject submission if turn.status !== "ready"
2. **Idempotency**: Callback handler checks if turn already completed
3. **Rate limiting**: 1 turn submission per 5 seconds per user

**Detection:** Log duplicate submission attempts

---

### Risk 7: Transition Detection Wrong

**Scenario:** LLM incorrectly detects chapter transition when scene transition appropriate

**Impact:** LOW - Story structure slightly off, but continues

**Mitigation:**
1. **Validation rules**: Backend rejects suspicious transitions
   - e.g., Chapter transition after 1 turn → downgrade to scene
2. **Human override**: GM can manually adjust scene/chapter after the fact
3. **LLM tuning**: Improve prompt with examples

**Detection:** Log all transitions, review manually weekly

---

### Risk 8: Socket.IO Connection Dropped

**Scenario:** User's connection drops during LLM processing

**Impact:** LOW - User doesn't see completion notification

**Mitigation:**
1. **Reconnection**: Socket.IO auto-reconnects
2. **State sync**: On reconnect, frontend fetches latest turn status
3. **Polling fallback**: If Socket.IO fails, poll `/turns/{id}/status` every 10s

**Detection:** Monitor Socket.IO disconnect rate

---

### Risk Summary Table

| Risk | Impact | Probability | Mitigation Effort | Priority |
|------|--------|-------------|-------------------|----------|
| Callback unreachable | High | Low | Medium (retry + logging) | P1 |
| Callback fails after retries | Medium | Low | High (recovery tools) | P2 |
| Context bundle too large | Low | Low | Low (size limits) | P3 |
| LLM timeout | Low | Medium | Low (timeout config) | P3 |
| Scene creation fails | Medium | Low | Medium (transactions) | P2 |
| Duplicate processing | Low | Medium | Low (status checks) | P3 |
| Wrong transition | Low | Medium | Medium (validation) | P3 |
| Socket.IO dropped | Low | Medium | Low (polling fallback) | P3 |

**Overall Risk Level:** ACCEPTABLE - No critical unmitigated risks identified

---

## Summary

This refactoring plan transforms the DungeonMaster workflow from a monolithic 34-node process into a clean hybrid architecture:

- **Backend:** Owns state, assembles context, handles business logic
- **n8n:** Focuses purely on LLM orchestration (5-6 nodes)
- **Async pattern:** Enables long-running LLM calls without blocking
- **Automated transitions:** LLM-driven scene/chapter creation
- **Single source of truth:** Backend writes all MongoDB data

**Next Steps:** Proceed to Phase 2C (Documentation) or begin implementation (Phase 3).

