"""
CallSession ORM model — represents one phone-call conversation session.
"""
from typing import Any, Optional, Union, List, Dict, Tuple
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.utils.constants import CallStatus


class CallSession(Base):
    __tablename__ = "call_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Optional Twilio call SID — populated when Twilio integration is live
    call_sid: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True)

    agent_name: Mapped[str] = mapped_column(String(128), nullable=False)
    customer_name: Mapped[str] = mapped_column(String(128), nullable=False)
    customer_phone: Mapped[str] = mapped_column(String(32), nullable=False)

    status: Mapped[str] = mapped_column(
        String(16), default=CallStatus.ACTIVE, nullable=False, index=True
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    transcript_chunks: Mapped[List["TranscriptChunk"]] = relationship(  # noqa: F821
        "TranscriptChunk", back_populates="session", cascade="all, delete-orphan"
    )
    ai_suggestions: Mapped[List["AISuggestion"]] = relationship(  # noqa: F821
        "AISuggestion", back_populates="session", cascade="all, delete-orphan"
    )
    compliance_flags: Mapped[List["ComplianceFlag"]] = relationship(  # noqa: F821
        "ComplianceFlag", back_populates="session", cascade="all, delete-orphan"
    )
    objection_events: Mapped[List["ObjectionEvent"]] = relationship(  # noqa: F821
        "ObjectionEvent", back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<CallSession id={self.id} agent={self.agent_name} status={self.status}>"
