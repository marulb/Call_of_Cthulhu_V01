# Architecture Overview

> **Last Updated:** 2024-11-29  
> **Analyzed By:** GitHub Copilot (Initial Scan)  
> **Status:** Phase 1 - Understanding

## Project Purpose

**Call of Cthulhu** is a tabletop RPG campaign management system that combines:
- A **FastAPI backend** for authoritative state management and MongoDB persistence
- **n8n workflows** for LLM-driven game orchestration (Keeper AI / DungeonMaster)
- A **VueJS frontend** for player interaction (out of scope for this analysis)

The system enables multiplayer sessions where players submit actions, and an AI "Dungeon Master" generates narrative responses.

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Vue 3 + TypeScript + Vite | Player UI |
| Backend | FastAPI + Motor (async MongoDB) | State management, API |
| Real-time | Socket.IO | Player presence, live updates |
| Orchestration | n8n | Workflow automation, LLM calls |
| LLM | Ollama (local) | Narrative generation |
| Vector DB | Qdrant | RAG for rules/lore |
| Database | MongoDB | Game records, characters |

---

## Backend File Responsibilities

### Core Infrastructure

| File | Lines | Responsibility |
|------|-------|---------------|
| `main.py` | 85 | FastAPI app setup, CORS, router mounting, lifecycle hooks |
| `database.py` | 50 | MongoDB connection management (system + gamerecords DBs) |
| `models.py` | 478 | Pydantic models for all entities (World, Realm, Campaign, Chapter, Scene, Turn, Character, ActionDraft) |
| `socketio_manager.py` | 316 | Real-time player presence, session joining, action broadcasts, ready states |

### Entity Routes (CRUD)

| File | Lines | Entity | Notes |
|------|-------|--------|-------|
| `routes_worlds.py` | 94 | World | Top-level ruleset container |
| `routes_realms.py` | 105 | Realm | Player group within a world |
| `routes_campaigns.py` | 115 | Campaign | Story arc within a realm |
| `routes_chapters.py` | 135 | Chapter | Major story segment |
| `routes_scenes.py` | 135 | Scene | AI-managed story segment within chapter |
| `routes_turns.py` | 273 | Turn | **KEY:** Player actions + Keeper reaction; calls n8n webhook |
| `routes_sessions.py` | 126 | Session | Active play session tracking |
| `routes_players.py` | 136 | Player | Player identity management |
| `routes_characters.py` | 142 | Character | Call of Cthulhu character sheets |
| `routes_action_drafts.py` | 158 | ActionDraft | Temporary UI state for current turn |

### AI Integration

| File | Lines | Responsibility |
|------|-------|---------------|
| `routes_ai.py` | 400 | AI endpoints: Prophet (Q&A), DungeonMaster (turn processing), mock fallbacks |

---

## n8n Workflow Responsibilities

### Main Workflows

| Workflow | Nodes | Responsibility |
|----------|-------|---------------|
| `DungeonMaster_Main.json` | 35 | **PRIMARY:** Turn processing orchestration. Receives actions → creates scene/turn if needed → fetches context → calls LLM → writes reaction |
| `Prophet_Main.json` | 20 | Q&A assistant. Intent classification → routes to appropriate data source → synthesizes answer |

### Sub-Workflows (Reusable Components)

| Workflow | Nodes | Responsibility |
|----------|-------|---------------|
| `Dice_Roller_SubWF.json` | 5 | Dice rolling mechanics (standard, percentage, skill checks) |
| `LLM_Synthesizer_SubWF.json` | 4 | Context building + Ollama LLM call + answer extraction |
| `MongoDB_Query_SubWF.json` | 8 | Parameterized MongoDB queries (character, turn, session, scene, campaign) |
| `Qdrant_RAG_SubWF.json` | 5 | Vector search for rules/lore retrieval |

---

## Entity Hierarchy

```
World (ruleset)
└── Realm (player group)
    ├── Players[]
    ├── Characters[]
    └── Campaigns[]
        └── Chapters[]
            └── Scenes[]
                └── Turns[]
                    ├── Actions[] (player inputs)
                    └── Reaction (AI output)

Session (tracks active play)
├── scene_id (current scene)
├── players_active[]
└── turn_number

ActionDraft (temporary UI state, cleared after turn submission)
```

---

## Key Integration Point

**`routes_turns.py` → `POST /{turn_id}/submit`** is the critical handoff:

1. Frontend submits turn via REST
2. Backend calls `http://n8n:5678/webhook/coc_dungeonmaster`
3. n8n orchestrates: context fetch → LLM call → response
4. Backend receives response, writes to MongoDB
5. Socket.IO broadcasts update to players

---

## Next Steps

- [ ] Document data flow in detail (`DATA_FLOW.md`)
- [ ] Identify friction points (`FRICTION_POINTS.md`)
- [ ] Phase 2: Design hybrid architecture
