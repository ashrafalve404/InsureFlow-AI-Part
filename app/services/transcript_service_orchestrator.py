"""
Transcript ingestion orchestrator service.

This is the central pipeline that:
  1. Stores the new transcript chunk
  2. Runs AI analysis on recent context
  3. Stores the AI suggestion
  4. Detects and stores objections
  5. Checks and stores compliance flags
  6. Broadcasts all results via WebSocket

Keeping this logic in a dedicated service keeps routes thin and testable.
"""
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services import ai_service, compliance_service, objection_service
from app.services.suggestion_service import store_suggestion
from app.services.transcript_service import (
    chunks_to_dicts,
    get_chunks_for_session,
    store_chunk,
)
from app.services.websocket_manager import ws_manager

logger = logging.getLogger(__name__)


async def ingest_transcript_chunk(
    session_id: int,
    speaker: str,
    text: str,
    timestamp: datetime,
    db: AsyncSession,
) -> dict:
    """
    Full ingestion pipeline for a single transcript utterance.

    Returns a dict summarising what was processed — useful for the API response
    and for verification in tests.
    """

    # ── 1. Store the chunk ──────────────────────────────────────────────────
    chunk = await store_chunk(session_id, speaker, text, timestamp, db)

    # ── 2. Fetch recent context for AI ─────────────────────────────────────
    recent_chunks = await get_chunks_for_session(
        session_id, db, limit=settings.AI_MAX_CONTEXT_CHUNKS
    )
    chunk_dicts = chunks_to_dicts(recent_chunks)

    # ── 3. Run live AI analysis ─────────────────────────────────────────────
    ai_output = await ai_service.generate_live_assistance(chunk_dicts)

    # ── 4. Store AI suggestion ──────────────────────────────────────────────
    suggestion = await store_suggestion(session_id, chunk.id, ai_output, db)

    # ── 5. Detect & store objection (customer utterances only) ──────────────
    objection_label = await objection_service.detect_and_store_objection(
        session_id=session_id,
        chunk_id=chunk.id,
        speaker=speaker,
        text=text,
        db=db,
    )

    # ── 6. Check & store compliance risk (agent utterances only) ────────────
    compliance_warning = await compliance_service.check_and_store_compliance(
        session_id=session_id,
        chunk_id=chunk.id,
        speaker=speaker,
        text=text,
        db=db,
    )

    # ── 7. Build broadcast payload ──────────────────────────────────────────
    broadcast_payload = {
        "event": "transcript_update",
        "session_id": session_id,
        "transcript": {
            "id": chunk.id,
            "speaker": chunk.speaker,
            "text": chunk.text,
            "timestamp": chunk.timestamp.isoformat(),
        },
        "ai_suggestion": {
            "id": suggestion.id,
            "suggested_response": suggestion.suggested_response,
            "objection_label": suggestion.objection_label,
            "compliance_warning": suggestion.compliance_warning,
            "call_stage": suggestion.call_stage,
        },
        "objection_detected": objection_label != "none",
        "objection_label": objection_label,
        "compliance_alert": compliance_warning,
    }

    # ── 8. Broadcast via WebSocket ──────────────────────────────────────────
    await ws_manager.broadcast(session_id, broadcast_payload)
    logger.info(
        "Transcript ingested | session=%s chunk=%s stage=%s objection=%s",
        session_id,
        chunk.id,
        suggestion.call_stage,
        objection_label,
    )

    return broadcast_payload
