# Current Task: Web Speech Synthesizer Implementation

> **Phase:** 7 - TTS / Narration Feature  
> **Created:** 2024-11-30  
> **Updated:** 2024-11-30  
> **Status:** ✅ COMPLETE

---

## Summary

Implement client-side Text-to-Speech using the Web Speech API to read Scene Progress narrative aloud. Includes session-level settings modal with voice configuration.

---

## Requirements

1. **Play/Stop button in SceneProgress header**
   - Position: between "N turns" badge and close (✕) button
   - Toggle button: shows ▶ (play) or ■ (stop)
   - Tooltip: "Select text to start reading from that point, or click to read from beginning"
   - Uses "Google UK English Male" voice (with fallback)

2. **Text selection determines start position**
   - If user selects text before clicking Play → start reading from selection
   - If no selection → read from beginning
   - Stop button cancels speech and resets state

3. **Settings modal (triggered from SessionInfoHeader)**
   - Gear icon (⚙) in SessionInfoHeader opens modal overlay
   - Modal contains collapsible/foldable sections for future settings
   - First section: "Storyteller Voice" (or similar creative name)
     - Voice dropdown (populated from speechSynthesis.getVoices())
     - Rate slider (0.5 - 2.0, default 1.0)
     - Pitch slider (0.5 - 2.0, default 1.0)
     - Volume slider (0 - 1.0, default 1.0)
     - Test textarea + play/stop button to preview settings

4. **Persistence**
   - Voice settings saved to localStorage via Pinia store
   - Settings restored on page load

---

## Task Breakdown

| # | Task | Status | Notes |
|---|------|--------|-------|
| T1 | Create `useSpeechSynthesis` composable | ✅ | Core TTS logic |
| T2 | Create `settings` Pinia store | ✅ | Persist voice prefs |
| T3 | Add Play/Stop to `SceneProgress.vue` | ✅ | Header button + tooltip |
| T4 | Create `SessionSettings.vue` modal | ✅ | Overlay with collapsible sections |
| T5 | Add gear icon to `SessionInfoHeader.vue` | ✅ | Emit event for modal |
| T6 | Wire modal in `GameView.vue` | ✅ | State + event handling |
| T7 | Update `HANDOFF_CONTEXT.md` | ✅ | Document changes |

---

## Implementation Details

### T1: useSpeechSynthesis Composable

**File:** `frontend/src/composables/useSpeechSynthesis.ts`

```typescript
// Exports:
// - speak(text: string, startFrom?: number): void
// - stop(): void
// - isSpeaking: Ref<boolean>
// - voices: Ref<SpeechSynthesisVoice[]>
// - selectedVoice: Ref<string>
// - rate: Ref<number>
// - pitch: Ref<number>
// - volume: Ref<number>
// - loadVoices(): void
```

Key features:
- Lazy voice loading (voices load async in some browsers)
- Prefer "Google UK English Male", fallback to first English voice
- Selection-based start: extract text from selection, find offset

### T2: Settings Store

**File:** `frontend/src/stores/settings.ts`

```typescript
// State:
// - voiceName: string
// - rate: number
// - pitch: number
// - volume: number
// Actions:
// - setVoice(name: string)
// - setRate/Pitch/Volume(value: number)
// - loadFromStorage()
// - saveToStorage()
```

### T3: SceneProgress Play/Stop Button

**Location:** Between `.turn-count` and `.btn-close` in `.header-actions`

```vue
<button 
  @click="toggleSpeech" 
  class="btn-speech" 
  :title="speechTooltip"
>
  {{ isSpeaking ? '■' : '▶' }}
</button>
```

Logic:
- On click: get current text selection in `.turns-container`
- If selection exists and is within container, extract start offset
- Call `speak(fullText, startOffset)` or `stop()`

### T4: SessionSettings Modal

**File:** `frontend/src/components/SessionSettings.vue`

Structure:
```
┌─────────────────────────────────────┐
│ ⚙ Session Settings            ✕    │
├─────────────────────────────────────┤
│ ▼ Storyteller Voice                 │
│   ┌─────────────────────────────┐   │
│   │ Voice: [Google UK English ▼]│   │
│   │ Rate:  ────●──────── 1.0    │   │
│   │ Pitch: ────────●──── 1.2    │   │
│   │ Volume:──────────●── 0.8    │   │
│   │                             │   │
│   │ Test: [___________________] │   │
│   │        [▶ Play] [■ Stop]    │   │
│   └─────────────────────────────┘   │
│                                     │
│ ▶ Display Options (collapsed)       │
│ ▶ Notifications (collapsed)         │
└─────────────────────────────────────┘
```

### T5: SessionInfoHeader Gear Icon

Add after `.players-online`:
```vue
<button @click="emit('openSettings')" class="btn-settings" title="Settings">
  ⚙
</button>
```

### T6: GameView Wiring

```typescript
const showSettings = ref(false)
// ... in template:
// <SessionInfoHeader ... @open-settings="showSettings = true" />
// <SessionSettings v-if="showSettings" @close="showSettings = false" />
```

---

## Files to Create/Modify

**Create:**
- `frontend/src/composables/useSpeechSynthesis.ts`
- `frontend/src/stores/settings.ts`
- `frontend/src/components/SessionSettings.vue`

**Modify:**
- `frontend/src/components/SceneProgress.vue`
- `frontend/src/components/SessionInfoHeader.vue`
- `frontend/src/views/GameView.vue`

---

## Success Criteria

