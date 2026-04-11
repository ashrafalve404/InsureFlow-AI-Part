"""
AISuggestion ORM model — stores the AI-generated response for a transcript chunk.
"""
from typing import Any, Optional, Union, List, Dict, Tuple
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AISuggestion(Base):
    __tablename__ = "ai_suggestions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("call_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # The transcript chunk that triggered this suggestion (optional reference)
    chunk_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("transcript_chunks.id", ondelete="SET NULL"), nullable=True
    )

    # Short AI-generated reply suggestion for the agent
    suggested_response: Mapped[str] = mapped_column(Text, nullable=False)

    # Objection label: price, not_interested, needs_time, etc. / "none"
    objection_label: Mapped[str] = mapped_column(String(64), default="none", nullable=False)

    # Free-text compliance warning, null if no risk detected
    compliance_warning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Call stage inferred at the time of this suggestion
    call_stage: Mapped[str] = mapped_column(String(32), default="unknown", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    session: Mapped["CallSession"] = relationship(  # noqa: F821
        "CallSession", back_populates="ai_suggestions"
    )

    def __repr__(self) -> str:
        return (
            f"<AISuggestion id={self.id} session={self.session_id} "
            f"stage={self.call_stage} objection={self.objection_label}>"
        )
