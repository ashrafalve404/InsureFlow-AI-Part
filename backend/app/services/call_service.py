"""
Call session service — CRUD operations for CallSession.
"""
from typing import Any, Optional, Union, List, Dict, Tuple
import logging
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.call_session import CallSession
from app.schemas.call import StartCallRequest
from app.utils.constants import CallStatus
from app.utils.time import utcnow_naive

logger = logging.getLogger(__name__)


async def create_session(data: StartCallRequest, db: AsyncSession) -> CallSession:
    """Create and persist a new call session."""
    now = utcnow_naive()
    session = CallSession(
        call_sid=data.call_sid,
        agent_name=data.agent_name,
        customer_name=data.customer_name,
        customer_phone=data.customer_phone,
        status=CallStatus.ACTIVE,
        started_at=now,
        created_at=now,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    logger.info("CallSession created | id=%s agent=%s", session.id, session.agent_name)
    return session


async def create_session(
    call_sid: str,
    agent_name: str,
    customer_phone: str,
    db: AsyncSession,
    customer_name: str = "Unknown",
) -> CallSession:
    """Create a session from Twilio webhook (minimal info)."""
    now = utcnow_naive()
    session = CallSession(
        call_sid=call_sid,
        agent_name=agent_name,
        customer_name=customer_name,
        customer_phone=customer_phone,
        status=CallStatus.ACTIVE,
        started_at=now,
        created_at=now,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    logger.info("CallSession created from Twilio | id=%s call_sid=%s", session.id, call_sid)
    return session


async def get_session(session_id: int, db: AsyncSession) -> Optional[CallSession]:
    """Fetch a single call session by primary key."""
    result = await db.execute(
        select(CallSession).where(CallSession.id == session_id)
    )
    return result.scalar_one_or_none()


async def list_sessions(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
) -> Tuple[int, List[CallSession]]:
    """Return paginated list of all call sessions, newest first."""
    total_result = await db.execute(select(func.count()).select_from(CallSession))
    total = total_result.scalar_one()

    result = await db.execute(
        select(CallSession)
        .order_by(CallSession.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    sessions = list(result.scalars().all())
    return total, sessions


async def end_session(
    session_id: int,
    db: AsyncSession,
) -> Optional[CallSession]:
    """
    Mark a call session as ended.
    Returns the updated session or None if not found / already ended.
    """
    session = await get_session(session_id, db)
    if session is None:
        return None
    if session.status == CallStatus.ENDED:
        return session  # idempotent

    session.status = CallStatus.ENDED
    session.ended_at = utcnow_naive()
    await db.commit()
    await db.refresh(session)
    logger.info("CallSession ended | id=%s", session.id)
    return session
