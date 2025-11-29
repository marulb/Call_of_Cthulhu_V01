# Call of Cthulhu Project

RPG campaign management system with Vue.js frontend and FastAPI backend.

## Documentation

| Document | Purpose |
|----------|---------|
| [`AGENTS.md`](./AGENTS.md) | **AI agent instructions** — read this first |
| [`docs/architecture/`](./docs/architecture/) | System design, data flow, friction points |
| [`docs/specifications/`](./docs/specifications/) | UI specs, data model |
| [`n8n_workflows/README.md`](./n8n_workflows/README.md) | Workflow documentation |

## Stack
- Frontend: Vue.js (port 3093)
- Backend: FastAPI (port 8093)
- Databases: MongoDB (27093), Qdrant (6393)
- Automation: n8n (port 5693)
- AI: Ollama (host port 11434)

## Port Schema
All services use ports ending in `93` (C1 hex → Call of Cthulhu v1)
- Frontend: 3093
- Backend: 8093
- MongoDB: 27093
- Qdrant: 6393
- n8n: 5693

## Setup
1. Ensure Docker image `fastapi_01:latest` is built
2. Start with Dockge: Upload docker-compose.yml
3. Access:
   - Frontend: http://localhost:3093
   - Backend API: http://localhost:8093/docs
   - n8n: http://localhost:5693
   - MongoDB: mongodb://localhost:27093
   - Qdrant: http://localhost:6393

## Development
Open `Call_of_Cthulhu_01.code-workspace` in VSCode.

## n8n — concise local info

Local web UI (host): http://localhost:5693/

Docker-internal address (other services in the same compose network): http://n8n:5678/

API base (host): http://localhost:5693/rest  (container-internal: http://n8n:5678/rest)

API key (local dev):
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1MDYwNzhjMC03YjhhLTQ2MjAtOGYxMi03Nzc2ZTVmMzRlYjEiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzYzOTE3MzM1LCJleHAiOjE3NzE2NTAwMDB9.pKKPZgl67iWGfH8AfvsVH6DQ6-gvAinvJJORYVGdlcU
```

Two quick API examples (use header `X-N8N-API-KEY: <key>`):

- List workflows

```bash
curl -sS -H "X-N8N-API-KEY: eyJhbGciOi..." http://localhost:5693/rest/workflows
```

- Create a workflow (minimal example)

```bash
curl -X POST http://localhost:5693/rest/workflows -H "Content-Type: application/json" -H "X-N8N-API-KEY: eyJhbGciOi..." -d '{"name":"my-workflow","nodes":[],"connections":{}}'
```

(Use the docker-internal URL `http://n8n:5678/rest` from other containers in the same compose network.)

## Export workflows to files (example)

Run these commands locally to export the workflows list and fetch the workflow named "Keeper" into the project `n8n` folder.

1) Fetch all workflows and save to `n8n/workflows.json`:

```bash
curl -X GET 'http://localhost:5693/api/v1/workflows' -H 'Accept: application/json' -H 'X-N8N-API-KEY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1MDYwNzhjMC03YjhhLTQ2MjAtOGYxMi03Nzc2ZTVmMzRlYjEiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzYzOTE3MzM1LCJleHAiOjE3NzE2NTAwMDB9.pKKPZgl67iWGfH8AfvsVH6DQ6-gvAinvJJORYVGdlcU' -o n8n/tmp/workflows.json
```

2) Extract the workflow id for the workflow named "Keeper" (example using jq or python):

```bash
# with jq (if installed)
jq -r '.data[] | select(.name=="Keeper") | .id' n8n/tmp/workflows.json

# or with python
python3 - <<'PY'
import json
js=json.load(open('n8n/workflows.json'))
for w in js.get('data',[]):
      if w.get('name','').lower().strip()=='keeper':
            print(w.get('id'))
            break
PY
```

3) Use the workflow id you found (example result: `Nbw7xEIAgNqaxqlo`) to fetch the Keeper workflow and save it to `n8n/Keeper.json`:

```bash
curl -X GET "http://localhost:5693/api/v1/workflows/Nbw7xEIAgNqaxqlo" -H 'Accept: application/json' -H 'X-N8N-API-KEY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1MDYwNzhjMC03YjhhLTQ2MjAtOGYxMi03Nzc2ZTVmMzRlYjEiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzYzOTE3MzM1LCJleHAiOjE3NzE2NTAwMDB9.pKKPZgl67iWGfH8AfvsVH6DQ6-gvAinvJJORYVGdlcU' -o n8n/workflows/Keeper.json
```

The commands above will create `n8n/tmp/workflows.json` and `n8n/workflows/Keeper.json` in the project folder so you can inspect or version them.

## Update the Keeper workflow (minimal payload)

When updating a workflow via the REST API, n8n expects only the allowed top-level fields. Use jq (or the equivalent) to create a minimal JSON and then PUT it.

Example (creates a minimal export and updates the workflow):

```bash
jq '{
   name: .name,
   nodes: .nodes,
   connections: .connections,
   settings: .settings
}' ./n8n/workflows/Keeper.json > ./n8n/tmp/Keeper-minimal.json

curl -X PUT "http://localhost:5693/api/v1/workflows/Nbw7xEIAgNqaxqlo" -H "X-N8N-API-KEY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1MDYwNzhjMC03YjhhLTQ2MjAtOGYxMi03Nzc2ZTVmMzRlYjEiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzYzOTE3MzM1LCJleHAiOjE3NzE2NTAwMDB9.pKKPZgl67iWGfH8AfvsVH6DQ6-gvAinvJJORYVGdlcU" -H "Content-Type: application/json" -d @./n8n/tmp/Keeper-minimal.json
```

This updates the Keeper workflow (id: `Nbw7xEIAgNqaxqlo`) with the minimal JSON saved in `./n8n/tmp/Keeper-minimal.json`.
