"""
Compliance monitoring service.
Combines fast rule-based phrase matching with AI-assisted risk detection.
"""
from typing import Any, Optional, Union, List, Dict, Tuple
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compliance_flag import ComplianceFlag
from app.services import ai_service
from app.utils.constants import COMPLIANCE_RISK_PHRASES
from app.utils.time import utcnow_naive

logger = logging.getLogger(__name__)


def rule_based_check(text: str) -> Tuple[bool, Optional[str]]:
    """
    Scan text for hard-coded high-risk compliance phrases.

    Returns:
        (has_risk: bool, matched_phrase: Optional[str])
    """
    lower = text.lower()
    for phrase in COMPLIANCE_RISK_PHRASES:
        if phrase in lower:
            logger.debug("Compliance rule match: phrase='%s'", phrase)
            return True, phrase
    return False, None


async def check_and_store_compliance(
    session_id: int,
    chunk_id: int,
    speaker: str,
    text: str,
    db: AsyncSession,
) -> Optional[str]:
    """
    Check a transcript utterance for compliance risks and persist flags.

    Strategy:
    1. Only agent utterances are checked (agents make the promises).
    2. Rule-based check runs first.
    3. AI check runs regardless to catch nuanced risks.
    4. The most severe finding is stored as a ComplianceFlag.

    Returns the warning message string (or None if no risk).
    """
    if speaker != "agent":
        return None

    warning_message: Optional[str] = None
    trigger_phrase: Optional[str] = None
    method = "rule_based"

    # ── Step 1: Rule-based ──────────────────────────────────────────────────
    has_rule_risk, matched_phrase = rule_based_check(text)
    if has_rule_risk and matched_phrase:
        trigger_phrase = matched_phrase
        warning_message = (
            f"Avoid using the phrase '{matched_phrase}' — it may imply a guarantee."
        )

    # ── Step 2: AI check ────────────────────────────────────────────────────
    try:
        ai_result = await ai_service.detect_compliance_risk(text)
        if ai_result.get("has_risk") and ai_result.get("warning"):
            method = "ai_assisted"
            if not warning_message:
                # AI found a risk that rule-based missed
                warning_message = ai_result["warning"]
                trigger_phrase = ai_result.get("trigger_phrase")
            # If rule already flagged, AI provides extra detail but we keep rule's message
    except Exception as exc:
        logger.warning("AI compliance check skipped: %s", exc)

    # ── Step 3: Persist ─────────────────────────────────────────────────────
    if warning_message:
        flag = ComplianceFlag(
            session_id=session_id,
            chunk_id=chunk_id,
            detection_method=method,
            trigger_phrase=trigger_phrase,
            warning_message=warning_message,
            severity="high" if has_rule_risk else "medium",
            created_at=utcnow_naive(),
        )
        db.add(flag)
        await db.commit()
        logger.info(
            "ComplianceFlag stored | session=%s severity=%s method=%s",
            session_id,
            flag.severity,
            method,
        )

    return warning_message
