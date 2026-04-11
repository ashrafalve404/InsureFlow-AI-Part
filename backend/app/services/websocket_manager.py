"""
WebSocket connection manager.
Maintains a registry of active connections per call session
and provides broadcast utilities.
"""
from typing import Any, Optional, Union, List, Dict, Tuple
import json
import logging
from collections import defaultdict

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages active WebSocket connections grouped by session_id.
    Thread-safe for single-process asyncio deployments.
    """

    def __init__(self) -> None:
        # session_id -> list of active WebSocket connections
        self._connections: Dict[int, List[WebSocket]] = defaultdict(list)

    async def connect(self, session_id: int, websocket: WebSocket) -> None:
        """Accept and register a WebSocket connection for a given session."""
        await websocket.accept()
        self._connections[session_id].append(websocket)
        logger.info(
            "WebSocket connected | session=%s | total_clients=%s",
            session_id,
            len(self._connections[session_id]),
        )

    def disconnect(self, session_id: int, websocket: WebSocket) -> None:
        """Remove a WebSocket connection from the registry."""
        connections = self._connections.get(session_id, [])
        if websocket in connections:
            connections.remove(websocket)
        if not connections:
            self._connections.pop(session_id, None)
        logger.info(
            "WebSocket disconnected | session=%s | remaining=%s",
            session_id,
            len(self._connections.get(session_id, [])),
        )

    async def broadcast(self, session_id: int, payload: dict) -> None:
        """
        Send a JSON payload to all connected clients for a session.
        Stale / closed connections are cleaned up automatically.
        """
        connections = list(self._connections.get(session_id, []))
        if not connections:
            return

        message = json.dumps(payload, default=str)
        dead: List[WebSocket] = []

        for ws in connections:
            try:
                await ws.send_text(message)
            except Exception as exc:
                logger.warning("WebSocket send failed: %s", exc)
                dead.append(ws)

        # Clean up broken connections
        for ws in dead:
            self.disconnect(session_id, ws)

    def active_sessions(self) -> List[int]:
        """Return a list of session IDs that have active WebSocket clients."""
        return list(self._connections.keys())

    def client_count(self, session_id: int) -> int:
        """Return number of active clients for a session."""
        return len(self._connections.get(session_id, []))


# Singleton instance shared across the application lifetime
ws_manager = WebSocketManager()
