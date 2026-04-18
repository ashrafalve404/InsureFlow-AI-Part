"""
Models package — import all models here so SQLAlchemy metadata is populated
before create_tables() is called.
"""
from app.models.ai_suggestion import AISuggestion
from app.models.call_session import CallSession
from app.models.compliance_flag import ComplianceFlag
from app.models.objection_event import ObjectionEvent
from app.models.transcript_chunk import TranscriptChunk
from app.models.system_setting import SystemSetting

__all__ = [
    "CallSession",
    "TranscriptChunk",
    "AISuggestion",
    "ComplianceFlag",
    "ObjectionEvent",
    "SystemSetting",
]
