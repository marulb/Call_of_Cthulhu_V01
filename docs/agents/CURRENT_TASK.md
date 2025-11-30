# Current Task: DungeonMaster Agent Improvements

> **Phase:** 6 - DungeonMaster Refinement  
> **Created:** 2024-11-30  
> **Updated:** 2024-11-30  
> **Status:** ✅ COMPLETE  
> **Specification:** `docs/specifications/DUNGEONMASTER_AGENT.md`

---

## Summary

All Phase 6 tasks completed successfully:

| Task | Status | Commit |
|------|--------|--------|
| T1: Pass existing actions to AI | ✅ | `377e7d9` |
| T2: Clarify appearance → demeanor | ✅ | `f12c6e4` |
| T3: Implement pacing system | ✅ | `e883b60` |
| T4: Shorten DM responses | ✅ | `b65c3eb` |
| T5: Enhance character context | ✅ | `aa332d9` |

---

## Completed Tasks

### T1: Fix AI Character Action Context ✅
- Frontend passes `existing_actions` from activeTurnList to AI generation
- AI now knows what other characters are doing this turn

### T2: Clarify "Appearance" Field ✅
- Renamed field label to "Demeanor" 
- Updated placeholder: "Posture, body language, visible emotions..."
- LLM prompt now explains field meaning clearly

### T3: Implement Pacing System ✅
- Added `turn_count` and `pacing_phase` to SceneContext
- Backend counts completed turns per scene
- Phase detection: establishment (1-5), unease (6-15), investigation (16-35), revelation (36-45), resolution (46+)
- n8n workflow passes pacing info to LLM

### T4: Shorten DM Responses ✅
- Added RESPONSE LENGTH section to DM prompt (150-300 words)
- Added PACING guidance for slow horror buildup
- Reduced num_predict from 1000 to 600 tokens
- Updated narrative requirement to "1-3 paragraphs"

### T5: Enhance Character Context ✅
- Added to CharacterContext: pronoun, birthplace, residence, backstory
- Fixed collection: db.characters → db.entities (kind: "pc")
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
