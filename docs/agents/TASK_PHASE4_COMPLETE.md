# Phase 4: Story Flow, AI Agents & Realm Setup

> **Status:** Planning → Discussion → Implementation  
> **Created:** 2025-11-29  
> **Priority:** High  
> **Type:** Major Feature Set

---

## Executive Summary

Transform the game from "LLM responds to actions" to a **structured narrative system** with:
1. Realm/Campaign setup with AI-generated story arcs
2. Automatic scene/chapter transitions with summarization
3. AI-controlled characters (player-owned) and NPCs (keeper-controlled)
4. Specialized agents for different tasks (Keeper, NPC Agent, Rules Agent)

---

## Core Concepts

### The Keeper's Role
The Keeper is a **scene narrator**, NOT an actor. It:
- Describes environments, atmosphere, consequences
- Guides story toward campaign milestones
- Triggers scene/chapter transitions
- Delegates to specialized agents (NPC Agent, Rules Agent)
- **NEVER speaks or acts for player characters**

### Agent Hierarchy
```
┌─────────────────────────────────────────────────────────┐
│                      KEEPER AGENT                        │
│  - Scene descriptions                                    │
│  - Story progression toward milestones                   │
│  - Transition detection (scene/chapter)                  │
│  - Orchestrates other agents                             │
└─────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   NPC AGENT     │  │  RULES AGENT    │  │ AI PLAYER AGENT │
│ - NPC dialogue  │  │ - Skill checks  │  │ - Generate acts │
│ - NPC actions   │  │ - Combat rules  │  │ - for AI chars  │
│ - Personality   │  │ - Sanity loss   │  │ - based on      │
│   consistency   │  │ - Damage calc   │  │   personality   │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### Character Controller Modes
From DATA_MODEL.md:
```json
"controller": {
  "owner": "player-alice",    // Who owns/manages this character
  "mode": "player|ai|keeper", // Current control mode
  "agent": "human|npc-agent|ai-player-agent"  // Which agent controls
}
```

- **player + human**: Normal player character
- **ai + ai-player-agent**: AI plays this character (owned by a player)
- **keeper + npc-agent**: NPC controlled by Keeper via NPC Agent

---

## Milestone 1: Realm & Campaign Setup

### 1.1 Realm Creation Enhancement

**Current State:** Realm has `setting.tone` and `setting.notes` but no UI to set them.

**Required:**
```json
// Realm setting (enhanced)
{
  "setting": {
    "tone": "dark, creeping dread",           // Mood for all campaigns
    "era": "1920s",                           // Time period
    "location": "New England, USA",           // Geographic setting
    "themes": ["cosmic horror", "isolation"], // Recurring themes
    "notes": "Resource scarcity; occult undertones"
  }
}
```

**Implementation:**
- [ ] Frontend: Add realm settings form on login/realm selection screen
- [ ] Backend: Ensure realm creation accepts setting fields
- [ ] Optional: LLM generates setting suggestions based on "Call of Cthulhu"

### 1.2 Campaign Creation with AI Story Arc

**Flow:**
1. User provides: Campaign name + brief concept (1-2 sentences)
2. LLM generates:
   - `story_arc.tagline` - One-liner
   - `story_arc.beginning` - Starting situation
   - `story_arc.ending` - Victory/resolution condition
   - `story_arc.milestones[]` - 3-5 key plot points
   - `setting.goal` - What players are trying to achieve
   - `setting.key_elements[]` - Important NPCs, locations, artifacts

**Schema Update:**
```json
{
  "id": "campaign-xxx",
  "story_arc": {
    "tagline": "Recovering the fragments of a shattered sun relic.",
    "beginning": "Players receive a cryptic letter summoning them to Arkham.",
    "ending": "Stop the cult from reassembling the Shattered Sun.",
    "milestones": [
      { "order": 1, "name": "The Letter", "description": "Receive mysterious invitation", "completed": false },
      { "order": 2, "name": "First Fragment", "description": "Locate fragment in university library", "completed": false },
      { "order": 3, "name": "The Cult Revealed", "description": "Discover the Order of the Shattered Sun", "completed": false },
      { "order": 4, "name": "Race Against Time", "description": "Prevent ritual at the lighthouse", "completed": false },
      { "order": 5, "name": "Final Confrontation", "description": "Stop the High Priest", "completed": false }
    ],
    "current_milestone": 1
  },
  "setting": {
    "tone": "paranoid investigation",
    "starting_point": "Arkham train station, autumn 1923",
    "goal": "Prevent the ritual that will awaken the Shattered Sun",
    "key_elements": ["Miskatonic University", "Order of the Shattered Sun", "Prof. Armitage"],
    "key_npcs": ["npc-armitage", "npc-cultist-leader"],
    "key_locations": ["loc-university", "loc-lighthouse"]
  }
}
```

**Implementation:**
- [ ] Backend: New endpoint `POST /api/v1/campaigns/generate-arc`
- [ ] n8n: New workflow "Campaign Arc Generator" using LLM
- [ ] Frontend: Campaign creation wizard with concept input
- [ ] Frontend: Display milestones in game view (progress tracker)

---

## Milestone 2: Automatic Scene/Chapter Summarization

### 2.1 Scene Lifecycle

```
Scene Status Flow:
┌──────────┐    ┌────────────┐    ┌───────────┐
│  active  │ →  │ completing │ →  │ completed │
└──────────┘    └────────────┘    └───────────┘
                     │
                     ▼
              Generate summary
              from all turns
