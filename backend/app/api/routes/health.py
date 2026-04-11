"""
Health check route.
"""
from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str
    version: str = "1.0.0"


@router.get("/health", response_model=HealthResponse, summary="API health check")
async def health_check() -> HealthResponse:
    """Returns the current health status of the API."""
    return HealthResponse(
        status="ok",
        app_name=settings.APP_NAME,
        environment=settings.APP_ENV,
    )
