"""
Pydantic schemas for AI Suggestion and post-call Summary endpoints.
"""
from typing import Any, Optional, Union, List, Dict, Tuple
from datetime import datetime

from pydantic import BaseModel


# ── Suggestion schemas ─────────────────────────────────────────────────────────

class AISuggestionResponse(BaseModel):
    """A single AI suggestion record."""
    id: int
    session_id: int
    chunk_id: Optional[int]
    suggested_response: str
    objection_label: str
    compliance_warning: Optional[str]
    call_stage: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SuggestionListResponse(BaseModel):
    """All AI suggestions for a session."""
    session_id: int
    total: int
    suggestions: List[AISuggestionResponse]


# ── Live AI output (broadcast payload) ────────────────────────────────────────

class LiveAIOutput(BaseModel):
    """
    Structured output from a single AI analysis run.
    This is what gets stored to the DB and broadcast over WebSocket.
    """
    suggested_response: str
    objection_label: str = "none"
    compliance_warning: Optional[str] = None
    call_stage: str = "unknown"


# ── Post-call summary ─────────────────────────────────────────────────────────

class PostCallSummaryResponse(BaseModel):
    """Summary generated when a call session is ended."""
    session_id: int
    overall_summary: str
    main_concerns: List[str]
    objections_raised: List[str]
    compliance_warnings: List[str]
    suggested_next_action: str
