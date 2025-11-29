# Narration and setting elements

## Worlds
Represents the lore and rule set for the game.
```json
{
  "id": "sphere-cthulhu",
  "kind": "world",
  "name": "Cthulhu",
  "ruleset": "Call of Cthulhu 7th Edition",
  "meta": {
    "created_by": "GMName",
    "created_at": "2025-11-01T10:00:00Z"
  },
  "changes": [
    { "by": "GMName", "at": "2025-11-01T10:00:00Z" }
  ]
}
```

## Realms
Represents a specific group of players within a world. Realms now explicitly list active `campaigns`.
```json
{
  "id": "fragment-cthulhu",
  "kind": "realm",
  "world_id": "sphere-cthulhu",
  "name": "Cthulhu – Day of the Tentacle",
  "players": [
    { "id": "player-alice", "name": "Alice" },
    { "id": "player-bob", "name": "Bob" }
  ],
  "characters": ["char-alice-1", "char-bob-1"],
  "campaigns": ["camp-shards"],
  "meta": {
    "created_by": "player-alice",
    "created_at": "2025-11-01T10:00:00Z"
  },
  "changes": [
    { "by": "player-alice", "at": "2025-11-01T10:00:00Z" }
  ],
  "setting": {
    "tone": "dark, creeping dread",
    "notes": "Resource scarcity; occult undertones"
  }
}
```

## Campaigns
Represents a story arc within a realm. `story_arc.acts` has been renamed to `story_arc.chapters` and includes a `tagline`.
```json
{
  "id": "camp-shards",
  "kind": "campaign",
  "realm_id": "fragment-cthulhu",
  "name": "Shards of the Sun",
  "status": "running",
  "story_arc": {
    "tagline": "Recovering the fragments of a shattered sun relic.",
    "chapters": ["chap-oasis-village", "chap-confrontation"]
  },
  "setting": {
    "tone": "very hostile environment",
    "starting_point": "A ruined port where fragments wash ashore",
    "goal": "Recover the major fragments and secure the relic",
    "story_elements": ["mystery fragments", "hostile cultists", "decaying technology"],
    "key_elements": ["Dune Archive", "Sun Shard", "Archivist NPC"]
  },
  "changes": [
    { "by": "player-alice", "at": "2025-11-01T10:00:00Z" }
  ]
}
```

## Chapters
Represents sub-story arcs within a campaign.
```json
{
  "id": "chap-oasis-village",
  "kind": "chapter",
  "campaign_id": "camp-shards",
  "name": "The Secret of the Oasis Village",
  "order": 1,
  "scenes": ["scene-dune-archive", "scene-another-scene"],
  "summary": "The party arrives at the oasis village and discovers clues about the lost fragment.",
  "changes": [
    { "by": "player-alice", "at": "2025-11-01T10:00:00Z" }
  ]
}
```

## Scenes
Represents individual scenes within a chapter. Scene belongs to a Chapter only - campaign and realm can be derived by traversing chapter_id → campaign_id → realm_id.
```json
{
  "id": "scene-dune-archive",
  "kind": "scene",
  "chapter_id": "chap-oasis-village",
  "name": "Dune Archive",
  "location_id": "loc-archive-building",
  "status": "in_progress",
  "participants": ["char-alice-1", "char-bob-1", "npc-archivist-77"],
  "turns": ["turn-001", "turn-002"],
  "summary": "The party enters the dune archive and starts investigating the lost fragment.",
  "changes": [
    { "by": "player-alice", "at": "2025-11-01T10:00:00Z" }
  ]
}
```