```

**When Scene Ends:**
1. Keeper detects transition (location change, time skip, dramatic event)
2. Backend receives transition signal in callback
3. Backend calls "Summarizer Agent" with all turns in scene
4. Summarizer generates `scene.summary` (2-3 sentences)
5. New scene created with:
   - Link to previous scene
   - Last turn context
   - Previous scene summary
6. Old scene marked `completed`

**Scene Summary Schema:**
```json
{
  "id": "scene-xxx",
  "status": "completed",
  "summary": "The investigators discovered a hidden passage behind the bookshelf in the archive. After a tense encounter with the archivist, they found the first fragment wrapped in strange cloth.",
  "discoveries": ["hidden passage", "first fragment"],
  "npcs_encountered": ["npc-archivist"],
  "next_scene_id": "scene-yyy"
}
```

### 2.2 Chapter Lifecycle

Same pattern, one level up:

**When Chapter Ends:**
1. Keeper detects major transition (new location/city, major time skip, story milestone)
2. Backend calls Summarizer with all scene summaries in chapter
3. Chapter summary generated (1 paragraph)
4. New chapter created
5. Old chapter marked `completed`

**Chapter Summary Schema:**
```json
{
  "id": "chapter-xxx",
  "status": "completed",
  "summary": "The investigators arrived in Arkham and began their search for the Shattered Sun fragments. They discovered the first fragment in the university library and learned of the Order's existence. Professor Armitage became a reluctant ally.",
  "key_events": ["Found first fragment", "Met Prof. Armitage", "Cult attack at library"],
  "milestone_reached": "First Fragment",
  "next_chapter_id": "chapter-yyy"
}
```

### 2.3 Context for New Scene/Chapter

**New Scene Receives:**
```json
{
  "previous_scene_summary": "...",
  "last_turn_reaction": "...",
  "active_npcs": [...],
  "campaign_milestones": [...],
  "current_milestone": 2
}
```

**New Chapter Receives:**
```json
{
  "previous_chapter_summary": "...",
  "campaign_story_arc": {...},
  "milestones_completed": [...],
  "next_milestone": {...}
}
```

---

## Milestone 3: AI-Controlled Characters

### 3.1 AI Player Characters

**Ownership Model:**
- AI character is **owned by a human player**
- Owner can provide `action` hints for the AI
- AI generates full action based on:
  - Character personality/traits
  - Scene context
  - Owner's action hint (if provided)
  - Other players' actions

**Flow:**
```
1. Scene turn starts
2. Human players write their actions
3. Owner of AI character optionally adds "action hint":
   { "actor_id": "char-ai-bob", "hint": "Bob should be suspicious of the archivist" }
4. When turn submitted, AI Player Agent generates:
   { "speak": "I don't trust this archivist...", 
     "act": "Positions himself near the exit",
     "emotion": "wary" }
