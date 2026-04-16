"""
FastAPI application entry point.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import WebSocket

from app.api.routes import calls, health, sessions, suggestions, twilio, websocket, rag, crm
from app.core.config import settings
from app.core.database import create_tables
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events: code to run on app startup and shutdown.
    """
    # Startup actions
    setup_logging()
    await create_tables()
    yield
    # Shutdown actions
    pass


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        description="Backend for Real-Time AI Sales Assistant",
        lifespan=lifespan,
    )

    # Allow CORS for dashboard UI
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify explicit domains
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(health.router)
    app.include_router(websocket.router)
    app.include_router(calls.router, prefix=settings.API_V1_PREFIX)
    app.include_router(sessions.router, prefix=settings.API_V1_PREFIX)
    app.include_router(suggestions.router, prefix=settings.API_V1_PREFIX)
    app.include_router(twilio.router, prefix=settings.API_V1_PREFIX)
    app.include_router(rag.router, prefix=settings.API_V1_PREFIX)
    app.include_router(crm.router, prefix=settings.API_V1_PREFIX)

    # Add Twilio media stream WebSocket at root level (no API prefix)
    @app.websocket("/twilio-media-stream")
    async def twilio_ws(ws: WebSocket):
        # Extract query parameters
        call_sid = ws.query_params.get("call_sid")
        session_id = ws.query_params.get("session_id")
        if session_id:
            session_id = int(session_id)
        await twilio.twilio_media_stream_websocket(ws, call_sid=call_sid, session_id=session_id)

    return app


app = create_app()
