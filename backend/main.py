"""
Call of Cthulhu API - Game Management System
Handles login flow, entity management, and session tracking.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import connect_to_mongo, close_mongo_connection
from app.routes_players import router as players_router
from app.routes_worlds import router as worlds_router
from app.routes_realms import router as realms_router
from app.routes_campaigns import router as campaigns_router
from app.routes_characters import router as characters_router
from app.routes_sessions import router as sessions_router
from app.routes_chapters import router as chapters_router
from app.routes_scenes import router as scenes_router
from app.routes_turns import router as turns_router
from app.routes_action_drafts import router as action_drafts_router
from app.routes_npcs import router as npcs_router
from app.routes_ai import router as ai_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    await connect_to_mongo()
    yield
    # Shutdown
    await close_mongo_connection()


app = FastAPI(
    title="Call of Cthulhu API",
    description="RPG campaign management system with login/selection flow",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3093", "http://localhost:5173", "http://localhost:5174"],  # Vue dev servers and production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(players_router, prefix="/api/v1")
app.include_router(worlds_router, prefix="/api/v1")
app.include_router(realms_router, prefix="/api/v1")
app.include_router(campaigns_router, prefix="/api/v1")
app.include_router(characters_router, prefix="/api/v1")
app.include_router(sessions_router, prefix="/api/v1")
app.include_router(chapters_router, prefix="/api/v1")
app.include_router(scenes_router, prefix="/api/v1")
app.include_router(turns_router, prefix="/api/v1")
app.include_router(action_drafts_router, prefix="/api/v1")
app.include_router(npcs_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Call of Cthulhu API is running",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# ============== Socket.IO Integration ==============

from app.socketio_manager import get_socketio_app

# Wrap FastAPI app with Socket.IO
socket_app = get_socketio_app(app)
