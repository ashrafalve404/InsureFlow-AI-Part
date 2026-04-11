"""
RAG API routes for ingestion and status.
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.rag.ingest import run_ingest
from app.rag.schemas import IngestResult, RAGStatus
from app.rag.vectorstore import get_vector_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["rag"])


class IngestResponse(BaseModel):
    success: bool
    message: str
    files_processed: int
    total_chunks: int


class StatusResponse(BaseModel):
    enabled: bool
    vector_store_exists: bool
    indexed_file_count: int
    total_chunks: int


@router.post("/ingest", response_model=IngestResponse)
async def trigger_ingest():
    """
    Manually trigger the RAG ingestion process.
    
    Loads DOCX files from knowledge/raw/, processes them,
    and builds the FAISS vector index.
    """
    if not settings.RAG_ENABLED:
        raise HTTPException(status_code=400, detail="RAG is disabled in settings")
    
    try:
        result = await run_ingest()
        return IngestResponse(
            success=result.indexed,
            message=result.message,
            files_processed=result.files_processed,
            total_chunks=result.total_chunks,
        )
    except Exception as exc:
        logger.error("Ingest failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Ingest failed: {str(exc)}")


@router.get("/status", response_model=StatusResponse)
async def get_rag_status():
    """
    Get the current status of the RAG system.
    
    Returns whether the vector store exists and statistics about indexed content.
    """
    store = get_vector_store()
    store_exists = store.exists()
    indexed_file_count = 0
    total_chunks = 0
    
    if store_exists:
        stats = store.get_stats()
        indexed_file_count = stats.get("indexed_file_count", 0)
        total_chunks = stats.get("total_chunks", 0)
    
    return StatusResponse(
        enabled=settings.RAG_ENABLED,
        vector_store_exists=store_exists,
        indexed_file_count=indexed_file_count,
        total_chunks=total_chunks,
    )
