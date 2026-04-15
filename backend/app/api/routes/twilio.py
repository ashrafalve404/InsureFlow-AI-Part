"""
Twilio webhook and transcript event endpoints.

POST /api/twilio/voice       — receive Twilio incoming calls (returns TwiML)
POST /api/twilio/webhook     — receive Twilio call lifecycle events
POST /api/twilio/transcript   — receive live or simulated transcript events
"""
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.schemas.twilio import TwilioTranscriptEvent, TwilioWebhookResponse
from app.services import call_service
from app.services.transcript_service_orchestrator import ingest_transcript_chunk
from app.services.twilio_service import twilio_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/twilio", tags=["Twilio"])


@router.post(
    "/voice",
    response_class=PlainTextResponse,
    summary="Twilio Voice webhook - handles incoming calls",
)
async def twilio_voice_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> PlainTextResponse:
    """
    Handle incoming Twilio voice calls.
    
    This is the main webhook URL Twilio calls when a call comes in.
    Returns TwiML to connect to the live transcription + AI assistant.
    """
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "")
    from_number = form_data.get("From", "")
    to_number = form_data.get("To", "")
    call_status = form_data.get("CallStatus", "")
    
    logger.info(f"Twilio voice webhook: call_sid={call_sid}, from={from_number}, status={call_status}")
    
    # Create session if call is incoming
    if call_status == "ringing" and call_sid:
        session = await call_service.create_session(
            call_sid=call_sid,
            agent_name="Agent",
            customer_phone=from_number,
            db=db,
        )
        logger.info(f"Created session {session.id} for call {call_sid}")
    
    # Get sales person number from config
    sales_number = settings.SALES_PERSON_NUMBER or "+8801335117990"
    
    # Return TwiML to transfer call to sales person
    twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Connecting you to an agent. Please wait.</Say>
    <Dial record="true" recordingStatusCallback="/api/v1/twilio/recording-status">
        <Number>{sales_number}</Number>
    </Dial>
</Response>"""
    
    return PlainTextResponse(content=twiml_response, media_type="application/xml")


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
    "/recording-status",
    response_model=TwilioWebhookResponse,
    summary="Twilio recording status callback",
)
async def twilio_recording_status(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TwilioWebhookResponse:
    """
    Handle Twilio recording status callbacks.
    """
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "")
    recording_status = form_data.get("RecordingStatus", "")
    
    logger.info(f"Recording status: call_sid={call_sid}, status={recording_status}")
    
    return TwilioWebhookResponse(received=True, message="Recording status received.")


@router.websocket("/media-stream")
async def twilio_media_stream(websocket: WebSocket):
    """
    WebSocket endpoint for Twilio Media Stream.
    Receives audio from Twilio and sends to Deepgram for transcription.
    """
    await websocket.accept()
    
    from deepgram import Deepgram
    from deepgram.exceptions import DeepgramException
    
    dg_connection = None
    call_sid = None
    
    try:
        # Initialize Deepgram client
        dg_client = Deepgram(settings.DEEPGRAM_API_KEY)
        
        # Connect to Deepgram
        dg_connection = await dg_client.transcription.live(
            {
                "punctuate": True,
                "interim_results": True,
                "language": "en",
                "model": "nova-2",
            }
        )
        
        async def on_transcript(event_type, transcription, **kwargs):
            """Handle transcription results from Deepgram."""
            if event_type == "Transcript":
                transcript_text = transcription.get("channel", {}).get("alternatives", [{}])[0].get("transcript", "")
                is_final = transcription.get("is_final", False)
                
                if transcript_text and call_sid:
                    logger.info(f"Transcription: {transcript_text} (final={is_final})")
                    
                    # TODO: Save to database and trigger AI suggestions
                    # For now, broadcast via WebSocket to frontend
        
        dg_connection.on("transcript", on_transcript)
        
        while True:
            # Receive message from Twilio
            data = await websocket.receive_text()
            import json
            message = json.loads(data)
            
            event = message.get("event")
            
            if event == "start":
                call_sid = message.get("callSid")
                logger.info(f"Media stream started for call {call_sid}")
                
            elif event == "media":
                # Forward audio to Deepgram
                media = message.get("media", "")
                if media and dg_connection:
                    dg_connection.send(media)
                    
            elif event == "stop":
                logger.info(f"Media stream stopped for call {call_sid}")
                break
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"Media stream error: {e}")
    finally:
        if dg_connection:
            dg_connection.finish()
        await websocket.close()


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
