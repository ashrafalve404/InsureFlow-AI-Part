"""
Rule-based + AI-assisted objection detection service.
Rule-based runs first (fast, free). AI is used for ambiguous cases.
"""
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.objection_event import ObjectionEvent
from app.services import ai_service
from app.utils.constants import OBJECTION_KEYWORDS, ObjectionLabel
from app.utils.time import utcnow_naive

logger = logging.getLogger(__name__)


def rule_based_detect(text: str) -> str:
    """
    Scan text for known objection keyword patterns.
    Returns an ObjectionLabel constant or ObjectionLabel.NONE.
    """
    lower = text.lower()
    for label, keywords in OBJECTION_KEYWORDS.items():
        for kw in keywords:
            if kw in lower:
                logger.debug("Rule-based objection match: label=%s kw='%s'", label, kw)
                return label
    return ObjectionLabel.NONE


async def detect_and_store_objection(
    session_id: int,
    chunk_id: int,
    speaker: str,
    text: str,
    db: AsyncSession,
) -> str:
    """
    Detect an objection from a transcript utterance and persist an ObjectionEvent.

    Strategy:
    1. Only customer utterances are checked (agents don't raise objections).
    2. Rule-based detection runs first.
    3. If rule-based returns NONE, AI is consulted.
    4. If an objection is found (by either method), it is stored in DB.

    Returns the final objection label.
    """
    if speaker != "customer":
        return ObjectionLabel.NONE

    # ── Step 1: Rule-based ──────────────────────────────────────────────────
    label = rule_based_detect(text)
    method = "rule_based"

    # ── Step 2: AI fallback ─────────────────────────────────────────────────
    if label == ObjectionLabel.NONE:
        try:
            ai_result = await ai_service.detect_objection(text)
            ai_label = ai_result.get("objection_label", ObjectionLabel.NONE)
            confidence = ai_result.get("confidence", 0.0)
            if ai_label != ObjectionLabel.NONE and confidence >= 0.6:
                label = ai_label
                method = "ai_assisted"
        except Exception as exc:
            logger.warning("AI objection detection skipped: %s", exc)

    # ── Step 3: Persist if objection found ──────────────────────────────────
    if label != ObjectionLabel.NONE:
        event = ObjectionEvent(
            session_id=session_id,
            chunk_id=chunk_id,
            objection_label=label,
            detection_method=method,
            source_text=text[:512],  # truncate to fit DB column
            created_at=utcnow_naive(),
        )
        db.add(event)
        await db.commit()
        logger.info(
            "ObjectionEvent stored | session=%s label=%s method=%s",
            session_id,
            label,
            method,
        )

    return label
