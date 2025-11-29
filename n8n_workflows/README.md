# Call of Cthulhu n8n Workflows

This directory contains modular n8n workflows for the Call of Cthulhu game system, implementing Prophet (AI assistant) and DungeonMaster (story agent) functionality.

## Architecture Overview

**Hybrid Modular Design:**
- **4 Shared Sub-Workflows** (separate files): Reusable components called by both main workflows
- **2 Main Workflows** (larger files): Prophet and DungeonMaster with inline agent-specific logic
- **Direct MongoDB Access**: No backend API layer for simplicity and performance

## Workflows

### Shared Sub-Workflows

1. **MongoDB_Query_SubWF.json**
   - Generic database fetcher for characters, campaigns, scenes, turns, sessions
   - Minimizes context by extracting only relevant fields
   - Input: `{ query_type: "character|turn|session|scene|campaign", entity_ids?, filters? }`
   - Output: `{ data: [...], references: [...], query_type }`

2. **Qdrant_RAG_SubWF.json**
   - Vector search for CoC rules and lore
   - Generates embeddings using Ollama (nomic-embed-text)
   - Queries Qdrant vector database (Cthulhu_Wiki collection)
   - Input: `{ query: "question text", collection?: "Cthulhu_Wiki", limit?: 5 }`
   - Output: `{ chunks: [{text, source, score}], references: [...] }`

3. **Dice_Roller_SubWF.json**
   - Dice calculations with CoC 7e mechanics
   - Supports: standard rolls (3D6+2), percentage rolls (D100), skill checks
   - Includes bonus/penalty dice support
   - Input: `{ roll_type: "standard|percentage|skill_check", expression?, skill_value?, bonus_dice?, penalty_dice? }`
   - Output: `{ total?, result?, formatted, roll_type, success_level? }`

4. **LLM_Synthesizer_SubWF.json**
   - Natural language generation using Ollama (gpt-oss:20b)
   - Builds context prompts from collected data
   - Supports both Prophet and DungeonMaster agent types
   - **Prophet Mode**: Simple Q&A format
   - **DungeonMaster Mode**: Structured JSON output with transition detection (Phase 3 enhancement)
   - Input: `{ question?, collected_data: {...}, agent_type: "prophet|dungeonmaster", references? }`
   - Output (Prophet): `{ answer, references, agent_type }`
   - Output (DungeonMaster): `{ narrative, summary, transition: { type, reason, suggested_name, suggested_description }, requires_input, interaction_type, references, agent_type }`

### Main Workflows

5. **Prophet_Main.json**
   - Read-only AI assistant for answering player questions
   - Webhook: `/coc_prophet`
   - Input: `{ player_id, question, session_id?, campaign_id?, character_ids? }`
   - Intent classification (6 types): RULES_LOOKUP, CHARACTER_INFO, GAME_HISTORY, DICE_CALCULATION, LORE_KNOWLEDGE, MULTI_STEP
   - Routes to appropriate sub-workflows based on intent
   - Supports iterative queries (max 5 cycles for complex questions)
   - Merges data from multiple sources before LLM synthesis
   - Response format: `{ output, references }`

6. **DungeonMaster_Main.json** (Legacy - 34 nodes)
   - Story agent for processing player actions and generating narrative scenes
   - Webhook: `/coc_dungeonmaster`
   - Input: `{ ActiveTurn: [...], scene_id, session_id, campaign_id, turn_id }`
   - Workflow: Parse actions → Detect skill checks (Ollama) → Fetch characters → Roll dice → Fetch campaign/scene → Query lore → Generate narrative (LLM) → Detect interaction (Ollama) → Write Turn reaction (MongoDB) → Respond
   - **CRITICAL**: Never takes actions on behalf of player characters, only resolves outcomes
   - Inline components: Skill check detection, interaction detection, Turn writing
   - Response format: `{ output, rules_applied[], requires_input, interaction_type }`
   - **Status**: Deprecated in favor of v2 (kept for backward compatibility)

7. **DungeonMaster_Main_v2.json** (Phase 3 Refactor - 6 nodes)
   - Simplified story agent using async callback pattern
   - Webhook: `/coc_dungeonmaster_v2`
   - Input: `{ turn_id, callback_url, context: {...}, actions: [...] }`
   - Workflow: Validate context → Prepare LLM input → Call LLM Synthesizer SubWF → Format callback → POST to backend
   - **Removes**: MongoDB writes, context assembly, skill checks, scene creation (all moved to backend)
   - **Keeps**: LLM orchestration only
   - Callback format: `POST {callback_url}` with `{ turn_id, success, result: { narrative, transition, ... }, error }`
   - **Requires**: Backend Phase 3 services (ContextAssemblyService, SkillCheckService, TransitionService)
   - **Feature flag**: Backend must set `USE_ASYNC_TURN_PROCESSING=True`

