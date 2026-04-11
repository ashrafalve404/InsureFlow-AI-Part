"""
Pydantic schemas for Transcript ingestion endpoints.
"""
from typing import Any, Optional, Union, List, Dict, Tuple
from datetime import datetime

from pydantic import BaseModel, Field


# ── Request schemas ────────────────────────────────────────────────────────────

class TranscriptChunkRequest(BaseModel):
    """Payload to ingest a single transcript utterance."""
    session_id: int = Field(..., ge=1, description="ID of the active call session")
    speaker: str = Field(
        ...,
        pattern="^(agent|customer)$",
        description="Who spoke: 'agent' or 'customer'",
    )
    text: str = Field(..., min_length=1, description="The spoken text")
    timestamp: datetime = Field(..., description="When the utterance occurred (ISO 8601)")


# ── Response schemas ───────────────────────────────────────────────────────────

class TranscriptChunkResponse(BaseModel):
    """Stored transcript chunk returned by the API."""
    id: int
    session_id: int
    speaker: str
    text: str
    timestamp: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class TranscriptListResponse(BaseModel):
    """List of transcript chunks for a session."""
    session_id: int
    total: int
    chunks: List[TranscriptChunkResponse]