## Turns
Represents individual turns within a scene. Turn structure: `actions` (character actions submitted by players) → `reaction` (scene description/narrative output from orchestrator agent).
```json
{
  "id": "turn-001",
  "kind": "turn",
  "session_id": "sess-2025-11-22",
  "scene_id": "scene-dune-archive",
  "order": 1,
  "status": "ready_for_agents",
  "actions": [
    {
      "actor_id": "char-alice-1",
      "controller_owner": "player-alice",
      "speak": "I ask the archivist about the lost fragment.",
      "act": "Steps closer to the desk.",
      "appearance": "Tense but polite.",
      "emotion": "curious, cautiously optimistic",
      "ooc": null,
      "meta": {
        "ready": true,
        "resolved": false
      }
    },
    {
      "actor_id": "char-bob-1",
      "controller_owner": "player-bob",
      "speak": null,
      "act": "Scans the room for hidden doors.",
      "appearance": "Suspicious, eyes darting.",
      "emotion": "uneasy",
      "ooc": "I want to roll Perception.",
      "meta": {
        "ready": true,
        "resolved": false
      }
    }
  ],
  "reaction": {
    "description": "The archivist looks up from dusty tomes, eyes narrowing with suspicion. 'The fragment you seek... many have asked. Few have left.' Meanwhile, Bob notices a faint draft coming from behind a bookshelf.",
    "rules_applied": ["Perception check: Success"],
    "narrative_summary": "Party engages archivist; Bob discovers hidden passage."
  },
  "agent_result": {
    "rules_summary": null,
    "narrative_summary": null
  },
  "changes": [
    { "by": "player-alice", "at": "2025-11-01T10:00:00Z" }
  ]
}
```

## Sessions
Represents individual game sessions - a play instance independent of the narrative hierarchy. Sessions track who played, when, and which story elements were active. Sessions reference realm and campaign for context but are not part of the World→Realm→Campaign→Chapter→Scene hierarchy.
```json
{
  "id": "sess-2025-11-22",
  "kind": "session",
  "realm_id": "fragment-cthulhu",
  "campaign_id": "camp-shards",
  "session_number": 13,
  "attendance": {
    "players_present": ["player-alice", "player-bob"],
    "players_absent": ["player-charlie"]
  },
  "story_links": {
    "chapters": ["chap-oasis-village"],
    "scenes": ["scene-dune-archive"],
    "active_chapter_index": 0,
    "active_scene_index": 0
  },
  "notes": "45-minute session; started 'Dune Archive' but did not complete it.",
  "changes": [
    { "by": "player-alice", "at": "2025-11-01T10:00:00Z", "type": "session_created" }
  ]
}

## Reference ID rules and naming

To keep a predictable and normalized schema, follow these rules:

- Always include a `kind` field on each top-level entity (one of: `world`, `realm`, `campaign`, `chapter`, `scene`, `turn`, `session`, `character`, `npc`, `object`, `location`).
- Use a single canonical parent reference field for hierarchical links. Examples:
  - Realm references its parent world using `world_id`.
  - Campaign references its parent realm using `realm_id`.
  - Chapter references its parent campaign using `campaign_id`.
  - Scene references its parent chapter using `chapter_id` (do not duplicate `campaign_id` or `realm_id` inside scenes; derive them by traversing chapter->campaign->realm when needed).
  - Turn references its parent scene using `scene_id` (do not include `chapter_id` or `campaign_id` inside turns; derive via scene->chapter->campaign if required).
- Characters are associated with a `realm_id` and can be referenced in campaigns/chapters/scenes by id.

These rules keep each document focused and ensure only one canonical place stores the immediate parent link.
```

# Unified Entity Schema (English)

## Hierarchy Overview
- **World** (top level): Defines ruleset and lore
  - **Realm**: A specific group of players within a world. Contains players and characters.
    - **Players**: Assigned to realm
    - **Characters/NPCs/Objects/Locations**: Assigned to realm (can be used across multiple campaigns)
    - **Campaign**: Story arc within a realm
      - **Chapter**: Sub-story arc with order number
        - **Scene**: Individual scene within a chapter
          - **Turn**: Individual actions within a scene

**Independent**: **Session** - play instance that references realm/campaign but isn't part of narrative hierarchy

## Entity Types
Applies to: pc (player characters), npc (non-player characters), beast, object, location
One entities collection with `kind` determining behavior.

