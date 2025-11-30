# Agent Handoff Context

> **Last Updated:** 2024-11-30 01:30  
> **Last Agent:** GitHub Copilot  
> **Current Phase:** 6 - DungeonMaster Refinement

---

## Quick Status

| Component | Status | Notes |
|-----------|--------|-------|
| Phase 4 (M1-M8) | ✅ Complete | All milestones done |
| Phase 5 (UX) | ✅ Complete | P5-1 through P5-4 done, P5-5 deferred |
| AI Action Generation | ✅ Working | But needs context improvements |
| DungeonMaster | 🔄 Needs Work | Too fast, verbose, missing context |
| n8n Workflows | ✅ Synced | Just exported from live instance |

---

## What Just Happened

### Session 2024-11-30

1. **Fixed AI Action Generation**
   - Fixed collection names (db.entities for characters, db.scenes for scenes)
   - Fixed kind filter (characters use "pc", not "character")
   - Added auto-creation of chapter/scene on game load
   - Commits: c70389b, 6e4e843, a1d5a1b

2. **Fixed AI Character Storage**
   - Added ai_controlled and ai_personality to API definitions
   - Fixed all submit handlers to pass AI fields
   - Changed AI badge from emoji to subtle star
   - Commit: 5c51b5d

3. **Exported n8n Workflows**
   - DungeonMaster_Main.json updated from live instance
   - LLM_Synthesizer_SubWF.json updated
   - Commit: 4527c8a

4. **Created DungeonMaster Specification**
   - docs/specifications/DUNGEONMASTER_AGENT.md
   - Defines pacing rules, data requirements, behavioral guidelines

5. **Reorganized Task/Report Structure**
   - Old files moved to docs/agents/archive/
   - New structure: CURRENT_TASK.md, CURRENT_REPORT.md (overwritten per phase)

---

## Current Task

**File:** docs/agents/CURRENT_TASK.md

5 tasks for DungeonMaster improvements:
- T1: Fix AI character action context (other characters' actions)
- T2: Clarify "appearance" field meaning
- T3: Implement pacing system (turn counting, phase rules)
- T4: Shorten DM responses (150-300 words target)
- T5: Enhance character context for DM

**Recommended order:** T2 → T1 → T5 → T4 → T3

---

## Key Files

### Documentation
- docs/specifications/DUNGEONMASTER_AGENT.md - DM agent spec (NEW)
- docs/agents/CURRENT_TASK.md - Current work items
- docs/architecture/ARCHITECTURE_OVERVIEW.md - System design

### Backend (AI/DM)
- backend/app/routes_ai.py - AI action generation endpoint
- backend/app/services/llm.py - LLM service, prompts
- backend/app/routes_turns.py - Turn submission, DM triggering

### Frontend (Relevant)
- frontend/src/components/SceneActiveTurn.vue - Action drafting UI
- frontend/src/services/api.ts - API definitions

### n8n Workflows
- n8n_workflows/DungeonMaster_Main.json - Main DM workflow
- n8n_workflows/LLM_Synthesizer_SubWF.json - LLM processing

---

## Known Issues

1. **AI actions don't see other characters' turn actions**
   - existing_actions parameter exists but not used properly

2. **"Appearance" field misinterpreted**
   - AI thinks it means physical description
   - Should mean demeanor/body language

3. **DM pacing too fast**
   - Horror elements appear turn 1
   - Should be slow burn (10+ turns before hints)

4. **DM responses too long**
   - Currently 500+ words
   - Target: 150-300 words

5. **DM lacks character knowledge**
   - Doesn't know character backgrounds
   - Doesn't acknowledge character expertise

---

## Architecture Notes

### Database Collections
- entities - Characters (kind: "pc"), NPCs (kind: "npc")
- scenes - Scenes
- chapters - Chapters
- campaigns - Campaigns
- turns - Completed turns
- action_drafts - In-progress actions

### Service Ports
| Service | Port |
|---------|------|
| Frontend | 3093 |
| Backend | 8093 |
| MongoDB | 27093 |
| n8n | 5693 |
| Qdrant | 6393 |

---

## For Next Agent

1. Read docs/agents/CURRENT_TASK.md for work items
2. Read docs/specifications/DUNGEONMASTER_AGENT.md for DM requirements
3. Start with T2 (appearance field clarification) - quick win
4. When done, update this file and CURRENT_TASK.md
