"""
Basic API tests to verify core endpoints.
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.core.database import create_tables

pytestmark = pytest.mark.asyncio

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    await create_tables()
    yield


async def test_health_check() -> None:
    """Test the /health endpoint."""
    from httpx import ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "app_name": "InsureFlow AI Sales Assistant",
        "environment": "development",
        "version": "1.0.0",
    }


async def test_create_session() -> None:
    """Test creating a call session."""
    from httpx import ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/calls/start",
            json={
                "agent_name": "Agent Smith",
                "customer_name": "Neo",
                "customer_phone": "+15551234567"
            },
        )
    assert response.status_code == 201
    data = response.json()
    assert data["agent_name"] == "Agent Smith"
    assert data["status"] == "active"
    assert "id" in data


async def test_ingest_transcript_missing_session() -> None:
    """Test ingesting a transcript chunk for a missing session."""
    from httpx import ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/transcripts",
            json={
                "session_id": 99999,
                "speaker": "agent",
                "text": "Hello?",
                "timestamp": "2024-01-01T12:00:00Z"
            },
        )
    assert response.status_code == 404
