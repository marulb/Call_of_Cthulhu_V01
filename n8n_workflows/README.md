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
   - Input: `{ question?, collected_data: {...}, agent_type: "prophet|dungeonmaster", references? }`
   - Output: `{ answer, references, agent_type }`

### Main Workflows

5. **Prophet_Main.json** (TODO)
   - Read-only AI assistant for answering player questions
   - Webhook: `/coc_prophet`
   - Intent classification → route to sub-workflows → iterate → respond
   - Response format: `{ output, references }`

6. **DungeonMaster_Main.json** (TODO)
   - Story agent for processing player actions and generating scenes
   - Webhook: `/coc_dungeonmaster`
   - Parse actions → detect skill checks → roll → generate scene → write Turn reaction
   - Response format: `{ output, rules_applied }`

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
   4. LLM_Synthesizer_SubWF.json
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
   6. DungeonMaster_Main.json
   ```

   - Import each file
   - Verify all sub-workflow calls are connected
   - Activate workflows

4. **Configure Webhook URLs**:
   - Prophet webhook: `http://<n8n-host>:5693/webhook/coc_prophet`
   - DungeonMaster webhook: `http://<n8n-host>:5693/webhook/coc_dungeonmaster`

   Update frontend environment variables:
   ```
   VITE_N8N_PROPHET_WEBHOOK=http://localhost:5693/webhook/coc_prophet
   VITE_N8N_DUNGEONMASTER_WEBHOOK=http://localhost:5693/webhook/coc_dungeonmaster
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

### Prophet Flow
```
User asks: "What is my Sanity?"
  ↓
Prophet Main: Intent = CHARACTER_INFO
  ↓
MongoDB Query SubWF: Fetch character
  ↓
LLM Synthesizer SubWF: Generate answer
  ↓
Return: "Your Sanity is 65/80..."
```

### DungeonMaster Flow
```
Players submit actions
  ↓
DungeonMaster Main: Parse actions
  ↓
Inline Skill Check Detector: "examine door" → Spot Hidden
  ↓
MongoDB Query SubWF: Fetch character stats
  ↓
Dice Roller SubWF: Roll Spot Hidden (success!)
  ↓
Qdrant RAG SubWF: Fetch mythos about "hidden passages"
  ↓
LLM Synthesizer SubWF: Generate narrative scene
  ↓
Inline Interaction Detector: Requires user input (hidden passage found)
  ↓
Inline Turn Writer: Write Turn.reaction to MongoDB
  ↓
Return: Scene description + rules_applied
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
