"""
Twilio webhook and transcript event endpoints.

POST /api/twilio/voice       — receive Twilio incoming calls (returns TwiML)
POST /api/twilio/webhook     — receive Twilio call lifecycle events
POST /api/twilio/transcript   — receive live or simulated transcript events
"""
import asyncio
import base64
import json
import logging
import os
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, AsyncSessionLocal
from app.core.config import settings
from app.schemas.twilio import TwilioTranscriptEvent, TwilioWebhookResponse
from app.services import call_service
from app.services.transcript_service_orchestrator import ingest_transcript_chunk
from app.services.twilio_service import twilio_service
from app.services.websocket_manager import ws_manager

logger = logging.getLogger(__name__)
# IMPORTANT: Ensure the prefix is correct
router = APIRouter(prefix="/twilio", tags=["Twilio"])

# Active Deepgram connections per call
active_stream_connections = {}


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
    Handle incoming Twilio voice calls with Media Stream support.
    """
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "")
    from_number = form_data.get("From", "")
    to_number = form_data.get("To", "")
    call_status = form_data.get("CallStatus", "")
    
    logger.info(f"Twilio voice webhook: call_sid={call_sid}, from={from_number}, status={call_status}")
    
    # Check if session already exists
    from sqlalchemy import select
    from app.models.call_session import CallSession
    
    result = await db.execute(
        select(CallSession).where(CallSession.call_sid == call_sid)
    )
    existing_session = result.scalar_one_or_none()
    
    session = None
    
    # Create session only if call is incoming and no existing session
    if call_status == "ringing" and call_sid and not existing_session:
        session = await call_service.create_session_minimal(
            call_sid=call_sid,
            agent_name="Agent",
            customer_phone=from_number,
            db=db,
        )
        logger.info(f"Created session {session.id} for call {call_sid}")
    
    # Get sales person number
    sales_number = settings.SALES_PERSON_NUMBER or "+8801723343865"
    
    # Get the base URL for WebSocket (favor the specific env var, then fallback)
    ws_base_url = os.environ.get("MEDIA_STREAM_WS_URL") or os.environ.get("MEDIA_STREAM_URL")
    if ws_base_url:
        # If it's a full URL, just get the base
        if ws_base_url.startswith("http"):
            ws_base_url = ws_base_url.replace("http", "ws", 1)
        if "/api/v1" in ws_base_url:
            ws_base_url = ws_base_url.split("/api/v1")[0]
    else:
        ws_base_url = "wss://sanded-paralyses-unstuffed.ngrok-free.dev"

    stream_url = f"{ws_base_url}/twilio-media-stream?call_sid={call_sid}"
    
    # Robust TwiML with Streaming restored
    stream_url = f"{ws_base_url}/twilio-media-stream?call_sid={call_sid}&amp;session_id={session.id if session else ''}"
    
    twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Please wait while we connect you to an agent.</Say>
    <Start>
        <Stream url="{stream_url}" track="inbound_track" />
    </Start>
    <Dial callerId="{to_number}" timeout="30" answerOnBridge="true">
        <Number>{sales_number}</Number>
    </Dial>
</Response>"""
    
    logger.info(f"Generated TwiML:\n{twiml_response}")
    
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

    # Validate Twilio signature in production
    # Map call_sid to a CallSession and update status accordingly
    if call_status in ("completed", "failed", "busy", "no-answer", "canceled"):
        from app.models.call_session import CallSession
        from sqlalchemy import select
        
        result = await db.execute(
            select(CallSession).where(CallSession.call_sid == call_sid)
        )
        session = result.scalar_one_or_none()
        
        if session and session.status == "active":
            session.status = "ended"
            session.ended_at = datetime.utcnow()
            await db.commit()
            await ws_manager.broadcast(session.id, {"type": "session_ended", "status": "ended"})

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


