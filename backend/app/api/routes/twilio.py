"""
Twilio webhook and transcript event endpoints.

POST /api/twilio/webhook     — receive Twilio call lifecycle events
POST /api/twilio/transcript  — receive live or simulated transcript events
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.twilio import TwilioTranscriptEvent, TwilioWebhookResponse
from app.services import call_service
from app.services.transcript_service_orchestrator import ingest_transcript_chunk
from app.services.twilio_service import twilio_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/twilio", tags=["Twilio"])


@router.post(
    "/webhook",
    response_model=TwilioWebhookResponse,
    summary="Receive Twilio call lifecycle webhook",
    description=(
        "Twilio sends POST requests here on call events (ringing, in-progress, completed). "
        "In production wire up Twilio signature validation in app/core/security.py."
    ),
)
async def twilio_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TwilioWebhookResponse:
    """
    Handle Twilio webhook events.

    Twilio sends application/x-www-form-urlencoded POSTs; we read them via
    request.form() and pass the data through the service layer.
    """
    try:
        form_data = dict(await request.form())
    except Exception:
        form_data = {}

    event = twilio_service.parse_webhook_event(form_data)
    call_sid = event.get("call_sid")
    call_status = event.get("call_status", "")

    logger.info(
        "Twilio webhook received | call_sid=%s status=%s", call_sid, call_status
    )

    # TODO: In production, validate Twilio signature with:
    #   from app.core.security import verify_twilio_signature
    #   signature = request.headers.get("X-Twilio-Signature", "")
    #   verify_twilio_signature(signature, str(request.url), form_data)

    # TODO: Map call_sid to a CallSession and update status accordingly
    # Example: if call_status == "completed": await call_service.end_session(...)

    return TwilioWebhookResponse(received=True, message="Webhook processed.")


@router.post(
    "/transcript",
    status_code=status.HTTP_201_CREATED,
    summary="Receive real-time or simulated transcript event from Twilio",
    description=(
        "Accepts a transcript utterance associated with a Twilio Call SID. "
        "The session is looked up by call_sid. "
        "When live Twilio Transcription is active, route its output here."
    ),
)
async def twilio_transcript_event(
    payload: TwilioTranscriptEvent,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Ingest a Twilio transcript event.

    1. Look up the CallSession by call_sid.
    2. Run the full transcript ingestion pipeline.
    3. Broadcast AI results via WebSocket.
    """
    from sqlalchemy import select
    from app.models.call_session import CallSession

    # Find session by Twilio call_sid
    result = await db.execute(
        select(CallSession).where(CallSession.call_sid == payload.call_sid)
    )
    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No session found for call_sid={payload.call_sid}. "
                   "Create a session first via POST /api/calls/start.",
        )

    if session.status == "ended":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Session for call_sid={payload.call_sid} has already ended.",
        )

    # Parse timestamp — accept ISO string
    try:
        timestamp = datetime.fromisoformat(payload.timestamp)
        if timestamp.tzinfo is not None:
            timestamp = timestamp.replace(tzinfo=None)
    except ValueError:
        timestamp = datetime.utcnow()

    ingestion_result = await ingest_transcript_chunk(
        session_id=session.id,
        speaker=payload.speaker,
        text=payload.text,
        timestamp=timestamp,
        db=db,
    )

    return ingestion_result