### Player Character Example
Characters are assigned to a Realm and can participate in multiple Campaigns within that Realm.
```json
{
  "id": "char-alice-1",
  "uid": "unique-character-id-123",
  "kind": "pc",
  "type": "investigator",
  "name": "Dr. Amelia Carter",
  "realm_id": "fragment-cthulhu",
  "controller": {
    "owner": "player-alice",
    "mode": "player",
    "agent": "human"
  },
  "data": {
    "character_sheet": {}
  },
  "meta": {
    "ready": true,
    "created_by": "player-alice",
    "created_at": "2025-11-01T20:00:00Z"
  },
  "visibility": "realm",
  "changes": [
    { "by": "player-alice", "at": "2025-11-01T20:00:00Z" }
  ]
}
```

### NPC Example
NPCs are assigned to a Realm and can appear in multiple Campaigns/Scenes.
```json
{
  "id": "npc-archivist-77",
  "kind": "npc",
  "type": "archivist",
  "name": "Keeper of the Dunes",
  "realm_id": "fragment-cthulhu",
  "controller": { 
    "owner": "gm", 
    "mode": "gm", 
    "agent": "npc-dialogue-agent" 
  },
  "data": {
    "personality": ["suspicious", "curious"],
    "secrets": ["knows the location of one fragment"],
    "voice_style": "dry, old, slightly tired"
  },
  "changes": [
    { "by": "gm", "at": "2025-11-01T20:00:00Z" }
  ]
}
```

### Object Example
Objects are assigned to a Realm and can be used across multiple Campaigns.
```json
{
  "id": "obj-sun-fragment-1",
  "kind": "object",
  "type": "artifact",
  "name": "Shard of the Sun",
  "realm_id": "fragment-cthulhu",
  "data": {
    "properties": ["hot to touch", "faint glow"],
    "mechanics": { "fire_resistance": 5 }
  },
  "changes": [
    { "by": "player-alice", "at": "2025-11-01T20:00:00Z" }
  ]
}
```

### Location Example
Locations are assigned to a Realm and can be reused across multiple Campaigns (e.g., a city that appears in different story arcs).
```json
{
  "id": "loc-archive-building",
  "kind": "location",
  "type": "building",
  "name": "Dune Archive",
  "realm_id": "fragment-cthulhu",
  "data": {
    "environment": "dusty, dim, sand everywhere",
    "zones": ["Entrance Hall", "Reading Room", "Basement"],
    "danger_level": "medium"
  },
  "changes": [
    { "by": "player-alice", "at": "2025-11-01T20:00:00Z" }
  ]
}
```

