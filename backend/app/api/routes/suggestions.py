"""
AI Suggestions retrieval endpoint.

GET /api/calls/{session_id}/suggestions — list stored AI suggestions for a session
"""
from typing import Any, Optional, Union, List, Dict, Tuple
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.suggestion import AISuggestionResponse, SuggestionListResponse
from app.services import call_service
from app.services.suggestion_service import get_suggestions_for_session

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Suggestions"])


@router.get(
    "/calls/{session_id}/suggestions",
    response_model=SuggestionListResponse,
    summary="Get all AI suggestions for a session",
    description="Returns all stored AI suggestions for the given call session, newest first.",
)
async def get_suggestions(
    session_id: int,
    db: AsyncSession = Depends(get_db),
) -> SuggestionListResponse:
    """List AI suggestions for a call session."""
    session = await call_service.get_session(session_id, db)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call session {session_id} not found.",
        )

    suggestions = await get_suggestions_for_session(session_id, db)
    return SuggestionListResponse(
        session_id=session_id,
        total=len(suggestions),
        suggestions=[AISuggestionResponse.model_validate(s) for s in suggestions],
    )
