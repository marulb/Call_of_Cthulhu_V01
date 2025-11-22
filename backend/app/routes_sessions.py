"""
API routes for Session entities.
Sessions are stored in the gamerecords database.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from .models import Session, SessionCreate, Change, Meta, EntityKind, Attendance
from .database import get_gamerecords_db
from datetime import datetime
import uuid

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=List[Session])
async def list_sessions(
    realm_id: Optional[str] = Query(None),
    campaign_id: Optional[str] = Query(None)
):
    """List sessions, optionally filtered by realm_id and/or campaign_id."""
    db = get_gamerecords_db()

    query = {}
    if realm_id:
        query["realm_id"] = realm_id
    if campaign_id:
        query["campaign_id"] = campaign_id

    sessions = await db.sessions.find(query).sort("session_number", -1).to_list(length=100)
    return sessions


@router.get("/latest", response_model=Optional[Session])
async def get_latest_session(
    realm_id: str = Query(...),
    campaign_id: str = Query(...)
):
    """Get the latest session for a specific realm and campaign."""
    db = get_gamerecords_db()

    session = await db.sessions.find_one(
        {"realm_id": realm_id, "campaign_id": campaign_id},
        sort=[("session_number", -1)]
    )

    return session


@router.get("/{session_id}", response_model=Session)
async def get_session(session_id: str):
    """Get a specific session by ID."""
    db = get_gamerecords_db()
    session = await db.sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("", response_model=Session)
async def create_session(session_data: SessionCreate):
    """Create a new session."""
    db = get_gamerecords_db()

    # Generate unique ID
    session_id = f"session-{uuid.uuid4().hex[:8]}"

    # Create session document
    session = Session(
        id=session_id,
        kind=EntityKind.SESSION,
        realm_id=session_data.realm_id,
        campaign_id=session_data.campaign_id,
        session_number=session_data.session_number,
        attendance=Attendance(
            players_present=session_data.players_present,
            players_absent=session_data.players_absent
        ),
        notes=session_data.notes,
        meta=Meta(created_by=session_data.created_by),
        changes=[Change(by=session_data.created_by, type="created")]
    )

    # Insert into database
    await db.sessions.insert_one(session.dict())

    return session


@router.put("/{session_id}", response_model=Session)
async def update_session(session_id: str, session_data: SessionCreate):
    """Update an existing session."""
    db = get_gamerecords_db()

    # Find existing session
    existing = await db.sessions.find_one({"id": session_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Session not found")

    # Update fields
    existing["session_number"] = session_data.session_number
    existing["attendance"]["players_present"] = session_data.players_present
    existing["attendance"]["players_absent"] = session_data.players_absent
    existing["notes"] = session_data.notes

    # Add change record
    existing["changes"].append(
        Change(by=session_data.created_by, at=datetime.utcnow(), type="updated").dict()
    )

    # Save to database
    await db.sessions.replace_one({"id": session_id}, existing)

    return Session(**existing)


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    db = get_gamerecords_db()

    result = await db.sessions.delete_one({"id": session_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"message": "Session deleted successfully"}
