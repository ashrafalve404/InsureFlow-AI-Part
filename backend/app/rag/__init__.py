"""
RAG module for knowledge retrieval.

Submodules:
- loader: DOCX file loading
- cleaner: Text cleaning and normalization
- chunker: Text chunking
- embeddings: OpenAI embeddings generation
- vectorstore: FAISS vector storage
- retriever: Runtime retrieval
- ingest: Ingestion script
- schemas: Pydantic schemas
"""
from app.rag.schemas import (
    Chunk,
    ChunkMetadata,
    RetrievedChunk,
    IngestResult,
    RAGStatus,
)
from app.rag.retriever import (
    retrieve,
    retrieve_for_live_suggestion,
    retrieve_for_compliance,
    retrieve_for_objection,
    retrieve_for_summary,
    format_retrieved_context,
    extract_transcript_for_retrieval,
)
from app.rag.vectorstore import (
    get_vector_store,
    load_vector_store,
    initialize_vector_store,
)

__all__ = [
    "Chunk",
    "ChunkMetadata",
    "RetrievedChunk",
    "IngestResult",
    "RAGStatus",
    "retrieve",
    "retrieve_for_live_suggestion",
    "retrieve_for_compliance",
    "retrieve_for_objection",
    "retrieve_for_summary",
    "format_retrieved_context",
    "extract_transcript_for_retrieval",
    "get_vector_store",
    "load_vector_store",
    "initialize_vector_store",
]
