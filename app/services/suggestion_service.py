"""
AI Suggestion service — stores AI analysis results and retrieves them.
"""
from typing import Any, Optional, Union, List, Dict, Tuple
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_suggestion import AISuggestion
from app.schemas.suggestion import LiveAIOutput
from app.utils.time import utcnow_naive

logger = logging.getLogger(__name__)


async def store_suggestion(
    session_id: int,
    chunk_id: int,
    output: LiveAIOutput,
    db: AsyncSession,
) -> AISuggestion:
    """Persist an AI suggestion record generated from a transcript chunk."""
    suggestion = AISuggestion(
        session_id=session_id,
        chunk_id=chunk_id,
        suggested_response=output.suggested_response,
        objection_label=output.objection_label,
        compliance_warning=output.compliance_warning,
        call_stage=output.call_stage,
        created_at=utcnow_naive(),
    )
    db.add(suggestion)
    await db.commit()
    await db.refresh(suggestion)
    logger.debug(
        "AISuggestion stored | id=%s session=%s stage=%s",
        suggestion.id,
        session_id,
        output.call_stage,
    )
    return suggestion


async def get_suggestions_for_session(
    session_id: int, db: AsyncSession
) -> List[AISuggestion]:
    """Return all AI suggestions for a session, newest first."""
    result = await db.execute(
        select(AISuggestion)
        .where(AISuggestion.session_id == session_id)
        .order_by(AISuggestion.created_at.desc())
    )
    return list(result.scalars().all())
