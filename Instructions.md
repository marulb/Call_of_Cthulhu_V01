# Call of Cthulhu - Game Management System Implementation

## Overview
RPG campaign management system with login/selection flow for World → Realm → Campaign → Characters → Session management.

## Data Architecture

### Two Parallel Layers

**1. In-Game Narrative Layer** (Hierarchical)
```
World (ruleset/lore)
  └─ Realm (player group)
      ├─ Characters (belong to realm, participate in campaigns)
      └─ Campaign (story arc)
          └─ Chapter (campaign parts) [DEFERRED]
              └─ Scene (chapter parts) [DEFERRED]
                  └─ Turn (smallest unit) [DEFERRED]
```

**2. Real-World Session Layer** (Independent)
```
Session (meeting instance)
  - References: realm_id, campaign_id
  - Tracks: attendance, story_links, notes
  - Not part of narrative hierarchy
```

### Database Structure

**Two MongoDB Databases:**

1. **`call_of_cthulhu_system`** - AI knowledge base (read-heavy, costly to regenerate)
   - Collections: `worlds`, `rulesets`, `ai_processed_content`
   - Mainly used by AI agents for retrieval

2. **`call_of_cthulhu_gamerecords`** - Player-created data (write-heavy)
   - Collections: `realms`, `campaigns`, `entities`, `sessions`
   - Used by both players and AI
   - `entities` collection stores all characters, NPCs, objects, locations (filtered by `kind` field)

**Change Tracking:**
All entities include `changes` array:
```json
"changes": [
  {"at": "2025-11-22T10:00:00Z", "by": "player-name"}
]
```

## Login & Selection Flow

### User Journey
1. **Enter Player Name** (real-world player, not character)
2. **Select/Create World** (ruleset)
3. **Select/Create Realm** (player group in this world)
4. **Select/Create Campaign** (story arc in this realm)
5. **Select Characters** (player's characters in this realm - multi-select)
6. **Session Choice**: "New Session" or "Continue Previous"

### State Management
- **Pinia Store**: Active session UI state (current selections, player name)
- **MongoDB**: Persistent state (character stats, story progress, current scene/turn)
- **localStorage**: Player name persistence for convenience

### UI Pattern (Consistent Across All Steps)
```
┌─────────────────────────────────────────┐
│ Table with Radio/Checkbox Selection     │
├─────────────────────────────────────────┤
│ ○ Existing Item 1      [Details ▼]      │
│ ○ Existing Item 2      [Details ▼]      │
│ ● Create New           [Form ▼]         │
└─────────────────────────────────────────┘
```

- **Single select**: Radio buttons (World, Realm, Campaign, Session)
- **Multi-select**: Checkboxes (Characters)
- **Unfold**: Click to expand details or creation form
- **Consistent layout** across all entity types

## Implementation Scope

### Phase 1: Core Login Flow (Current)
✅ **Full CRUD Implementation:**
- World (name, ruleset, description)
- Realm (name, world_id, players, description)
- Campaign (name, realm_id, status, description)
- Character (name, realm_id, type, controller, description)
- Session (session_number, realm_id, campaign_id, attendance)

⏸️ **Deferred to Later:**
- Chapters, Scenes, Turns
- NPCs, Objects, Locations
- Full character sheets
- Authentication/authorization

### Backend API Structure

**Base URL:** `/api/v1/`

**Endpoints:**
```
GET    /worlds                    # List all worlds
POST   /worlds                    # Create world
GET    /worlds/{id}               # Get world details
PUT    /worlds/{id}               # Update world
DELETE /worlds/{id}               # Delete world

GET    /realms?world_id={id}      # List realms (filtered by world)
POST   /realms                    # Create realm
GET    /realms/{id}               # Get realm details
PUT    /realms/{id}               # Update realm
DELETE /realms/{id}               # Delete realm

GET    /campaigns?realm_id={id}   # List campaigns (filtered by realm)
POST   /campaigns                 # Create campaign
GET    /campaigns/{id}            # Get campaign details
PUT    /campaigns/{id}            # Update campaign
DELETE /campaigns/{id}            # Delete campaign

GET    /characters?realm_id={id}&player={name}  # List player's characters
POST   /characters                # Create character
GET    /characters/{id}           # Get character details
PUT    /characters/{id}           # Update character
DELETE /characters/{id}           # Delete character

GET    /sessions?realm_id={id}&campaign_id={id}  # List sessions
POST   /sessions                  # Create session
GET    /sessions/{id}             # Get session details
GET    /sessions/latest?realm_id={id}&campaign_id={id}  # Get latest session
PUT    /sessions/{id}             # Update session
DELETE /sessions/{id}             # Delete session
```

### Frontend Structure

**Router:**
```
/                       → Login (player name entry)
/select/world           → World selection
/select/realm           → Realm selection
/select/campaign        → Campaign selection
/select/characters      → Character selection
/select/session         → Session choice (new/continue)
/game                   → Main game view [FUTURE]
```

**Pinia Stores:**
```javascript
// stores/session.ts
- playerName: string
- selectedWorld: World | null
- selectedRealm: Realm | null
- selectedCampaign: Campaign | null
- selectedCharacters: Character[]
- currentSession: Session | null
```

**Components:**
```
src/
├── views/
│   ├── LoginView.vue           # Player name entry
│   ├── WorldSelectView.vue     # World selection
│   ├── RealmSelectView.vue     # Realm selection
│   ├── CampaignSelectView.vue  # Campaign selection
│   ├── CharacterSelectView.vue # Character selection (multi)
│   └── SessionSelectView.vue   # New/Continue session
├── components/
│   ├── EntityTable.vue         # Reusable table for all entities
│   ├── EntityRow.vue           # Expandable row component
│   └── CreateEntityForm.vue    # Generic creation form
└── stores/
    └── session.ts              # Session state management
```

## Technical Stack

### Backend
- **FastAPI** (already installed)
- **Motor** (async MongoDB driver - already installed)
- **Pydantic** models for validation

### Frontend
- **Vue 3** with TypeScript
- **Vue Router** for navigation
- **Pinia** for state management
- **Axios** for API calls

### Available Backend Dependencies
```python
# Already in fastapi_01:latest image
fastapi
uvicorn
motor              # MongoDB async driver
python-multipart
aiohttp
diff-match-patch
```

## Development Commands

### Git SSH Setup (Manual)
```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/git_marulb
# Enter passphrase when prompted
```

### Git Push
```bash
git push -u origin main
```

### Access Points
- Frontend: http://localhost:3093
- Backend API Docs: http://localhost:8093/docs
- MongoDB: mongodb://localhost:27093
- Qdrant: http://localhost:6393
- n8n: http://localhost:5693

## Port Schema
All services use ports ending in `93` (C1 hex → Call of Cthulhu v1)

## Next Steps (After Phase 1)
1. Implement Chapter/Scene/Turn management
2. Add NPC/Object/Location entities
3. Build game session interface (turn-based gameplay)
4. Integrate AI agents for narrative generation
5. Add authentication and user management