## Character sheet
```json
{
  "investigator": {
    "name": "",
    "birthplace": "",
    "pronoun": "",
    "occupation": "",
    "residence": "",
    "age": ""
  },
  "characteristics": {
    "STR": {
      "reg": ""
    },
    "CON": {
      "reg": ""
    },
    "DEX": {
      "reg": ""
    },
    "APP": {
      "reg": ""
    },
    "INT": {
      "reg": ""
    },
    "POW": {
      "reg": ""
    },
    "SIZ": {
      "reg": ""
    },
    "EDU": {
      "reg": ""
    }
  },
  "hit_points": {
    "max": "",
    "current": ""
  },
  "magic_points": {
    "max": "",
    "current": ""
  },
  "luck": {
    "starting": "",
    "current": ""
  },
  "sanity": {
    "max": "",
    "current": "",
    "insane": ""
  },
  "status": {
    "temporary_insanity": false,
    "indefinite_insanity": false,
    "major_wound": false,
    "unconscious": false,
    "dying": false
  },
  "skills": {
    "Accounting": {
      "base": "05",
      "reg": "",
      "used": false
    },
    "Anthropology": {
      "base": "01",
      "reg": "",
      "used": false
    },
    "Appraise": {
      "base": "05",
      "reg": "",
      "used": false
    },
    "Archaeology": {
      "base": "01",
      "reg": "",
      "used": false
    },
    "Art/Craft": {
      "base": "05",
      "reg": "",
      "used": false
    },
    "Charm": {
      "base": "15",
      "reg": "",
      "used": false
    },
    "Climb": {
      "base": "20",
      "reg": "",
      "used": false
    },
    "Credit Rating": {
      "base": "00",
      "reg": "",
      "used": false
    },
    "Cthulhu Mythos": {
      "base": "00",
      "reg": "",
      "used": false
    },
    "Disguise": {
      "base": "05",
      "reg": "",
      "used": false
    },
    "Dodge": {
      "base": "DEX/2",
      "reg": "",
      "used": false
    },
    "Drive Auto": {
      "base": "20",
      "reg": "",
      "used": false
    },
    "Elec. Repair": {
      "base": "10",
      "reg": "",
      "used": false
    },
    "Fast Talk": {
      "base": "05",
      "reg": "",
      "used": false
    },
    "Fighting (Brawl)": {
      "base": "25",
      "reg": "",
      "used": false
    },
    "Firearms (Handgun)": {
      "base": "20",
      "reg": "",
      "used": false
    },
    "Firearms (Rifle/Shotgun)": {
      "base": "25",
      "reg": "",
      "used": false
    },
    "First Aid": {
      "base": "30",
      "reg": "",
      "used": false
    },
    "History": {
      "base": "05",
      "reg": "",
      "used": false
    },
    "Intimidate": {
      "base": "15",
      "reg": "",
      "used": false
    },
    "Jump": {
      "base": "20",
      "reg": "",
      "used": false
    },
    "Language (Own)": {
      "base": "EDU",
      "reg": "",
      "used": false
    },
    "Language": {
      "base": "01",
      "reg": "",
      "used": false
    },
    "Law": {
      "base": "05",
      "reg": "",
      "used": false
    },
    "Library Use": {
      "base": "20",
      "reg": "",
      "used": false
    },
    "Listen": {
      "base": "20",
      "reg": "",
      "used": false
    },
    "Locksmith": {
      "base": "01",
      "reg": "",
      "used": false
    },
    "Mech. Repair": {
      "base": "10",
      "reg": "",
      "used": false
    },
    "Medicine": {
      "base": "01",
      "reg": "",
      "used": false
    },
    "Natural World": {
      "base": "10",
      "reg": "",
      "used": false
    },
    "Navigate": {
      "base": "10",
      "reg": "",
      "used": false
    },
    "Occult": {
      "base": "05",
      "reg": "",
      "used": false
    },
    "Persuade": {
      "base": "10",
      "reg": "",
      "used": false
    },
    "Pilot": {
      "base": "01",
      "reg": "",
      "used": false
    },
    "Psychoanalysis": {
      "base": "01",
      "reg": "",
      "used": false
    },
    "Psychology": {
      "base": "10",
      "reg": "",
      "used": false
    },
    "Ride": {
      "base": "05",
      "reg": "",
      "used": false
    },
    "Science": {
      "base": "01",
      "reg": "",
      "used": false
    },
    "Sleight of Hand": {
      "base": "10",
      "reg": "",
      "used": false
    },
    "Spot Hidden": {
      "base": "25",
      "reg": "",
      "used": false
    },
    "Stealth": {
      "base": "20",
      "reg": "",
      "used": false
    },
    "Survival": {
      "base": "10",
      "reg": "",
      "used": false
    },
    "Swim": {
      "base": "20",
      "reg": "",
      "used": false
    },
    "Throw": {
      "base": "20",
      "reg": "",
      "used": false
    },
    "Track": {
      "base": "10",
      "reg": "",
      "used": false
    }
  },
  "combat": {
    "weapons": [
      {
        "name": "Brawl",
        "skill": "Fighting (Brawl)",
        "damage": "1D3 + DB",
        "num_attacks": "1",
        "range": "-",
        "ammo": "-",
        "malf": "-"
      }
    ],
    "move": 8,
    "build": "",
    "damage_bonus": ""
  },
  "story": {
    "my_story": "",
    "backstory": {
      "personal_description": "",
      "ideology_beliefs": "",
      "significant_people": "",
      "meaningful_locations": "",
      "treasured_possessions": "",
      "traits": "",
      "injuries_scars": "",
      "phobias_manias": "",
      "arcane_tomes_spells": "",
      "encounters_strange_entities": ""
    }
  },
  "gear_possessions": "",
  "wealth": {
    "spending_level": "",
    "cash": "",
    "assets": ""
  },
  "relationships": [

  ]
}
```