## Setup Instructions

### Prerequisites

- n8n instance running (Docker recommended)
- MongoDB accessible at `mongodb:27017`
  - Database: `call_of_cthulhu_gamerecords`
  - Collections: `entities`, `turns`, `sessions`, `scenes`, `campaigns`
- Qdrant vector database at `qdrant:6333`
  - Collection: `Cthulhu_Wiki` (populated with CoC rules and lore)
- Ollama running at `host.docker.internal:11434`
  - Model: `gpt-oss:20b` (for LLM)
  - Model: `nomic-embed-text` (for embeddings)

### Installation Steps

1. **Import Sub-Workflows First** (in order):
   ```
   1. MongoDB_Query_SubWF.json
   2. Qdrant_RAG_SubWF.json
   3. Dice_Roller_SubWF.json
   4. LLM_Synthesizer_SubWF_v2.json  ← Use v2 for Phase 3
   ```

2. **Import Main Workflows**:
   ```
   5. Prophet_Main.json
   6. DungeonMaster_Main_v2.json  ← Use v2 for Phase 3
   ```

   **Note**: For Phase 3 testing, rename v2 workflows in n8n UI:
   - `LLM Synthesizer SubWF v2` → `LLM Synthesizer SubWF`
   - Keep `DungeonMaster Main v2` as-is (different webhook path)
   ```

   In n8n:
   - Go to Workflows → Import from File
   - Select each JSON file
   - **IMPORTANT**: Activate each sub-workflow after import

2. **Configure MongoDB Credentials**:
   - Go to Settings → Credentials → Add Credential
   - Type: MongoDB
   - Name: `CoC MongoDB`
   - Connection String: `mongodb://martin_usr:CorzBRxa8Xz3iAv90VmH@mongodb:27017/?authSource=admin`
   - Test connection
   - Save

3. **Import Main Workflows**:
   ```
   5. Prophet_Main.json
   6. DungeonMaster_Main.json (legacy)
   7. DungeonMaster_Main_v2.json (Phase 3 refactored version)
   ```

   - Import each file
   - Verify all sub-workflow calls are connected
   - Activate workflows

4. **Configure Webhook URLs**:
   - Prophet webhook: `http://<n8n-host>:5693/webhook/coc_prophet`
   - DungeonMaster webhook (legacy): `http://<n8n-host>:5693/webhook/coc_dungeonmaster`
   - DungeonMaster v2 webhook: `http://<n8n-host>:5693/webhook/coc_dungeonmaster_v2`

   Update backend environment variables for Phase 3:
   ```
   N8N_DUNGEONMASTER_V2_WEBHOOK=http://n8n:5678/webhook/coc_dungeonmaster_v2
   USE_ASYNC_TURN_PROCESSING=True
   ```

## Testing

### Test MongoDB Query SubWF

```json
{
  "query_type": "character",
  "entity_ids": ["char-alice-1"]
}
```

Expected output: Character data with minimized fields

### Test Qdrant RAG SubWF

```json
{
  "query": "How do skill checks work?",
  "collection": "Cthulhu_Wiki",
  "limit": 5
}
```

Expected output: Relevant rule chunks with sources

### Test Dice Roller SubWF

**Standard Roll:**
```json
{
  "roll_type": "standard",
  "expression": "3D6+2"
}
```

**Skill Check:**
```json
{
  "roll_type": "skill_check",
  "skill_name": "Spot Hidden",
  "skill_value": 45,
  "bonus_dice": 0,
  "penalty_dice": 0,
  "difficulty": "Regular"
}
```

Expected output: Formatted dice results with success determination

### Test LLM Synthesizer SubWF

```json
{
  "question": "What is my Sanity?",
  "agent_type": "prophet",
  "collected_data": {
    "characters": [
      {
        "name": "Dr. Amelia Carter",
        "sanity": {
          "current": 65,
          "max": 80
        }
      }
    ]
  },
  "references": ["Character: Dr. Amelia Carter"]
}
```

Expected output: Natural language answer with references

### Test LLM Synthesizer SubWF (DungeonMaster Mode)

**Phase 3 Enhancement:** DungeonMaster agent now returns structured JSON with transition detection.

```json
{
  "agent_type": "dungeonmaster",
  "collected_data": {
    "campaign": {
      "name": "The Haunting",
      "setting": { "tone": "classic horror" }
    },
    "chapter": {
      "name": "Investigation",
      "summary": "Investigators look into Corbitt House"
    },
    "scene": {
      "name": "The Foyer",
      "location": "Corbitt House entrance",
      "summary": "Party just arrived"
    },
    "previous_turns": [],
    "characters": [
      {
        "name": "Dr. Morgan",
        "occupation": "Physician"
      }
    ],
    "lore_context": [],
    "skill_checks": [
      {
        "character_name": "Dr. Morgan",
        "skill_name": "Spot Hidden",
        "success_level": "Regular Success",
        "rolled": 32,
        "target_value": 45
      }
    ]
  },
  "references": []
}
```

