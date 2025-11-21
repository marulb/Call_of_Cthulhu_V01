# Call of Cthulhu Project Setup

## Project Structure to Create

```
/shared/projects_martin/Call_of_Cthulhu_01/
├── .gitignore
├── docker-compose.yml
├── README.md
├── Call_of_Cthulhu_01.code-workspace
├── frontend/
│   ├── Dockerfile
│   ├── .gitignore
│   └── (Vue.js project files - to be created separately)
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── .gitignore
│   └── app/
├── n8n/
│   └── .gitkeep
└── database/
    ├── mongodb/
    ├── n8n-mongodb/
    └── qdrant/
```

## Files to Create

### 1. Root .gitignore
```gitignore
# Databases
database/

# Environment
.env
*.log

# OS
.DS_Store
Thumbs.db
```

### 2. docker-compose.yml
```yaml
version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - "3093:80"
    depends_on:
      - backend
    networks:
      - coc-network

  backend:
    image: fastapi_01:latest
    volumes:
      - ./backend:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8093:8000"
    environment:
      - MONGODB_URL=mongodb://mongodb:27017/coc_db
      - QDRANT_URL=http://qdrant:6333
      - OLLAMA_URL=http://host.docker.internal:11434
    depends_on:
      - mongodb
      - qdrant
    networks:
      - coc-network
    extra_hosts:
      - "host.docker.internal:host-gateway"

  n8n:
    image: n8nio/n8n:latest
    ports:
      - "5693:5678"
    environment:
      - DB_TYPE=mongodb
      - DB_MONGODB_CONNECTION_URL=mongodb://n8n-mongodb:27017/n8n
      - N8N_HOST=0.0.0.0
      - WEBHOOK_URL=http://localhost:5678/
      - OLLAMA_HOST=http://host.docker.internal:11434
    volumes:
      - ./n8n:/home/node/.n8n
    depends_on:
      - n8n-mongodb
    networks:
      - coc-network
    extra_hosts:
      - "host.docker.internal:host-gateway"

  n8n-mongodb:
    image: mongo:latest
    volumes:
      - ./database/n8n-mongodb:/data/db
    networks:
      - coc-network

  mongodb:
    image: mongo:latest
    volumes:
      - ./database/mongodb:/data/db
    ports:
      - "27093:27017"
    networks:
      - coc-network

  qdrant:
    image: qdrant/qdrant:latest
    volumes:
      - ./database/qdrant:/qdrant/storage
    ports:
      - "6393:6333"
    networks:
      - coc-network

networks:
  coc-network:
    driver: bridge
```

### 3. frontend/Dockerfile
```dockerfile
FROM node:18-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 4. frontend/.gitignore
```gitignore
node_modules/
dist/
.env.local
.env.*.local
```

### 5. backend/.gitignore
```gitignore
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
```

### 6. backend/main.py (starter)
```python
from fastapi import FastAPI

app = FastAPI(title="Call of Cthulhu API")

@app.get("/")
async def root():
    return {"message": "Call of Cthulhu API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

### 7. backend/requirements.txt
```txt
# Additional requirements beyond fastapi_01 base image
# Add project-specific packages here
```

### 8. Call_of_Cthulhu_01.code-workspace
```json
{
  "folders": [
    {"path": ".", "name": "Root"},
    {"path": "frontend", "name": "Frontend"},
    {"path": "backend", "name": "Backend"}
  ],
  "settings": {
    "files.exclude": {
      "**/__pycache__": true,
      "**/node_modules": true,
      "database": true
    }
  }
}
```

### 9. README.md
```markdown
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
```

### 10. n8n/.gitkeep
Empty file to track the directory in Git.

## Git Initialization Commands

**IMPORTANT: Run this manually in your VSCode terminal FIRST (before Claude Code executes git commands):**

```bash
# Start SSH agent and add key (enter passphrase when prompted)
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/git_marulb
# Enter your passphrase interactively
```

**After SSH agent is running, Claude Code can execute:**

```bash
cd /shared/projects_martin/Call_of_Cthulhu_01
git init
git add .
git commit -m "Initial project setup with Docker Compose, FastAPI, Vue.js, n8n"
git remote add origin git@github.com:marulb/Call_of_Cthulhu_V01.git
git branch -M main
git push -u origin main
```

## Notes
- Ollama instance running on host port 11434 (standard instance)
- Docker image `fastapi_01:latest` already built with base dependencies
- Database volumes will be created automatically on first run
- n8n workflows will be saved in ./n8n/ directory (versionable)