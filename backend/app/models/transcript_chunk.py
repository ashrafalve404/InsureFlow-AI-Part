"""
TranscriptChunk ORM model — a single utterance captured during a call.
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TranscriptChunk(Base):
    __tablename__ = "transcript_chunks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("call_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # "agent" or "customer"
    speaker: Mapped[str] = mapped_column(String(16), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    # Client-provided timestamp for the utterance
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Server-side ingestion time
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    session: Mapped["CallSession"] = relationship(  # noqa: F821
        "CallSession", back_populates="transcript_chunks"
    )

    def __repr__(self) -> str:
        return f"<TranscriptChunk id={self.id} session={self.session_id} speaker={self.speaker}>"
