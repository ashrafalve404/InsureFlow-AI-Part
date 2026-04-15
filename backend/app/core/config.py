"""
Pydantic-based application configuration.
All settings are loaded from environment variables / .env file.
"""
from typing import Any, Optional, Union, List, Dict, Tuple
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── General ───────────────────────────────────────────────────────────────
    APP_NAME: str = "InsureFlow AI Sales Assistant"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production"

    # ── OpenAI ────────────────────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # ── Twilio ────────────────────────────────────────────────────────────────
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./insureflow.db"

    # ── AI behaviour ──────────────────────────────────────────────────────────
    AI_MAX_CONTEXT_CHUNKS: int = 10
    AI_TEMPERATURE: float = 0.3

    # ── RAG Configuration ──────────────────────────────────────────────────────
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    RAG_ENABLED: bool = True
    RAG_TOP_K: int = 4
    RAG_CHUNK_SIZE: int = 1000
    RAG_CHUNK_OVERLAP: int = 150
    RAG_VECTOR_DIR: str = "knowledge/vector_store"
    RAG_RAW_DOCS_DIR: str = "knowledge/raw"

    # ── CRM Configuration ────────────────────────────────────────────────────────────────
    CRM_ENABLED: bool = True
    CRM_PROVIDER: str = "gohighlevel"
    GHL_API_BASE_URL: str = "https://services.leadconnectorhq.com"
    GHL_PRIVATE_INTEGRATION_TOKEN: str = ""
    GHL_LOCATION_ID: str = ""
    GHL_API_VERSION: str = "2021-07-28"

    # ── Deepgram Configuration ───────────────────────────────────────────────────────
    DEEPGRAM_API_KEY: str = ""
    MEDIA_STREAM_URL: str = ""
    SALES_PERSON_NUMBER: str = ""


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance (singleton)."""
    return Settings()


# Convenience singleton used throughout the app
settings = get_settings()
