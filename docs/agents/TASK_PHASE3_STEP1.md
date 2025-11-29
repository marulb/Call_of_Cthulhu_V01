# Task: Phase 3 - Implement Hybrid Architecture (Step 1: Backend Services)

## Mode: Autonomous with Checkpoints
Complete Step 1 fully, then pause for review before Step 2.

---

## Setup

Read these files first:
1. `AGENTS.md` — agent instructions and documentation rules
2. `docs/agents/HANDOFF_CONTEXT.md` — current state (Phase 2 complete)
3. `docs/architecture/REFACTORING_PLAN.md` — **the design to implement**
   - Section 3: New Backend Endpoints
   - Section 5: Context Bundle Schema  
   - Section 6: Scene/Chapter Transition Logic

Reference existing code for patterns:
- `backend/app/routes_turns.py` — current turn handling
- `backend/app/models.py` — Pydantic models
- `backend/app/database.py` — MongoDB access

---

## Context: Key Design Decisions (from Phase 2)

| Decision | Value |
|----------|-------|
| Processing model | Async with callback |
| MongoDB writes | Backend only (n8n never writes) |
| Context assembly | Backend service provides complete bundle |
| Skill checks | Backend detects + rolls, LLM can enhance |
| Transitions | LLM-detected during narrative generation |
| Feature flag | `USE_ASYNC_TURN_PROCESSING` for gradual rollout |

---

## Step 1: Create Backend Services

### 1.1 Create Context Assembly Service

Create `backend/app/services/context_assembly.py`:

```python
"""
Context assembly service for turn processing.
Gathers all context needed for LLM narrative generation.
"""
```

**Must include:**
- `ContextBundle` Pydantic model matching Section 5 schema
- `async def assemble_context(turn_id: str) -> ContextBundle`
- Fetch: campaign, chapter, scene, previous turns, characters, lore (Qdrant)
- Handle missing data gracefully (defaults, not errors)
- Logging for debugging

**Reference:** `REFACTORING_PLAN.md` Section 5 for exact schema.

---

### 1.2 Create Skill Check Service

Create `backend/app/services/skill_check.py`:

```python
"""
Skill check detection and dice rolling service.
Replaces n8n skill check nodes.
"""
```

**Must include:**
- `SkillCheckResult` Pydantic model
- `def detect_skill_checks(actions: List[Action]) -> List[DetectedSkill]`
  - Use regex/keyword matching (not LLM) for speed
  - Match against CoC 7e skill list
- `async def roll_skill_checks(detected: List[DetectedSkill], characters: List[Character]) -> List[SkillCheckResult]`
  - D100 roll logic
  - Success levels: Critical, Extreme, Hard, Regular, Fail, Fumble
- Dice rolling utility functions

---

### 1.3 Create Transition Detection Service

Create `backend/app/services/transition.py`:

```python
"""
Scene/chapter transition detection service.
Processes LLM response to detect narrative transitions.
"""
```

**Must include:**
- `TransitionResult` Pydantic model with `type: "scene" | "chapter" | None`
- `def parse_transition_from_llm(llm_response: dict) -> TransitionResult`
  - Extract transition info from LLM structured output
- `async def create_scene(chapter_id: str, trigger: str) -> Scene`
- `async def create_chapter(campaign_id: str, trigger: str) -> Chapter`
- Summarization logic for closing scenes/chapters

---

### 1.4 Create Services __init__.py

Create `backend/app/services/__init__.py`:

```python
"""Backend services for turn processing."""
from .context_assembly import ContextAssemblyService, ContextBundle
from .skill_check import SkillCheckService, SkillCheckResult
from .transition import TransitionService, TransitionResult

__all__ = [
    "ContextAssemblyService", "ContextBundle",
    "SkillCheckService", "SkillCheckResult", 
    "TransitionService", "TransitionResult",
]
```

---

## Code Style Requirements

Follow existing patterns in `backend/app/`:

- **Pydantic models** for all data structures
- **Async functions** for all database operations
- **Type hints** on all functions
- **Docstrings** explaining purpose
- **Logging** with `logging.getLogger(__name__)`
- **Error handling** with custom exceptions where appropriate

Example from existing code:
```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class MyModel(BaseModel):
    id: Optional[str] = None
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True
```

---

## Feature Flag

Add to `backend/app/config.py` (create if doesn't exist):

```python
import os

# Feature flags
USE_ASYNC_TURN_PROCESSING = os.getenv("USE_ASYNC_TURN_PROCESSING", "false").lower() == "true"
```

---

## Constraints

- ✅ Create new files in `backend/app/services/`
- ✅ Follow existing code patterns
- ✅ Add proper type hints and docstrings
- ✅ Include feature flag for gradual rollout
- ❌ Do NOT modify `routes_turns.py` yet (Step 2)
- ❌ Do NOT modify n8n workflows yet (Step 4)
- ❌ Do NOT delete any existing code

---

## Deliverables

After completing Step 1:

1. **New files created:**
   - [ ] `backend/app/services/__init__.py`
   - [ ] `backend/app/services/context_assembly.py`
   - [ ] `backend/app/services/skill_check.py`
   - [ ] `backend/app/services/transition.py`
   - [ ] `backend/app/config.py` (if doesn't exist)

2. **Update documentation:**
   - [ ] Update `docs/agents/HANDOFF_CONTEXT.md` with:
     - Step 1 complete
     - Files created
     - Ready for Step 2

3. **Do NOT proceed to Step 2** — pause for human review.

---

## Success Criteria

Services are complete when:
- All files created with proper structure
- Pydantic models match REFACTORING_PLAN.md Section 5
- Async functions use Motor for MongoDB access
- Code follows existing patterns in backend/app/
- No import errors (run `python -c "from app.services import *"`)

---

## Begin

1. Read the referenced documentation
2. Create the services directory and files
3. Implement each service following the design
4. Update HANDOFF_CONTEXT.md
5. STOP and report completion (do not start Step 2)
