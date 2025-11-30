# Current Task: DungeonMaster Agent Improvements

> **Phase:** 6 - DungeonMaster Refinement  
> **Created:** 2024-11-30  
> **Priority:** High  
> **Specification:** `docs/specifications/DUNGEONMASTER_AGENT.md`

---

## Context

After testing the AI action generation and DungeonMaster response system, several issues were identified:

1. **AI Turn Generation** doesn't know about other characters' actions in the current turn
2. **"Appearance" field** is misunderstood by AI (interprets as age/clothing, should be body language/demeanor)
3. **Story pacing is too fast** - cosmic horror appears in turn 1 instead of slow build
4. **Scene descriptions too long** - should be 50-70% shorter
5. **DM lacks character awareness** - doesn't seem to know the characters well

---

## Tasks

### T1: Fix AI Character Action Context
**Priority:** High  
**Effort:** 2-3 hours

**Problem:** When generating an AI character's action, the LLM doesn't see what other characters are doing this turn.

**Solution:**
1. Modify `backend/app/routes_ai.py` `generate_ai_character_action()`:
   - Accept `existing_actions: list` in request (already in schema)
   - Include these in the LLM prompt as "Other characters this turn are..."
2. Modify `frontend/src/components/SceneActiveTurn.vue`:
   - Pass `actionDrafts` to the `generateAIAction` call
   - Filter to only include ready/submitted actions

**Files:**
- `backend/app/routes_ai.py`
- `backend/app/services/llm.py` 
- `frontend/src/components/SceneActiveTurn.vue`
- `frontend/src/services/api.ts`

---

### T2: Clarify "Appearance" Field
**Priority:** Medium  
**Effort:** 1-2 hours

**Problem:** AI interprets "appearance" as physical description (age, hair, clothing).

**Correct meaning:** What others can OBSERVE right now:
- Body language (tense shoulders, relaxed pose)
- Micro-expressions (forced smile, furrowed brow)
- Observable state (sweating, trembling, pale)
- Presentation choices (standing protectively, leaning in)

**Solution:**
1. Rename field from `appearance` to `demeanor` or `visible_state`
2. Update placeholder text to clarify meaning
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
