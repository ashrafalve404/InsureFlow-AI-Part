"""
WebSocket endpoint for real-time dashboard streaming.

WS /ws/calls/{session_id}

Clients connect here to receive live updates for a call session:
  - transcript_update  — new chunk + AI suggestion
  - session_ended      — post-call summary
  - ping/pong          — keepalive
"""
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.websocket_manager import ws_manager

logger = logging.getLogger(__name__)
router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/calls/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: int) -> None:
    """
    WebSocket endpoint for a specific call session.

    Connect to receive real-time events as JSON:
        ws://localhost:8000/ws/calls/{session_id}

    Supported inbound messages (from client):
        {"type": "ping"} → server replies {"type": "pong"}

    Outbound events (from server):
        {"event": "transcript_update", ...}
        {"event": "session_ended", ...}
    """
    await ws_manager.connect(session_id, websocket)
    logger.info("WebSocket client joined session=%s", session_id)

    try:
        # Send an immediate welcome confirmation
        await websocket.send_json(
            {
                "event": "connected",
                "session_id": session_id,
                "message": f"Subscribed to call session {session_id}. Awaiting updates.",
            }
        )

        # Keep connection alive; handle inbound client messages
        while True:
            try:
                raw = await websocket.receive_text()
                data = json.loads(raw)
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass  # Ignore unparseable messages from client

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected from session=%s", session_id)
    except Exception as exc:
        logger.warning("WebSocket error session=%s: %s", session_id, exc)
    finally:
        ws_manager.disconnect(session_id, websocket)
