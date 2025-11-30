# Agent Handoff Context

> **Last Updated:** 2024-11-30 14:00  
> **Last Agent:** GitHub Copilot  
> **Current Phase:** 7 - TTS / Narration Feature (COMPLETE)

---

## Quick Status

| Component | Status | Notes |
|-----------|--------|-------|
| Phase 4 (M1-M8) | ✅ Complete | All milestones done |
| Phase 5 (UX) | ✅ Complete | P5-1 through P5-4 done, P5-5 deferred |
| Phase 6 (DM Refinement) | ✅ Complete | All 5 tasks done |
| Phase 7 (TTS) | ✅ Complete | Web Speech API, settings modal |
| AI Action Generation | ✅ Working | Knows other characters' actions |
| DungeonMaster | ✅ Improved | Pacing, word limits, character context |
| n8n Workflows | ✅ Updated | Pacing info, shorter prompts |

---

## What Just Happened

### Session 2024-11-30 (Phase 7 - TTS Complete)

**Web Speech Synthesizer implementation:**

1. **useSpeechSynthesis composable** (new)
   - `frontend/src/composables/useSpeechSynthesis.ts`
   - Play/stop controls with text selection support
   - Prefers "Google UK English Male" with fallback chain
   - Integrates with settings store for voice/rate/pitch/volume

2. **Settings store** (new)
   - `frontend/src/stores/settings.ts`
   - Pinia store persisting TTS preferences to localStorage
   - Key: `coc_settings`

3. **SceneProgress.vue** (modified)
   - Added ▶/■ play/stop toggle button in header
   - Position: between turn count badge and close button
   - Tooltip: "Select text to start reading from that point..."
   - Reads Keeper's responses aloud from selection or beginning

4. **SessionSettings.vue** (new)
   - `frontend/src/components/SessionSettings.vue`
   - Modal overlay with collapsible sections
   - "🎭 Storyteller Voice" section with:
     - Voice dropdown (English voices)
     - Rate/Pitch/Volume sliders
     - Test textarea with play/stop preview
   - Placeholder sections for Display/Notifications

5. **SessionInfoHeader.vue** (modified)
   - Added ⚙ gear icon button
   - Emits `openSettings` event

6. **GameView.vue** (modified)
   - Imported SessionSettings component
   - Added `showSettings` state
   - Wired gear button to open modal

---

## Files Created

| File | Purpose |
|------|---------|
| `frontend/src/composables/useSpeechSynthesis.ts` | TTS composable |
| `frontend/src/stores/settings.ts` | Settings persistence |
| `frontend/src/components/SessionSettings.vue` | Settings modal |
| `docs/agents/CURRENT_REPORT.md` | Implementation report |

## Files Modified

| File | Changes |
|------|---------|
| `frontend/src/components/SceneProgress.vue` | Play/stop button + TTS logic |
| `frontend/src/components/SessionInfoHeader.vue` | Gear icon + emit |
| `frontend/src/views/GameView.vue` | Import modal + state |
| `docs/agents/CURRENT_TASK.md` | Phase 7 task list |

---

## Browser Compatibility Notes

- Web Speech API: Chrome, Edge, Firefox, Safari
- "Google UK English Male" only in Chrome/Chromium
- Fallback: first en-GB or en-* voice available
- Settings persist via localStorage

---

## Previous Phase (6) Summary

3. **Phase 7 candidates:**
   - RAG integration for lore context
   - Scene transition automation
   - NPC dialogue enhancements

---

## Key Files

### Documentation
- docs/specifications/DUNGEONMASTER_AGENT.md - DM agent spec
- docs/agents/CURRENT_TASK.md - Phase 6 tasks (COMPLETE)
- docs/architecture/ARCHITECTURE_OVERVIEW.md - System design

### Backend (AI/DM)
- backend/app/services/context_assembly.py - Context bundling + pacing
- backend/app/services/llm.py - LLM service, prompts
- backend/app/routes_turns.py - Turn submission, DM triggering

### Frontend
- frontend/src/components/SceneActiveTurn.vue - Action drafting UI

### n8n Workflows
- n8n_workflows/LLM_Synthesizer_SubWF.json - DM prompts + pacing
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