**Expected Output:**
```json
{
  "narrative": "Dr. Morgan steps into the dusty foyer, eyes scanning the shadows. The keen physician notices subtle scratches on the floorboards, suggesting something has been dragged across them recently...",
  "summary": "Dr. Morgan examines the foyer and notices drag marks",
  "transition": {
    "type": "none",
    "reason": null,
    "suggested_name": null,
    "suggested_description": null
  },
  "requires_input": false,
  "interaction_type": "DISCOVERY",
  "agent_type": "dungeonmaster",
  "references": []
}
```

**Transition Detection Example (Scene Change):**
```json
{
  "narrative": "You push open the heavy door and descend the creaking wooden stairs. The air grows colder and damper with each step. At the bottom, you find yourself in a low-ceilinged basement, its stone walls slick with moisture...",
  "summary": "Party descends to the basement",
  "transition": {
    "type": "scene",
    "reason": "Location change to basement (different floor, significant atmospheric shift)",
    "suggested_name": "The Basement",
    "suggested_description": "A damp, low-ceilinged basement with stone walls"
  },
  "requires_input": false,
  "interaction_type": "NONE",
  "agent_type": "dungeonmaster",
  "references": []
}
```

### Test DungeonMaster Main v2 (Full Workflow)

**Phase 3 Enhancement:** v2 workflow receives pre-assembled context bundle from backend.

```json
{
  "turn_id": "turn-test-001",
  "callback_url": "http://backend:8000/api/v1/internal/turns/turn-test-001/complete",
  "timestamp": "2025-11-29T12:00:00Z",
  "context": {
    "campaign": {
      "name": "The Haunting",
      "setting": { "tone": "cosmic horror" }
    },
    "chapter": {
      "name": "Investigation",
      "summary": "Looking into Corbitt House"
    },
    "scene": {
      "name": "The Foyer",
      "location": "Corbitt House entrance"
    },
    "previous_turns": [],
    "characters": [
      { "name": "Dr. Morgan", "occupation": "Physician" }
    ],
    "lore_context": [],
    "skill_checks": []
  },
  "actions": [
    {
      "character": "Dr. Morgan",
      "act": "Examines the dusty entrance hall carefully"
    }
  ]
}
```

**Expected Workflow:**
1. ✅ Webhook receives context bundle
2. ✅ Validates required fields (turn_id, callback_url, context, actions)
3. ✅ Formats for LLM Synthesizer SubWF
4. ✅ Calls LLM (returns narrative + transition)
5. ✅ Formats callback payload
6. ✅ POSTs to backend callback URL

**Backend Callback Receives:**
```json
{
  "turn_id": "turn-test-001",
  "success": true,
  "result": {
    "narrative": "Dr. Morgan steps into the dusty foyer...",
    "summary": "Dr. Morgan examines the entrance",
    "transition": { "type": "none" },
    "requires_input": false,
    "interaction_type": "DISCOVERY"
  },
  "error": null
}
```

## Troubleshooting

### MongoDB Connection Fails
- Verify MongoDB is accessible from n8n container
- Check credentials in n8n settings
- Ensure database name is correct: `call_of_cthulhu_gamerecords`

### Qdrant Not Returning Results
- Verify Qdrant is running: `http://qdrant:6333/collections`
- Check collection exists: `Cthulhu_Wiki`
- Verify collection has data points
- Test embedding generation with Ollama

### Ollama LLM Calls Timeout
- Increase timeout in HTTP Request nodes (default: 60s)
- Verify Ollama is running: `curl http://host.docker.internal:11434/api/tags`
- Check model is pulled: `gpt-oss:20b` and `nomic-embed-text`
- Monitor Ollama logs for errors

### Sub-Workflow Not Found
- Ensure sub-workflows are activated in n8n
- Check workflow IDs match in Execute Workflow nodes
- Re-import sub-workflows if necessary

## Architecture Decisions

### Why MongoDB Direct Access?
- **Simpler**: No extra HTTP layer
- **Faster**: Direct DB connection, no network hop
- **Easier**: Native n8n MongoDB node support
- **Better for development**: Easier debugging

### Why Hybrid Structure?
- **Shared sub-workflows**: MongoDB, Qdrant, Dice, LLM truly reused by both agents
- **Inline main logic**: Skill check detection, interaction detection inline for easier visualization
- **Best of both**: Reusability where it matters, simplicity where it helps

## Data Flow Examples

