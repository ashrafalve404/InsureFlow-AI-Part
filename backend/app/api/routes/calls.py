"""
Call session endpoints.

POST /api/calls/start     — create a new call session
GET  /api/calls           — list all sessions (paginated)
GET  /api/calls/{id}      — get session details
POST /api/calls/{id}/end  — end a session and trigger post-call summary
"""
from typing import Any, Optional, List
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.call import (
    CallSessionListResponse,
    CallSessionResponse,
    StartCallRequest,
)
from app.schemas.suggestion import PostCallSummaryResponse
from app.services import call_service
from app.services.summary_service import generate_summary
from app.services.websocket_manager import ws_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/calls", tags=["Call Sessions"])


@router.post(
    "/start",
    response_model=CallSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new call session",
)
async def start_call(
    payload: StartCallRequest,
    db: AsyncSession = Depends(get_db),
) -> CallSessionResponse:
    """Create a new active call session. Optionally attach a Twilio Call SID."""
    session = await call_service.create_session(payload, db)
    return CallSessionResponse.model_validate(session)


@router.get(
    "",
    response_model=CallSessionListResponse,
    summary="List all call sessions",
)
async def list_calls(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=50, ge=1, le=200, description="Max records to return"),
    db: AsyncSession = Depends(get_db),
) -> CallSessionListResponse:
    """Return a paginated list of all call sessions, newest first."""
    total, sessions = await call_service.list_sessions(db, skip=skip, limit=limit)
    return CallSessionListResponse(
        total=total,
        sessions=[CallSessionResponse.model_validate(s) for s in sessions],
    )


@router.get(
    "/{session_id}",
    response_model=CallSessionResponse,
    summary="Get a single call session",
)
async def get_call(
    session_id: int,
    db: AsyncSession = Depends(get_db),
) -> CallSessionResponse:
    """Return details for a single call session by its ID."""
    session = await call_service.get_session(session_id, db)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call session {session_id} not found.",
        )
    return CallSessionResponse.model_validate(session)


@router.post(
    "/{session_id}/end",
    summary="End an active call session",
)
async def end_call(
    session_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Mark a call session as ended, generate a post-call summary,
    and broadcast the summary to any connected WebSocket clients.
    """
    session = await call_service.end_session(session_id, db)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call session {session_id} not found.",
        )

    # Generate post-call summary
    summary = await generate_summary(session_id, db)

    # Broadcast session-ended event to WebSocket subscribers
    await ws_manager.broadcast(
        session_id,
        {
            "event": "session_ended",
            "session_id": session_id,
            "summary": summary.model_dump(),
        },
    )

    logger.info("Call session ended and summary broadcast | session=%s", session_id)

    return {
        "message": "Call session ended successfully.",
        "session_id": session_id,
        "status": session.status,
        "ended_at": session.ended_at,
        "summary": summary.model_dump(),
    }

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_call(session_id: int, db: AsyncSession = Depends(get_db)):
    """Hard delete a call session and all its associated data (transcripts, etc)."""
    from app.models.call_session import CallSession
    from sqlalchemy import select
    result = await db.execute(select(CallSession).where(CallSession.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    await db.delete(session)
    await db.commit()
    return None
