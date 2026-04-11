"""
RAG data schemas for type safety and validation.
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    """Metadata associated with a text chunk."""
    source_filename: str
    doc_type: str = "general"
    chunk_id: str
    chunk_index: int
    total_chunks: int


class Chunk(BaseModel):
    """A text chunk with its embedding and metadata."""
    id: str = Field(alias="chunk_id")
    text: str
    metadata: ChunkMetadata
    embedding: Optional[List[float]] = None

    class Config:
        populate_by_name = True


class RetrievedChunk(BaseModel):
    """A chunk returned from the retriever."""
    text: str
    source_filename: str
    doc_type: str
    chunk_index: int
    score: float = 0.0


class IngestResult(BaseModel):
    """Result of an ingestion run."""
    files_processed: int
    total_chunks: int
    indexed: bool
    message: str


class RAGStatus(BaseModel):
    """Status of the RAG system."""
    enabled: bool
    vector_store_exists: bool
    indexed_file_count: int
    total_chunks: int