### Prophet Flow (Simple Query)
```
User asks: "What is my Sanity?"
  ↓
Webhook - Prophet: Receive request
  ↓
Extract Context: Parse player_id, question, character_ids
  ↓
Intent Classifier: Ollama LLM → "CHARACTER_INFO"
  ↓
Intent Router: Route to character path
  ↓
Prepare Character Query: Build MongoDB query
  ↓
MongoDB Query SubWF: Fetch character data
  ↓
Merge Collected Data: Combine character data + references
  ↓
LLM Synthesizer SubWF: Generate answer with agent_type='prophet'
  ↓
Format Response: { output: "Your Sanity is 65/80...", references: [...] }
  ↓
Respond to Webhook: Return JSON to frontend
```

### Prophet Flow (Multi-Step Query)
```
User asks: "Can I make the Spot Hidden check to find the hidden door?"
  ↓
Webhook - Prophet: Receive request
  ↓
Extract Context: Parse question
  ↓
Intent Classifier: Ollama LLM → "MULTI_STEP"
  ↓
Multi-Step Orchestrator: Iteration 1
  ↓
Analyze Data Needs: LLM determines needs_characters=true, needs_rules=true
  ↓
[Loop back to fetch character data + Spot Hidden skill value]
  ↓
MongoDB Query SubWF: Fetch character with Spot Hidden skill
  ↓
Qdrant RAG SubWF: Fetch rules about skill checks
  ↓
Merge Collected Data: Combine all context
  ↓
LLM Synthesizer SubWF: Generate comprehensive answer
  ↓
Format Response: { output: "Your Spot Hidden is 45%...", references: [...] }
  ↓
Respond to Webhook: Return JSON
```

### DungeonMaster Flow
```
Players submit actions: { ActiveTurn: [{ speak: "...", act: "I examine the door carefully", ... }] }
  ↓
Webhook - DungeonMaster: Receive request
  ↓
Parse Actions: Extract player actions, character IDs, scene/session/campaign IDs
  ↓
Detect Skill Checks (Ollama): Analyze actions → detects "Spot Hidden" needed
  ↓
Parse Detected Skills: Extract skill check requirements
  ↓
Has Skill Checks? → TRUE path
  ↓
Prepare Character Fetch: Build MongoDB query for character IDs
  ↓
MongoDB Query SubWF: Fetch characters with skill values
  ↓
Match Skills to Characters: Find "Spot Hidden" value (45%) for player character
  ↓
Dice Roller SubWF: Roll skill check → "Success" (rolled 32 vs 45)
  ↓
[Parallel fetches]
├─ Fetch Campaign (MongoDB): Get story arc, milestones, setting
├─ Fetch Scene (MongoDB): Get current scene context, participants
└─ Qdrant RAG SubWF: Query lore about "hidden passages" and "examination"
  ↓
Merge Collected Data: Combine all context (characters, campaign, scene, lore, skill results)
  ↓
Prepare LLM Input: Format collected data for dungeonmaster agent
  ↓
LLM Synthesizer SubWF: Generate narrative (agent_type='dungeonmaster')
  → "You carefully examine the door. Your keen eye notices subtle scratches..."
  ↓
Detect Interaction Needed (Ollama): Analyze scene → requires_input=true (DISCOVERY)
  ↓
Parse Interaction: Extract interaction data
  ↓
Write Turn Reaction (MongoDB): Update Turn document with:
  - reaction.description (narrative)
  - reaction.skill_checks (Spot Hidden: Success)
  - reaction.requires_input (true)
  - status: "awaiting_player_input"
  ↓
Format Response: Build final output
  ↓
Respond to Webhook: Return JSON
{
  "output": "You carefully examine the door...",
  "rules_applied": [{ "rule_type": "skill_check", "skill_name": "Spot Hidden", "result": "Success" }],
  "requires_input": true,
  "interaction_type": "DISCOVERY"
}
```

## Maintenance

### Updating Sub-Workflows
1. Export modified workflow from n8n
2. Replace JSON file in this directory
3. Document changes in commit message
4. Test with both Prophet and DungeonMaster

### Adding New Sub-Workflows
1. Create new workflow in n8n
2. Test independently
3. Export to this directory
4. Update this README
5. Update main workflows to use new sub-workflow

## Performance Targets

- **MongoDB Query**: <1s
- **Qdrant RAG**: <2s (including embedding)
- **Dice Roller**: <100ms
- **LLM Synthesizer**: <3s (depends on model/prompt size)
- **Prophet End-to-End**: <5s
- **DungeonMaster End-to-End**: <8s

## Security Considerations

- MongoDB credentials stored in n8n encrypted credentials
- No credentials exposed in workflow JSON files
- Qdrant and Ollama on internal network only
- Webhooks accessible from frontend (consider authentication layer)
