# Phase 5: UI/UX Improvements & AI Character Integration

> **Created:** 2025-11-29
> **Status:** Active
> **Priority:** High

---

## Task Summary

| ID | Task | Priority | Difficulty | Status |
|----|------|----------|------------|--------|
| P5-1 | Player name case sensitivity | Medium | � Easy | ✅ Done |
| P5-2 | AI checkbox/dropdown styling | Low | � Easy | ✅ Done |
| P5-3 | Action ready/edit toggle (✓/✗) | High | 🟡 Medium | ✅ Done |
| P5-4 | AI Character action generation | High | � Complex | �🟡 In Progress (Claude Code) |
| P5-5 | Automatic character creation | - | 🔴 Complex | ⏸️ DEFERRED |

---

## P5-1: Player Name Case Sensitivity

**Problem:** Player names are case-sensitive but this only becomes evident at character selection screen (confusing UX).

**Solution Options:**
1. Normalize player names to lowercase on login
2. Show existing player names as suggestions on login
3. Display warning if similar name exists with different case

**Files:** `frontend/src/views/LoginView.vue`, possibly backend validation

---

## P5-2: AI Checkbox/Dropdown Styling

**Problem:** The "AI Controlled" checkbox and "AI Personality" dropdown in CharacterSheet look different from other form elements.

**Solution:** Apply consistent styling to match other form fields in the character sheet.

**Files:** `frontend/src/components/CharacterSheetForm.vue`

---

## P5-3: Action Ready/Edit Toggle (✓/✗ Buttons)

**Problem:** Current action UI has "Create Action" and "Cancel" buttons, but actions can't be edited once created.

**Proposed Solution:**
- Remove "Create Action" and "Cancel" buttons
- Add **✓** (check) and **✗** (remove) buttons per action
- **✓** toggles between:
  - **Ready state** (non-editable, darker green background)
  - **Edit state** (editable, lighter green background)
- **✗** removes the action entirely
- Visual feedback: color change on toggle

**Behavior:**
```
[Edit Mode]     →  Click ✓  →  [Ready Mode]
(light green)                   (darker green, non-editable)
    ↑                                ↓
    └──────── Click ✓ ────────────────┘
```

**Files:** `frontend/src/components/SceneActiveTurn.vue`

---

## P5-4: AI Character Action Generation

**Problem:** AI-controlled characters don't automatically generate actions; the `ai_controlled` flag isn't being stored properly.

### Sub-tasks:

#### P5-4a: Fix AI Character Storage
- Verify `ai_controlled` and `ai_personality` are saved to MongoDB
- Check character update route handles these fields

#### P5-4b: AI Action Generation Button
**Option A - In Active Turn List:**
- Add **⋆˙⟡** (sparkle) button next to AI character actions
- Clicking triggers LLM to generate actions for that character
- Actions are inserted at the character's position in the turn

**Option B - In Players List:**
- Add **⋆˙⟡** next to AI character names in player list
- Clicking generates actions and adds to active turn

**Option C - Both approaches** (recommended)

#### P5-4c: Auto-trigger Warning/Generation
When submitting active turn:
- Check if AI characters are present but have no actions
- Either:
  - Show warning: "AI characters have no actions. Generate automatically?"
  - Auto-generate actions before submission

**Files:**
- `frontend/src/components/SceneActiveTurn.vue`
- `frontend/src/components/PlayersList.vue`
- `backend/app/services/llm.py` (new method: `generate_character_actions`)
- `backend/app/routes_ai.py` (new endpoint)

---

## P5-5: Automatic Character Creation

> ⏸️ **DEFERRED - TO BE DEFINED LATER**

**Concept:** During character creation, player can click "Automatic" to have stats filled according to Call of Cthulhu rules.

**Considerations:**
- Which edition's rules? (7th edition recommended)
- Random vs point-buy generation
- Which fields to auto-generate (attributes, skills, backstory?)
- Integration with existing character sheet structure

**Dependencies:** Requires detailed specification of CoC character creation rules.

**Status:** Awaiting user requirements definition.

---

## Implementation Order (Recommended)

1. **P5-4a** - Fix AI storage (quick fix, unblocks P5-4)
2. **P5-2** - AI styling (quick fix)
3. **P5-3** - Action toggle buttons (medium effort, improves UX)
4. **P5-4b/c** - AI action generation (larger feature)
5. **P5-1** - Player name handling (quality of life)

---

## Technical Notes

### AI Action Generation Flow
```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Click ⋆˙⟡ on   │────▶│ POST /api/v1/ai/ │────▶│ LLMService.     │
│ AI character    │     │ generate-action  │     │ generate_action │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                         │
                                                         ▼
                                               ┌─────────────────┐
                                               │ Return action   │
                                               │ {speak, act,    │
                                               │  emotion, ...}  │
                                               └─────────────────┘
```

### LLM Prompt for AI Action
```
Character: {name}
Personality: {ai_personality}
Current Scene: {scene context}
Previous Actions: {other character actions this turn}

Generate an action for this character that fits their personality.
Return JSON: {"speak": "...", "act": "...", "emotion": "..."}
```
