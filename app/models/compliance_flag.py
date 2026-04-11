"""
ComplianceFlag ORM model — records a single compliance/risk detection event.
"""
from typing import Any, Optional, Union, List, Dict, Tuple
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ComplianceFlag(Base):
    __tablename__ = "compliance_flags"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("call_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("transcript_chunks.id", ondelete="SET NULL"), nullable=True
    )

    # "rule_based" or "ai_assisted"
    detection_method: Mapped[str] = mapped_column(String(32), nullable=False)

    # The matched phrase or AI reason
    trigger_phrase: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    # Human-readable warning description
    warning_message: Mapped[str] = mapped_column(Text, nullable=False)

    # Severity: low | medium | high
    severity: Mapped[str] = mapped_column(String(16), default="medium", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    session: Mapped["CallSession"] = relationship(  # noqa: F821
        "CallSession", back_populates="compliance_flags"
    )

    def __repr__(self) -> str:
        return (
            f"<ComplianceFlag id={self.id} session={self.session_id} "
            f"severity={self.severity} method={self.detection_method}>"
        )
