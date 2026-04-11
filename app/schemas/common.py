"""
Common Pydantic schemas reused across the API.
"""
from datetime import datetime

from pydantic import BaseModel


class TimestampMixin(BaseModel):
    """Adds created_at to response schemas."""
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str


class ErrorResponse(BaseModel):
    """Standard error response body."""
    detail: str
