"""
Post-call summary service — generates and returns a full call summary.
"""
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.suggestion import PostCallSummaryResponse
from app.services import ai_service
from app.services.transcript_service import chunks_to_dicts, get_chunks_for_session

logger = logging.getLogger(__name__)


async def generate_summary(
    session_id: int,
    db: AsyncSession,
) -> PostCallSummaryResponse:
    """
    Fetch all transcript chunks for a session and generate a post-call summary.
    This is called automatically when a session is ended.
    """
    logger.info("Generating post-call summary | session=%s", session_id)

    # Fetch complete transcript
    chunks = await get_chunks_for_session(session_id, db)
    chunk_dicts = chunks_to_dicts(chunks)

    if not chunk_dicts:
        logger.warning("No transcript chunks found for session=%s", session_id)
        return PostCallSummaryResponse(
            session_id=session_id,
            overall_summary="No transcript available for this session.",
            main_concerns=[],
            objections_raised=[],
            compliance_warnings=[],
            suggested_next_action="Review session manually.",
        )

    return await ai_service.generate_post_call_summary(chunk_dicts, session_id)
