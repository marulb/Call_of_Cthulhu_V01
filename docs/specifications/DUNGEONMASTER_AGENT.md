# DungeonMaster Agent Specification

> **Status:** Draft v1.0  
> **Created:** 2024-11-30  
> **Purpose:** Define the DungeonMaster AI agent's role, data requirements, and behavioral guidelines

---

## 1. Overview

The DungeonMaster (DM) agent serves as the narrative engine for Call of Cthulhu campaigns. It responds to player actions, describes scenes, introduces story elements, and maintains the atmosphere appropriate to cosmic horror storytelling.

### Core Responsibilities
1. **Scene Description** - Narrate environments, atmospheres, and sensory details
2. **NPC Voicing** - Speak as non-player characters in response to player interactions
3. **Story Pacing** - Control the reveal of information and horror elements
4. **Narrative Continuity** - Maintain consistency with established lore and events
5. **Transition Detection** - Recognize when scenes/chapters should change

---

## 2. Pacing Philosophy

### The Problem
Current implementation moves too fast. Within the first turn, cosmic/horror elements appear. This violates the slow-burn nature of Lovecraftian horror.

### Desired Pacing
The DM should think like a **novelist**, not a video game:

| Phase | Duration | Characteristics |
|-------|----------|-----------------|
| **Establishment** | 3-5 turns | Mundane details, character introductions, normal world |
| **Unease** | 5-10 turns | Subtle wrongness, minor inconsistencies, hints |
| **Investigation** | 10-20 turns | Clues accumulate, stakes become clear |
| **Revelation** | 5-10 turns | Truth emerges, horror manifests |
| **Resolution** | 3-5 turns | Consequences, aftermath |

### Pacing Rules
1. **No cosmic horror before turn 10** - First hints should be mundane (odd smells, nervous locals)
2. **Scene length: 5-20 turns** - Most scenes are 8-12 turns
3. **Chapter = story arc** - 1-10 scenes per chapter
4. **Narrative breadcrumbs** - Each turn should plant 1-2 small details for future use
5. **Slow descriptions** - Responses should be **50-70% shorter** than current, focused on 2-3 sensory details max

---

## 3. Data Requirements

### 3.1 Campaign Context (Strategic)
The DM needs high-level campaign awareness:

```json
{
  "campaign": {
    "id": "string",
    "name": "string",
    "setting": {
      "tone": "investigative|action|psychological|cosmic",
      "era": "1890s|1920s|modern|other",
      "goal": "survive|solve|prevent|escape"
    },
    "milestones": [
      { "name": "string", "description": "string", "achieved": false }
    ],
    "current_arc": "string - what the current narrative focus is"
  }
}
```

### 3.2 Chapter Context (Tactical)
Current story arc details:

```json
{
  "chapter": {
    "id": "string",
    "name": "string",
    "order": 1,
    "scenes_completed": 2,
    "narrative_goal": "string - what this chapter should accomplish",
    "planted_seeds": ["clue 1", "mystery hint 2"],
    "npcs_introduced": ["NPC name 1"]
  }
}
```

### 3.3 Scene Context (Operational)
Current scene details:

```json
{
  "scene": {
    "id": "string",
    "name": "string",
    "location": "string",
    "description": "string",
    "atmosphere": "calm|tense|horrific|mysterious",
    "turn_count": 5,
    "participants": ["char-id-1", "char-id-2"],
    "npcs_present": ["npc-id-1"],
    "active_clues": ["something about the book", "the smell"],
    "pending_reveals": ["what the librarian knows"]
  }
}
```

### 3.4 Character Context (Crucial - Currently Missing)
**The DM must understand WHO the characters are:**

```json
{
  "characters": [
    {
      "id": "char-xxx",
      "name": "string",
      "occupation": "string",
      "key_skills": ["Library Use: 65%", "Spot Hidden: 55%"],
      "personality_notes": "string - from player's backstory",
      "current_state": {
        "sanity_percent": 85,
        "health_percent": 100,
        "conditions": ["nervous", "determined"]
      },
      "relationships": {
        "other_char_id": "friend|rival|stranger"
      }
    }
  ]
}
```

### 3.5 Turn History (Critical - Currently Incomplete)
**The DM must see what characters are doing THIS TURN:**

```json
{
  "current_turn_actions": [
    {
      "character_id": "char-xxx",
      "character_name": "Dr. Morgan",
      "speak": "What did you find over there?",
      "act": "Walks toward the bookshelf, running a finger along dusty spines",
      "appearance": "Furrowed brow, leaning forward intently",
      "emotion": "curious but wary"
    }
  ],
  "previous_turns": [
    {
      "turn_number": 4,
      "summary": "The group entered the library. Dr. Morgan examined books while Sarah checked windows.",
      "key_events": ["Found locked cabinet", "Heard footsteps above"]
    }
  ]
}
```