5. AI action added to turn alongside human actions
6. Turn proceeds to Keeper
```

**Character Schema Addition:**
```json
{
  "controller": {
    "owner": "player-alice",
    "mode": "ai",
    "agent": "ai-player-agent"
  },
  "ai_personality": {
    "traits": ["suspicious", "protective", "veteran"],
    "goals": ["protect the group", "find his missing brother"],
    "behavior_style": "cautious",
    "speech_style": "terse, military background"
  }
}
```

### 3.2 NPCs (Keeper-Controlled)

**Different from AI Characters:**
- NPCs don't have full character sheets
- NPCs are controlled by Keeper via NPC Agent
- NPCs appear in Keeper's narrative, not in action list
- NPCs have personality, knowledge, secrets

**NPC Schema (already in DATA_MODEL):**
```json
{
  "id": "npc-archivist",
  "kind": "npc",
  "name": "Keeper of the Dunes",
  "realm_id": "realm-xxx",
  "controller": { 
    "owner": "keeper", 
    "mode": "keeper", 
    "agent": "npc-agent" 
  },
  "data": {
    "personality": ["suspicious", "curious", "secretive"],
    "knowledge": ["knows fragment location", "fears the cult"],
    "secrets": ["is former cult member"],
    "voice_style": "dry, old, slightly tired",
    "current_disposition": "neutral"
  }
}
```

**NPC in Scene Flow:**
1. Scene has `participants: ["char-alice", "char-bob", "npc-archivist"]`
2. When Keeper generates narrative, it knows NPC is present
3. Keeper can request NPC Agent to generate dialogue
4. NPC dialogue woven into Keeper's scene description

---

## Milestone 4: Specialized Agents

### 4.1 Agent Architecture

| Agent | Trigger | Input | Output |
|-------|---------|-------|--------|
| **Keeper** | Turn submitted | Actions, context, NPCs | Scene description, transition signal |
| **NPC Agent** | Keeper request | NPC data, scene context, player actions | NPC dialogue/reaction |
| **Rules Agent** | Skill check needed | Check type, character stats | Roll result, interpretation |
| **AI Player Agent** | Turn with AI char | Character data, scene, hint | Character action |
| **Summarizer** | Scene/Chapter ends | Turns/Scenes | Summary text |
| **Campaign Generator** | Campaign created | User concept | Story arc, milestones |

### 4.2 Implementation Priority

1. **Keeper** - Already exists, needs refinement
2. **Summarizer** - Critical for scene flow
3. **Campaign Generator** - Enhances setup
4. **AI Player Agent** - Nice to have
5. **NPC Agent** - Can be simplified into Keeper initially
6. **Rules Agent** - Already partially exists in skill_check service

---

## Milestone 5: Frontend Fixes & Enhancements

### 5.1 Bug Fixes (HIGH PRIORITY)

| Bug | Location | Symptom | Likely Cause |
|-----|----------|---------|--------------|
| Character sheet closes | CharacterSheet component | Closes after ~1s | State reset or auto-close timer |
| Combat section collapses | Combat editing | Collapses on keystroke | Input triggers parent state change |
| Relationships collapses | Relationships editing | Same as combat | Same pattern |

**Investigation Steps:**
1. Check for `setTimeout` or auto-close logic
2. Check if input `onChange` triggers component re-render
3. Check if expanded/collapsed state is tied to data changes

### 5.2 Realm Setup UI

- [ ] Add realm settings form (tone, era, themes)
- [ ] Display realm settings in game view header

### 5.3 Campaign Setup UI

- [ ] Campaign creation wizard
- [ ] "Generate story arc" button
- [ ] Milestone tracker in game view

### 5.4 AI Character Support

- [ ] Visual indicator for AI-controlled characters
- [ ] "Action hint" input for AI characters
- [ ] AI action display in turn

---

## Implementation Order

### Phase 4.1: Foundation (Estimated: 1-2 sessions)
1. [ ] Fix frontend bugs (character sheet, combat, relationships)
2. [ ] Add realm settings to creation flow
3. [ ] Enhance context assembly with previous turn summaries

### Phase 4.2: Summarization (Estimated: 1-2 sessions)
1. [ ] Create Summarizer agent/prompt
2. [ ] Implement scene summarization on transition
3. [ ] Implement chapter summarization
4. [ ] Update Keeper prompt to receive summaries

### Phase 4.3: Campaign Arc (Estimated: 1 session)
1. [ ] Create Campaign Generator agent
2. [ ] Add milestone schema to campaigns
3. [ ] Campaign creation wizard in frontend
4. [ ] Milestone tracker in game view

### Phase 4.4: AI Characters (Estimated: 2 sessions)
1. [ ] Update character schema with controller modes
2. [ ] Create AI Player Agent
3. [ ] Frontend support for AI action hints
4. [ ] NPC presence in scenes

---

## Questions for Discussion

1. **Summarization Timing:**
   - After every turn (incremental)?
   - Only when scene ends?
   - Background job vs inline?

2. **Milestone Progression:**
   - Auto-detect from narrative?
   - Keeper explicitly signals?
   - Human GM confirms?

3. **AI Character Turns:**
   - Generate with human turns (simultaneous)?
   - Generate after humans submit (sequential)?
   - Owner must trigger generation?

4. **NPC Complexity:**
   - Start simple (name + personality in Keeper prompt)?
   - Full NPC Agent from start?

5. **Chat Participation (AI):**
   - AI characters listen to realm chat?
   - Can respond autonomously?
   - Owner moderation?

---

## Files to Create/Modify

### New Files
- `backend/app/services/summarizer.py` - Summarization logic
- `backend/app/routes_npcs.py` - NPC CRUD
- `n8n_workflows/Summarizer_SubWF.json` - Summary generation
- `n8n_workflows/Campaign_Generator.json` - Arc generation
- `n8n_workflows/AI_Player_Agent.json` - AI character actions

### Modify
- `backend/app/services/context_assembly.py` - Add summaries to context
- `backend/app/models.py` - Campaign milestones, NPC model
- `backend/app/routes_campaigns.py` - Arc generation endpoint
- `backend/app/routes_turns.py` - AI character support
- `n8n_workflows/LLM_Synthesizer_SubWF.json` - Updated prompts
- `frontend/src/components/CharacterSheet*.vue` - Bug fixes
- `frontend/src/views/GameView.vue` - Milestone tracker, AI chars

---

## Change Log

| Date | Agent | Changes |
|------|-------|---------|
| 2025-11-29 | Copilot | Initial comprehensive task document |
