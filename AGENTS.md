# AI Agent Instructions

> **Location:** Project root (`AGENTS.md`)  
> **Purpose:** Universal instructions for all AI coding agents  
> **Last Updated:** 2024-11-30

---

## Quick Context

**Project:** Call of Cthulhu RPG Campaign Manager  
**Stack:** FastAPI + MongoDB + n8n + Vue 3 + Ollama LLM  
**Status:** Active development, Phase 6 - DungeonMaster Refinement

---

## Documentation Structure

```
/
├── AGENTS.md                    ← YOU ARE HERE (agent instructions)
├── README.md                    ← Project setup, ports, commands
├── docs/
│   ├── architecture/
│   │   ├── ARCHITECTURE_OVERVIEW.md   ← System design
│   │   ├── DATA_FLOW.md               ← How data moves
│   │   ├── FRICTION_POINTS.md         ← Known problems
│   │   └── REFACTORING_PLAN.md        ← Implementation plan
│   ├── specifications/
│   │   ├── GAMEPLAY_UI.md             ← Frontend spec
│   │   ├── DATA_MODEL.md              ← MongoDB schema
│   │   └── DUNGEONMASTER_AGENT.md     ← DM agent behavior spec
│   ├── decisions/
│   │   └── ADR-*.md                   ← Architecture Decision Records
│   └── agents/
│       ├── HANDOFF_CONTEXT.md         ← Quick briefing for agents
│       ├── CURRENT_TASK.md            ← Active task (overwritten per phase)
│       └── archive/                   ← Previous task/report files
├── backend/app/                 ← FastAPI routes + models
├── frontend/src/                ← Vue 3 components
└── n8n_workflows/               ← Workflow JSON files + README
```

---

## Output Rules

**Keep chat responses minimal.** Write detailed output to files:

1. **Task completion** → Update `docs/agents/CURRENT_TASK.md` (mark items done)
2. **Handoff updates** → Write to `docs/agents/HANDOFF_CONTEXT.md`
3. **Design docs** → Write to `docs/architecture/` or `docs/decisions/`

**Chat response format after completing a task:**
```
✅ <Task Name> Complete

Updated: docs/agents/CURRENT_TASK.md
Next: <next task from CURRENT_TASK.md>
```

Do NOT paste file contents or long summaries in chat.

---

## Common Commands

### Development

```bash
# Start full stack (Docker)
docker-compose up -d

# Backend only (local dev)
cd backend && uvicorn main:app --reload --port 8093

# Frontend only (local dev)
cd frontend && npm run dev

# Check logs
docker-compose logs -f backend
docker-compose logs -f n8n
```

### Ports

| Service | Host Port | Internal |
|---------|-----------|----------|
| Frontend | 3093 | - |
| Backend | 8093 | 8000 |
| MongoDB | 27093 | 27017 |
| n8n | 5693 | 5678 |
| Qdrant | 6393 | 6333 |

### n8n API

```bash
# List workflows
curl -H "X-N8N-API-KEY: $N8N_KEY" http://localhost:5693/rest/workflows

# Trigger DungeonMaster
curl -X POST http://localhost:5693/webhook/coc_dungeonmaster \
  -H "Content-Type: application/json" \
  -d '{"DungeonMaster": [...]}'
```

---

## Documentation Update Rules

**Every agent session MUST follow these rules:**

### 1. Before Starting Work
- Read `docs/agents/HANDOFF_CONTEXT.md` for quick context
- Check `docs/architecture/FRICTION_POINTS.md` for known issues
- Review relevant section of `ARCHITECTURE_OVERVIEW.md`

### 2. After Completing Work
- Update `HANDOFF_CONTEXT.md` with:
  - What was changed
  - New friction points discovered
  - What the next agent should know
- Add timestamp and agent name to "Last Updated"

### 3. When Adding Features
- Update `ARCHITECTURE_OVERVIEW.md` if new components added
- Update `DATA_FLOW.md` if data paths changed
- Create `docs/decisions/ADR-XXX-*.md` for significant decisions

### 4. When Fixing Bugs
- Remove resolved items from `FRICTION_POINTS.md`
- Document fix approach if non-obvious

### 5. ADR Format (Architecture Decision Records)

```markdown
# ADR-XXX: Title

## Status
Proposed | Accepted | Deprecated | Superseded

## Context
What is the issue?

## Decision
What was decided?

## Consequences
What are the trade-offs?
```

---

## Code Style Guidelines

### Python (Backend)
- Use Pydantic models for all request/response types
- Async functions for all database operations
- Document routes with docstrings
- Keep routes thin, logic in services

### TypeScript (Frontend)
- Composition API with `<script setup>`
- Pinia for state management
- Type all props and emits

### n8n Workflows
- Name nodes descriptively
- Use sub-workflows for reusable logic
- Document webhook inputs/outputs in README

---

## Current Focus Areas

### Phase 2 (Upcoming)
- Simplify `DungeonMaster_Main.json` workflow
- Move context assembly to backend
- Backend owns all MongoDB writes
- n8n focuses only on LLM orchestration

### Known Friction Points (Top 3)
1. Dual MongoDB write paths (backend + n8n)
2. Scene/chapter creation logic in n8n
3. Complex context assembly in workflow

---

## Agent-Specific Notes

### For Claude Code
- This file is auto-detected as `AGENTS.md`
- Extended Thinking useful for architecture design
- Prefer writing to `docs/` over long chat responses

### For GitHub Copilot
- Reference `docs/agents/HANDOFF_CONTEXT.md` for context
- Use `@workspace` to search codebase
- Check `FRICTION_POINTS.md` before proposing solutions

### For Other Agents
- Start by reading `HANDOFF_CONTEXT.md`
- Update docs after completing work
- Ask clarifying questions before large changes

---

## Handoff Checklist

When ending a session, ensure:

- [ ] `HANDOFF_CONTEXT.md` updated with session summary
- [ ] New files documented in relevant README
- [ ] Friction points updated (added/removed)
- [ ] Breaking changes noted
- [ ] Next steps clearly stated