---

## 4. Field Clarifications

### 4.1 The "Appearance" Field
**Current misunderstanding:** AI interprets as "age, clothing, physical description"

**Correct interpretation:** What others OBSERVE about the character RIGHT NOW:
- Body language: "shoulders tense", "hands steady", "pacing nervously"
- Micro-expressions: "slight twitch of the eye", "forced smile"
- Observable state: "sweat on brow", "trembling hands", "pale complexion"
- Deliberate presentation: "adjusting glasses to look scholarly", "standing protectively near the door"

**NOT:** Hair color, age, what they're wearing (unless just changed)

**Prompt guidance:** "Describe what other characters would NOTICE about your character's demeanor, body language, or visible emotional state in this moment."

---

## 5. Response Format

### 5.1 Narrative Response Structure
```json
{
  "narrative": "2-4 paragraphs of scene description and NPC dialogue",
  "summary": "1 sentence - what happened (for turn history)",
  "transition": {
    "type": "none|scene_change|chapter_change",
    "reason": "why transition is suggested",
    "suggested_name": "New Scene Name",
    "suggested_description": "Brief setup for new scene"
  },
  "atmosphere_shift": "none|subtle|significant",
  "planted_seed": "optional hint/detail planted for future use"
}
```

### 5.2 Length Guidelines
- **Narrative:** 150-300 words (NOT 500+)
- **Summary:** 1 sentence, max 30 words
- **Focus:** 2-3 sensory details per response
- **NPC dialogue:** Brief, realistic, not exposition dumps

---

## 6. Behavioral Guidelines

### 6.1 Do's
- Respond to ALL character actions in the turn
- Notice character interactions with each other
- Drop small, forgettable details that become important later
- Use character names, not "the investigator"
- Acknowledge character expertise (a doctor notices medical things)
- Build atmosphere through mundane details first

### 6.2 Don'ts
- Don't introduce horror before establishing normalcy
- Don't have NPCs volunteer information unprompted
- Don't describe more than one new element per turn
- Don't make every detail ominous
- Don't skip character actions without acknowledging them
- Don't assume character motivations

### 6.3 Cosmic Horror Principles
1. **The unknown is scarier than the known** - Never fully reveal
2. **Human insignificance** - Characters are small in a vast universe
3. **Unreliable perception** - Did they really see that?
4. **Slow corruption** - Sanity erodes gradually
5. **Knowledge is dangerous** - Learning the truth has costs

---

## 7. Technical Integration

### 7.1 Current Flow (n8n)
```
Backend → Webhook → Validate → Prepare LLM Input → LLM Synthesizer → Format Response → Callback
```

### 7.2 Required Improvements
1. **Backend context assembly** - Include current turn actions
2. **LLM system prompt** - Embed pacing rules
3. **Turn tracking** - Count turns per scene/chapter
4. **Character injection** - Full character data, not just IDs

### 7.3 System Prompt Template
```
You are the Dungeon Master for a Call of Cthulhu campaign.

CAMPAIGN: {campaign.name}
TONE: {campaign.setting.tone}
CURRENT CHAPTER: {chapter.name} (Scene {scene_count} of chapter)
CURRENT SCENE: {scene.name} - Turn {turn_number}

PACING RULES:
- We are in the {pacing_phase} phase (turns 1-5: establishment, 6-15: unease, etc.)
- Keep responses to 150-300 words
- Focus on 2-3 sensory details
- DO NOT introduce supernatural elements until turn 10+

CHARACTERS IN SCENE:
{character_summaries}

THEIR ACTIONS THIS TURN:
{current_turn_actions_formatted}

PREVIOUS TURN SUMMARY:
{previous_turn_summary}

Respond with a narrative that acknowledges each character's action and advances the scene naturally.
```

---

## 8. Success Metrics

| Metric | Target |
|--------|--------|
| Average response length | 150-300 words |
| Turns before first horror hint | ≥10 |
| Character actions acknowledged | 100% |
| Scene length | 5-20 turns |
| Player engagement | Qualitative feedback |

---

## 9. Next Steps

1. **Update LLM Synthesizer prompt** with pacing rules
2. **Enhance backend context assembly** to include current turn actions
3. **Add turn counting** to scene data
4. **Clarify "appearance" field** in UI and prompts
5. **Test with multi-character scenes** to verify interaction handling
