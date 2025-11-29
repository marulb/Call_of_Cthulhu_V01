# Agent Handoff Context

> **Purpose:** Quick briefing for AI agents to continue work  
> **Last Updated:** 2024-11-29  
> **Last Agent:** GitHub Copilot  
> **Session:** Documentation setup + Phase 2 task definition  
> **Word Limit:** ~500 words

---

## Active Task

**📋 Current Task:** `docs/agents/TASK_PHASE2_DESIGN.md`  
**Status:** Ready for Claude Code  
**Goal:** Design hybrid architecture to simplify DungeonMaster workflow

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

## Clarifying Questions Needed

Before Phase 2, ask the user:
1. Is 60-second webhook timeout acceptable?
2. Should scene creation remain AI-driven?
3. Where should skill check logic live?
