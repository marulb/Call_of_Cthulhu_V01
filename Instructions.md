# Gameplay Interface Specification

## Overview
The gameplay interface is the core session screen where players interact with the Keeper AI, manage their characters' actions, and coordinate with other players. This interface operates within an active **Session**, which references a specific Realm and Campaign.

## Data Model Context
See `data.md` for complete schema. **Note:** `data.md` is a draft schema and can be adapted based on best-practice considerations during development.

This interface operates on:

```
World (ruleset/lore)
  └─ Realm (player group)
      ├─ Players (users in realm)
      ├─ Characters/NPCs/Objects/Locations (entities in realm)
      └─ Campaign (story arc)
          └─ Chapter [AI-managed]
              └─ Scene [AI-managed]
                  └─ Turn (player actions → Keeper response)
```

**Sessions** are independent entities (not part of narrative hierarchy) that reference:
- `realm_id`, `campaign_id`
- `attendance.players_present`, `attendance.players_absent`
- `story_links.active_chapter_index`, `story_links.active_scene_index`

## Core Components

### 1. Session Info Header
Display current context (read-only):
- Campaign name (from `campaigns` collection)
- Chapter name (from `story_links.chapters[active_chapter_index]`)
- Scene name (from `story_links.scenes[active_scene_index]`)
- Turn number (current `turn.order` + 1)

### 2. Players List
**Purpose:** Show all players in the current session, their characters, ready states, and Master designation.

**Structure:**
```
[MASTER] PlayerName
  ├─ Character1
  ├─ Character2
  └─ Character3
```

Display hierarchy from:
- **Players:** `realm.players[]` filtered by `session.attendance.players_present[]`
- **Characters:** `entities` collection where `kind: "pc"` and `controller.owner` matches player ID
- **Master:** Player matching `session.master_player_id` (field to be added to Session schema)

**Visual Indicators:**
- **Master Badge:** `[MASTER]` prefix on player name
- **Local Player:** Faint yellow background (toggles to faint green when ready)
- **Other Players:** Faint red background (not ready) → Faint green (ready)
- **Characters:** Inherit parent player's color scheme
- **Owned Characters:** Yellow background (toggles to green when ready)

**Ready State Logic:**
- Each character has individual ready toggle
- Player-level ready button sets ALL owned characters to ready
- Players can un-ready themselves/characters at any time
- Ready states sync in real-time across all clients

**Master Controls:**
- First player to join session becomes Master automatically
- **"Become Master" button** visible to all players (instant transfer, no confirmation needed)
  - Purpose: Prevent session blocking due to AFK master
- Only Master can submit the action list to Keeper AI
- Master can submit even if not all players are ready (warning popup: "Not all players ready. Proceed?")

**Late Joiners:**
- New players joining active session trigger Master notification: "PlayerName wants to join. Accept?"
- If accepted: 
  - Add player to `session.attendance.players_present[]`
  - Player's characters (from `entities` where `controller.owner` matches) added to UI
  - New players can immediately add actions to current turn

### 3. Realm Chat (Session Chat)
Player-to-player communication within the current session.

**Features:**
- Standard chat interface (input field + message history)
- Foldable/expandable panel
- Visual alert (flashing) when folded and new message received
- **Persistence:** Does NOT persist across page refreshes (ephemeral)

**Priority:** Medium (below Action List and Turn History, above Rules Chat)

### 4. Rules Chat (Per-Player)
Private AI conversation for rules clarification.

**Features:**
- Each player has individual chat instance (not visible to others)
- Connects to dedicated Rules AI agent
- Foldable/expandable panel with alert indicator
- **Persistence:** Does NOT persist across page refreshes

**Priority:** Lowest

### 5. Turn History Display
Scrollable chat-style view showing past turns and current turn.

**Format:**
```
▼ Turn 2: Actions [foldable/locked]
  └─ (Submitted action list from Turn 2)
  
▼ Turn 2: Scene Description [foldable/locked]
  └─ (Keeper's narrative response)
  
▶ Turn 3: Actions [current/editable]
  └─ (Active action list - see below)
```

**Behavior:**
- Past turns are locked (read-only, copyable)
- Foldable sections to manage screen space
- Auto-scroll to current turn on new Keeper response
- **Persistence:** Full turn history stored in MongoDB

**Priority:** High (primary focus with Action List)

### 6. Action List (Current Turn)
The core interaction interface where players queue character actions.

#### Action Entry Structure
Each action entry contains:
- **Character selector** (dropdown of owned characters from `entities` where `controller.owner` matches local player)
  - **Fixed after creation:** Character assignment cannot be changed once action is created
  - To reassign: delete action and create new one with different character
