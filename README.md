# Call of Cthulhu Project

RPG campaign management system with Vue.js frontend and FastAPI backend.

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
