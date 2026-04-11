"""
Transcript service — ingestion and retrieval of TranscriptChunk records.
"""
from typing import Any, Optional, Union, List, Dict, Tuple
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transcript_chunk import TranscriptChunk
from app.utils.time import utcnow_naive

logger = logging.getLogger(__name__)


async def store_chunk(
    session_id: int,
    speaker: str,
    text: str,
    timestamp: datetime,
    db: AsyncSession,
) -> TranscriptChunk:
    """Persist a single transcript utterance."""
    chunk = TranscriptChunk(
        session_id=session_id,
        speaker=speaker,
        text=text,
        timestamp=timestamp,
        created_at=utcnow_naive(),
    )
    db.add(chunk)
    await db.commit()
    await db.refresh(chunk)
    logger.debug(
        "TranscriptChunk stored | id=%s session=%s speaker=%s",
        chunk.id,
        session_id,
        speaker,
    )
    return chunk


async def get_chunks_for_session(
    session_id: int,
    db: AsyncSession,
    limit: Optional[int] = None,
) -> List[TranscriptChunk]:
    """
    Return transcript chunks for a session ordered by timestamp ascending.
    If `limit` is provided, return only the most recent N chunks.
    """
    query = (
        select(TranscriptChunk)
        .where(TranscriptChunk.session_id == session_id)
        .order_by(TranscriptChunk.timestamp.asc())
    )
    result = await db.execute(query)
    all_chunks = list(result.scalars().all())

    if limit is not None and limit > 0:
        return all_chunks[-limit:]
    return all_chunks


def chunks_to_dicts(chunks: List[TranscriptChunk]) -> List[dict]:
    """Convert ORM chunks to plain dicts for AI service consumption."""
    return [
        {
            "speaker": c.speaker,
            "text": c.text,
            "timestamp": c.timestamp.isoformat(),
        }
        for c in chunks
    ]