- **Five optional collapsible text fields:**
  1. **Speak:** Dialogue
  2. **Act:** Physical action
  3. **Appearance:** Observable behavior (shivering, grinning)
  4. **Emotion:** Inner emotional state (fearful, excited)
  5. **OOC:** Out-of-character notes/questions to Keeper
  - Empty fields should be collapsed/hidden by default
  - Show expand indicator when field has content

These map to the `turn.actions[]` array structure in `data.md`:
```json
{
  "actor_id": "char-alice-1",           // Character ID (immutable after creation)
  "controller_owner": "player-alice",   // Player ID
  "speak": "...",
  "act": "...",
  "appearance": "...",
  "emotion": "...",
  "ooc": "...",
  "meta": {
    "ready": true,
    "resolved": false
  }
}
```

**Example:**
```
Character: Aldric
Speak: "I think there might be someone at the door"
Act: Looking at Beatrice
Appearance: Questioning look
```

#### Action List Mechanics
- **Multiple Actions:** Same character can appear multiple times in list
- **Drag-and-Drop Reordering:** Full flexibility - any action can be moved anywhere
- **Adding Actions:** 
  - "Add Action" button beside each owned character in Players List
  - Alternative: Drag character from Players List into Action List
- **Removing Actions:** Delete button per action entry
- **Reactive Updates:** All players see real-time updates to action list

**Conceptual Example:**
```
1. [Character: Aldric] Speak: "Check the door?" Act: "Looking at Beatrice"
2. [Character: Beatrice] Act: "Nodding and gesturing at door"
3. [Character: Aldric] Speak: "Ok, I'll look" Act: "Moving toward door"
4. [Character: Chen] Act: "Drawing weapon quietly"
```

#### Submission Flow
1. Players add/edit actions for their characters
2. Players mark characters/themselves as ready (via `meta.ready` flag)
3. Master clicks "Submit Turn" button
4. If not all ready: Warning popup with Proceed/Cancel
5. Action list submitted to Keeper AI:
   - Create new `Turn` document with `status: "ready_for_agents"`
   - Populate `turn.actions[]` with ordered action entries
   - Add Turn ID to `scene.turns[]` array
6. Keeper AI processes turn:
   - Updates `turn.status` to "processing" → "completed"
   - Populates `turn.reaction.description` (scene narrative)
   - May mark actions as `resolved: true` or leave some unprocessed
7. UI updates:
   - Turn moves to history (locked)
   - `turn.reaction.description` displays as "Scene Description"
   - New empty action list for next turn

**Important:** Keeper AI may interrupt action list before all actions complete (unforeseeable story events via `turn.reaction.description`). Actions left with `resolved: false` are dropped - players react to new scene state.

**Persistence:** 
- Action drafts: Store in temporary collection or session state (restore on refresh)
- Submitted actions: Permanent in `turns` collection as per `data.md`

## Technical Requirements

### Real-Time Sync (WebSocket)
- Players List ready states
- Action List changes (add/remove/reorder)
- **Action field edits:** Persist on blur (when focus leaves input field)
  - Debounce: Save to backend when user stops typing for 500ms or moves to different field
  - Optimistic UI: Show changes immediately, sync in background
- Chat messages (Realm + Rules)
- Late joiner notifications
- Turn submissions and Keeper responses
- Master transfers

**Reconnection Handling:**
- On reconnect: Fetch latest `action_drafts` for current session
- Restore action list state from backend
- Show notification if other players made changes during disconnect

### MongoDB Collections Structure

**Reference `data.md` for authoritative schema.** Key adaptations needed:

**sessions:** Add field
```javascript
{
  // ... existing fields from data.md ...
  master_player_id: String,  // Player ID of current master
}
```

**turns:** Already matches requirements in `data.md`
- `actions[]` array with `actor_id`, `controller_owner`, action fields
- `reaction.description` for Keeper narrative response
- `meta.ready` and `meta.resolved` flags per action

**action_drafts:** (New temporary collection for UI state)
```javascript
{
  _id: ObjectId,
  session_id: String,
  player_id: String,
  character_id: String,
  speak: String,
  act: String,
  appearance: String,
  emotion: String,
  ooc: String,
  order: Number,
  meta: {
    ready: Boolean
  },
  updated_at: Date
}
```

Note: Clear `action_drafts` for session after turn submission.

### UI Layout Priority
1. **Highest:** Turn History + Current Action List (always visible)
2. **Medium:** Realm Chat (foldable with alerts)
3. **Lowest:** Rules Chat (foldable with alerts)

### Future Considerations
- Scene/Chapter transitions: AI-detected via `turn.reaction` content, not manual UI initially
- Turn summarization: `turn.agent_result.narrative_summary` feeds into `scene.summary`
- Scene summarization: Aggregate `scene.summary` feeds into `chapter.summary`
- Historical context: Keeper AI receives summaries from `campaign.story_arc`, completed chapters/scenes
- Master settings interface: Player management (kick, permissions) - deferred
- Character ownership transfer: Allow reassigning `controller.owner` - deferred