- [ ] Play button in SceneProgress reads Keeper's responses aloud
- [ ] Text selection determines where reading starts
- [ ] Stop button cancels speech
- [ ] Gear icon in header opens settings modal
- [ ] Settings modal has collapsible sections
- [ ] Voice/rate/pitch/volume configurable in "Storyteller Voice" section
- [ ] Test area allows previewing voice settings
- [ ] Settings persist across page reloads
- [ ] Fallback to any English voice if Google UK English Male unavailable

---

## Browser Compatibility Notes

- Web Speech API supported in Chrome, Edge, Firefox, Safari
- Voice availability varies by browser/OS
- Google voices only available in Chrome/Chromium
- Need graceful fallback for Firefox/Safari users

---

## Previous Phase (6) - COMPLETED

All Phase 6 tasks completed successfully:

| Task | Status | Commit |
|------|--------|--------|
| T1: Pass existing actions to AI | ✅ | `377e7d9` |
| T2: Clarify appearance → demeanor | ✅ | `f12c6e4` |
| T3: Implement pacing system | ✅ | `e883b60` |
| T4: Shorten DM responses | ✅ | `b65c3eb` |
| T5: Enhance character context | ✅ | `aa332d9` |
- Added _summarize_backstory() to combine key backstory fields (max 300 chars)
- n8n workflow now displays all character background info

---

## Files Modified

**Backend:**
- `backend/app/services/context_assembly.py` - CharacterContext + SceneContext enhancements
- `backend/app/services/llm.py` - Demeanor field handling

**Frontend:**
- `frontend/src/components/SceneActiveTurn.vue` - Demeanor label + pass existing actions

**Workflows:**
- `n8n_workflows/LLM_Synthesizer_SubWF.json` - Enhanced prompts + pacing

---

## Next Steps

Phase 6 is complete. Suggested next phase:

1. **Test the improvements** - Play through several turns to verify:
   - Shorter DM responses
   - Proper pacing progression
   - AI characters knowing other actions
   
2. **Monitor pacing phases** - Verify turn counting works correctly

3. **Consider Phase 7** - Additional improvements:
   - RAG integration for lore context
   - Scene transition automation
   - NPC dialogue enhancements
3. Update AI prompts to correctly interpret this field

**Files:**
- `frontend/src/components/SceneActiveTurn.vue` - rename field, update placeholder
- `backend/app/services/llm.py` - update prompt wording
- `backend/app/models.py` - if field name changes
- Database migration (if renaming field)

**Alternative:** Keep name but fix prompts only (less invasive):
- Update `llm.py` prompt: "Their demeanor/body language (appearance field): ..."

---

### T3: Implement Pacing System
**Priority:** High  
**Effort:** 4-6 hours

**Problem:** Story moves too fast. Horror elements appear immediately.

**Solution:**
1. Add turn tracking to scenes:
   - `scene.turn_count` field
   - Increment on each turn submission
2. Define pacing phases in scene:
   - Turns 1-5: Establishment (mundane only)
   - Turns 6-15: Unease (subtle hints)
   - Turns 16+: Investigation/Revelation
3. Pass pacing phase to LLM Synthesizer
4. Update system prompt with phase-specific rules

**Files:**
- `backend/app/models.py` - add `turn_count` to Scene
- `backend/app/routes_turns.py` - increment turn count on submit
- `n8n_workflows/LLM_Synthesizer_SubWF.json` - update system prompt
- `docs/specifications/DUNGEONMASTER_AGENT.md` - reference

---

### T4: Shorten DM Responses
**Priority:** Medium  
**Effort:** 1-2 hours

**Problem:** Scene descriptions too verbose (500+ words).

**Target:** 150-300 words per response.

**Solution:**
1. Update LLM Synthesizer system prompt:
   - Add explicit word limit
   - Limit to 2-3 sensory details per response
   - Instruct to focus on reaction to player actions
2. Add response length check in backend callback handler
3. Log warning if responses exceed target

**Files:**
- `n8n_workflows/LLM_Synthesizer_SubWF.json`
- `backend/app/routes_ai.py` (callback handler)

---

### T5: Enhance Character Context for DM
**Priority:** High  
**Effort:** 3-4 hours

**Problem:** DM doesn't have good grasp of who characters are.

**Solution:**
1. Expand character data in context bundle:
   - Include occupation, key skills (top 5)
   - Include backstory summary (first 200 chars)
   - Include current HP/Sanity percentages
   - Include character personality notes
2. Format character summaries for LLM prompt
3. Include character relationships if available

**Files:**
- `backend/app/services/context_assembler.py` (or create if needed)
- `backend/app/routes_turns.py` - where context is assembled
- `n8n_workflows/DungeonMaster_Main.json` - prepare LLM input node

---

## Implementation Order

1. **T2** (quick fix) - Clarify appearance field via prompt update
2. **T1** (needed for testing) - Fix AI action context
3. **T5** (improves quality) - Enhance character context
4. **T4** (prompt tuning) - Shorten responses
5. **T3** (larger refactor) - Implement pacing system

---

## Success Criteria

- [ ] AI character actions reference what other characters are doing
- [ ] "Appearance" field correctly interpreted as demeanor/body language
- [ ] DM responses are 150-300 words on average
- [ ] No supernatural elements before turn 10
- [ ] DM addresses characters by name and acknowledges their expertise
- [ ] Turn count visible in scene data

---

## Notes

- Pacing rules should be configurable per campaign (some may want faster pace)
- Consider adding "pacing_override" flag for game masters
- Track response lengths for quality monitoring
