"""
ObjectionEvent ORM model — records a detected customer objection during a call.
"""
from typing import Any, Optional, Union, List, Dict, Tuple
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ObjectionEvent(Base):
    __tablename__ = "objection_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("call_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("transcript_chunks.id", ondelete="SET NULL"), nullable=True
    )

    # e.g., "price", "not_interested", "needs_time", etc.
    objection_label: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # "rule_based" or "ai_assisted"
    detection_method: Mapped[str] = mapped_column(String(32), nullable=False)

    # The customer text that triggered this event
    source_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    session: Mapped["CallSession"] = relationship(  # noqa: F821
        "CallSession", back_populates="objection_events"
    )

    def __repr__(self) -> str:
        return (
            f"<ObjectionEvent id={self.id} session={self.session_id} "
            f"label={self.objection_label}>"
        )
