"""
Pydantic schemas for Twilio webhook events.
"""
from typing import Any, Optional, Union, List, Dict, Tuple
from pydantic import BaseModel, Field


class TwilioWebhookEvent(BaseModel):
    """
    Represents the minimal body of a Twilio voice webhook POST.
    Twilio sends form-encoded data; FastAPI will parse it as a regular body here.
    """
    CallSid: Optional[str] = Field(default=None, description="Twilio Call SID")
    CallStatus: Optional[str] = Field(default=None, description="e.g. in-progress, completed")
    From: Optional[str] = Field(default=None, description="Caller phone number")
    To: Optional[str] = Field(default=None, description="Dialled phone number")
    Direction: Optional[str] = Field(default=None, description="inbound or outbound-dial")
    AccountSid: Optional[str] = Field(default=None)

    model_config = {"extra": "allow"}  # Twilio sends many extra fields


class TwilioTranscriptEvent(BaseModel):
    """
    Simulated or live Twilio transcript event payload.
    When Twilio Transcription (Media Streams) is live this will carry real data.
    """
    call_sid: str = Field(..., description="Twilio Call SID")
    speaker: str = Field(..., pattern="^(agent|customer)$")
    text: str = Field(..., min_length=1)
    timestamp: str = Field(..., description="ISO 8601 datetime string")


class TwilioWebhookResponse(BaseModel):
    """Response returned to Twilio after webhook processing."""
    received: bool = True
    message: str = "OK"