# Media Stream WebSocket - registered at root level to avoid prefix issues
# This endpoint handles real-time audio streaming from Twilio
@router.websocket("/media-stream")
async def twilio_media_stream(websocket: WebSocket):
    """
    WebSocket endpoint for Twilio Media Stream.
    Receives audio from Twilio and sends to Deepgram for transcription.
    """
    await websocket.accept()
    
    import json
    import base64
    from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents
    from app.core.database import AsyncSessionLocal
    
    dg_connection = None
    call_sid = websocket.query_params.get("call_sid")
    session_id = websocket.query_params.get("session_id")
    
    logger.info(f"Stream connection attempt: call_sid={call_sid}, session_id={session_id}")
    
    try:
        # Initialize Deepgram
        dg_client = DeepgramClient(settings.DEEPGRAM_API_KEY)
        dg_connection = dg_client.listen.asynclive.v("1")
        
        # Callback for transcripts
        async def on_transcript(self, result, **kwargs):
            transcript_text = result.channel.alternatives[0].transcript
            if not transcript_text or not call_sid:
                return
                
            is_final = result.is_final
            logger.info(f"Deepgram: {transcript_text} (final={is_final})")
            
            async with AsyncSessionLocal() as db:
                from sqlalchemy import select
                from app.models.call_session import CallSession
                from app.services.transcript_service_orchestrator import ingest_transcript_chunk
                
                # Find the session for this call
                stmt = select(CallSession).where(CallSession.call_sid == call_sid)
                db_res = await db.execute(stmt)
                session = db_res.scalar_one_or_none()
                
                if session:
                    speaker = "customer" if is_final else "agent"
                    try:
                        res = await ingest_transcript_chunk(
                            session_id=session.id,
                            speaker=speaker,
                            text=transcript_text,
                            timestamp=datetime.utcnow(),
                            db=db
                        )
                        
                        # Broadcast to UI
                        await ws_manager.broadcast(
                            session.id,
                            {
                                "type": "transcript_update",
                                "transcript": {
                                    "speaker": speaker,
                                    "text": transcript_text,
                                    "timestamp": datetime.utcnow().isoformat(),
                                },
                                "ai_suggestion": res.get("ai_suggestion", {}),
                            }
                        )
                    except Exception as e:
                        logger.error(f"Error in transcript chunk: {e}")

        dg_connection.on(LiveTranscriptionEvents.Transcript, on_transcript)
        
        options = LiveOptions(
            model="nova-2",
            language="en-US",
            smart_format=True,
            interim_results=False, # Disable partial sentences
            endpointing=300, # Faster cut-offs
            encoding="mulaw",
            sample_rate=8000,
        )
        
        if not await dg_connection.start(options):
            logger.error("Could not start Deepgram")
            return

        # Main message loop
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            event = message.get("event")
            
            if event == "start":
                call_sid = message.get("callSid")
                logger.info(f"Stream started: {call_sid}")
            elif event == "media":
                media_data = message.get("media", {})
                payload = media_data.get("payload")
                if payload and dg_connection:
                    try:
                        dg_connection.send(base64.b64decode(payload))
                    except Exception as e:
                        logger.error(f"Error sending to Deepgram: {e}")
            elif event == "stop":
                logger.info(f"Stream stopped: {call_sid}")
                break
                
    except WebSocketDisconnect:
        logger.info("Twilio disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if dg_connection:
            await dg_connection.finish()
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


# WebSocket endpoint for Twilio Media Stream (at root level)
async def twilio_media_stream_websocket(websocket: WebSocket, call_sid: str = None, session_id: int = None):
    """
    WebSocket endpoint to receive audio from Twilio Media Stream.
    Integrates with Deepgram for real-time transcription and OpenAI for AI suggestions.
    """
    await websocket.accept()
    
    dg_connection = None
    call_sid_val = call_sid
    session_id_val = session_id
    
    logger.info(f"Twilio media stream connected: call_sid={call_sid_val}, session_id={session_id_val}")
    
    try:
        # Use the same logic as the other websocket
        from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents
        dg_client = DeepgramClient(settings.DEEPGRAM_API_KEY)
        dg_connection = dg_client.listen.asynclive.v("1")
        
        options = LiveOptions(
            model="nova-2",
            language="en-US",
            smart_format=True,
            interim_results=False, # Disable partial sentences
            endpointing=300, # Faster cut-offs
            encoding="mulaw",
            sample_rate=8000,
        )

        async def on_message(self, result, **kwargs):
            try:
                transcript_text = ""
                is_final = False
                
                # Safely handle both dict and object formats
                if isinstance(result, dict):
                    if result.get("type", "") != "Results":
                        return
                    is_final = result.get("is_final", False)
                    alts = result.get("channel", {}).get("alternatives", [])
                    if not alts: return
                    transcript_text = alts[0].get("transcript", "")
                else:
                    if getattr(result, "type", "") != "Results":
                        return
                    is_final = getattr(result, "is_final", False)
                    if not hasattr(result, "channel") or not result.channel.alternatives:
                        return
                    transcript_text = result.channel.alternatives[0].transcript

                if not transcript_text or not is_final:
                    return
                
                logger.info(f"Deepgram transcript: '{transcript_text}'")
                
                from app.core.database import AsyncSessionLocal
                from sqlalchemy import select
                from app.models.call_session import CallSession
                
                async with AsyncSessionLocal() as db:
                    # Dynamically look up session if we have the call SID
                    current_sid = getattr(self, "call_sid_val", call_sid_val)
                    if not current_sid:
                        return
                        
                    stmt = select(CallSession).where(CallSession.call_sid == current_sid)
                    db_res = await db.execute(stmt)
                    session = db_res.scalar_one_or_none()
                    
                    if not session:
                        return
                        
                    res = await ingest_transcript_chunk(
                        session_id=session.id,
                        speaker="customer", # Minimal logic for stream
                        text=transcript_text,
                        timestamp=datetime.utcnow(),
                        db=db,
                    )
                    
                    await ws_manager.broadcast(
                        session.id,
                        {
                            "type": "transcript_update",
                            "transcript": {
                                "speaker": "customer",
                                "text": transcript_text,
                                "timestamp": datetime.utcnow().isoformat(),
                            },
                            "ai_suggestion": res.get("ai_suggestion", {}),
                        }
                    )
            except Exception as e:
                logger.error(f"Error in on_message: {e}")

        async def on_error(self, error, **kwargs):
            logger.error(f"Deepgram SDK Error Event: {error}")

        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        dg_connection.on(LiveTranscriptionEvents.Error, on_error)
        
        if not await dg_connection.start(options):
            logger.error("Failed to start Deepgram connection")
            return

        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                event = message.get("event")
                if event == "start":
                    start_data = message.get("start", {})
                    call_sid_val = start_data.get("callSid") or message.get("callSid", call_sid_val)
                    setattr(dg_connection, "call_sid_val", call_sid_val)
                    logger.info(f"Stream started: call_sid_val={call_sid_val}")
                elif event == "media":
                    media_data = message.get("media", {})
                    track = media_data.get("track", "inbound")
                    if track != "inbound":
                        continue
                        
                    payload = media_data.get("payload")
                    if payload and dg_connection:
                        try:
                            audio_data = base64.b64decode(payload)
                            await dg_connection.send(audio_data)
                        except Exception as e:
                            logger.error(f"Error sending to Deepgram: {e}")
                elif event == "stop":
                    break
            except Exception as e:
                break
                
    except Exception as e:
        logger.error(f"Media stream error: {e}")
    finally:
        if dg_connection:
            try:
                await dg_connection.finish()
            except:
                pass
        await websocket.close()
        
        # Mark session as ended when stream closes
        if call_sid_val:
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import select
            from app.models.call_session import CallSession
            
            async with AsyncSessionLocal() as db:
                stmt = select(CallSession).where(CallSession.call_sid == call_sid_val)
                db_res = await db.execute(stmt)
                session = db_res.scalar_one_or_none()
                if session and session.status == "active":
                    session.status = "ended"
                    session.ended_at = datetime.utcnow()
                    await db.commit()
                    await ws_manager.broadcast(session.id, {"type": "session_ended", "status": "ended"})
                    
        logger.info(f"Media stream closed for call {call_sid_val}")
