"""
Pydantic schemas for Call Session endpoints.
"""
from typing import Any, Optional, Union, List, Dict, Tuple
from datetime import datetime

from pydantic import BaseModel, Field


# ── Request schemas ────────────────────────────────────────────────────────────

class StartCallRequest(BaseModel):
    """Payload to create a new call session."""
    agent_name: str = Field(..., min_length=1, max_length=128, examples=["Jane Smith"])
    customer_name: str = Field(..., min_length=1, max_length=128, examples=["John Doe"])
    customer_phone: str = Field(..., min_length=5, max_length=32, examples=["+15551234567"])
    call_sid: Optional[str] = Field(
        default=None,
        max_length=64,
        description="Optional Twilio Call SID",
        examples=["CA1234567890abcdef"],
    )


# ── Response schemas ───────────────────────────────────────────────────────────

class CallSessionResponse(BaseModel):
    """Full call session detail returned by the API."""
    id: int
    call_sid: Optional[str]
    agent_name: str
    customer_name: str
    customer_phone: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class CallSessionListResponse(BaseModel):
    """Paginated list of call sessions."""
    total: int
    sessions: List[CallSessionResponse]


class EndCallResponse(BaseModel):
    """Response returned when a session is ended."""
    message: str
    session_id: int
    status: str
    ended_at: datetime
