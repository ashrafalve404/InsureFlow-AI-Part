"""
Transcript ingestion and retrieval endpoints.

POST /api/transcripts                       — ingest a new transcript chunk
GET  /api/calls/{session_id}/transcripts    — list all chunks for a session
"""
from typing import Any, Optional, Union, List, Dict, Tuple
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.transcript import (
    TranscriptChunkRequest,
    TranscriptChunkResponse,
    TranscriptListResponse,
)
from app.services import call_service
from app.services.transcript_service import chunks_to_dicts, get_chunks_for_session
from app.services.transcript_service_orchestrator import ingest_transcript_chunk

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Transcripts"])


@router.post(
    "/transcripts",
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a real-time transcript chunk",
    description=(
        "Receives a single utterance, runs AI analysis, stores results, "
        "and broadcasts the update to all WebSocket subscribers for this session."
    ),
)
async def ingest_transcript(
    payload: TranscriptChunkRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Core real-time endpoint.

    Pipeline triggered on every transcript chunk:
    1. Store transcript chunk
    2. Fetch recent context
    3. Run AI analysis (suggestion + stage)
    4. Detect objection (rule-based + AI)
    5. Detect compliance risk (rule-based + AI)
    6. Broadcast via WebSocket
    """
    # Validate session exists and is still active
    session = await call_service.get_session(payload.session_id, db)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call session {payload.session_id} not found.",
        )
    if session.status == "ended":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Call session {payload.session_id} has already ended.",
        )

    result = await ingest_transcript_chunk(
        session_id=payload.session_id,
        speaker=payload.speaker,
        text=payload.text,
        timestamp=payload.timestamp,
        db=db,
    )

    return result


@router.get(
    "/calls/{session_id}/transcripts",
    response_model=TranscriptListResponse,
    summary="Get all transcript chunks for a session",
)
async def get_transcripts(
    session_id: int,
    db: AsyncSession = Depends(get_db),
) -> TranscriptListResponse:
    """Return the full ordered transcript for a given call session."""
    session = await call_service.get_session(session_id, db)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call session {session_id} not found.",
        )

    chunks = await get_chunks_for_session(session_id, db)
    return TranscriptListResponse(
        session_id=session_id,
        total=len(chunks),
        chunks=[TranscriptChunkResponse.model_validate(c) for c in chunks],
    )
