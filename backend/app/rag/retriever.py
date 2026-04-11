"""
Retriever — retrieves relevant chunks from the vector store at runtime.
"""
import logging
from typing import List, Optional, Dict, Any
from app.core.config import settings
from app.rag import embeddings
from app.rag.vectorstore import get_vector_store, load_vector_store

logger = logging.getLogger(__name__)

_vector_store_initialized = False


def _ensure_vector_store() -> bool:
    """Ensure vector store is loaded."""
    global _vector_store_initialized
    if not _vector_store_initialized:
        _vector_store_initialized = load_vector_store()
    return _vector_store_initialized


async def retrieve(
    query_text: str,
    top_k: Optional[int] = None,
    doc_type_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve relevant chunks from the vector store.
    
    Args:
        query_text: Text to search for (e.g., recent transcript context).
        top_k: Number of chunks to retrieve. Defaults to RAG_TOP_K.
        doc_type_filter: Optional filter by doc_type (sales, compliance, general).
        
    Returns:
        List of retrieved chunks with text and metadata.
    """
    if not settings.RAG_ENABLED:
        logger.debug("RAG is disabled")
        return []
    
    if not _ensure_vector_store():
        logger.warning("Vector store not available")
        return []
    
    k = top_k or settings.RAG_TOP_K
    
    try:
        query_embedding = await embeddings.generate_embedding(query_text)
    except Exception as exc:
        logger.error("Failed to generate query embedding: %s", exc)
        return []
    
    store = get_vector_store()
    results = store.search(
        query_embedding=query_embedding,
        k=k,
        doc_type_filter=doc_type_filter,
    )
    
    logger.info(
        "Retrieved chunks | query_len=%d top_k=%s doc_type=%s found=%d",
        len(query_text), k, doc_type_filter, len(results)
    )
    
    return results


def format_retrieved_context(
    chunks: List[Dict[str, Any]],
    max_chars: Optional[int] = 2000,
) -> str:
    """
    Format retrieved chunks into a context string for prompts.
    
    Args:
        chunks: List of retrieved chunks.
        max_chars: Maximum total characters (None for unlimited).
        
    Returns:
        Formatted context string.
    """
    if not chunks:
        return "No relevant knowledge context available."
    
    context_parts = []
    total_chars = 0
    
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("source_filename", "unknown")
        doc_type = chunk.get("doc_type", "general")
        text = chunk.get("text", "")
        
        header = f"[Source: {source} ({doc_type})]"
        
        if max_chars and total_chars + len(header) + len(text) > max_chars:
            remaining = max_chars - total_chars - len(header) - 20
            if remaining > 50:
                text = text[:remaining] + "..."
                context_parts.append(f"{header}\n{text}")
            break
        
        context_parts.append(f"{header}\n{text}")
        total_chars += len(header) + len(text)
    
    header = "=== KNOWLEDGE CONTEXT ===\n"
    footer = f"\n=== END CONTEXT ({len(chunks)} chunks) ==="
    
    return header + "\n\n".join(context_parts) + footer


def extract_transcript_for_retrieval(
    transcript_chunks: List[Dict[str, Any]],
    last_n: Optional[int] = 5,
) -> str:
    """
    Extract recent transcript text for retrieval query.
    
    Args:
        transcript_chunks: List of transcript chunk dicts.
        last_n: Number of most recent chunks to include. None = all chunks.
        
    Returns:
        Concatenated transcript text.
    """
    if not transcript_chunks:
        return ""
    
    recent = transcript_chunks[-last_n:] if last_n else transcript_chunks
    
    texts = []
    for chunk in recent:
        speaker = chunk.get("speaker", "unknown")
        text = chunk.get("text", "")
        if text:
            texts.append(f"{speaker}: {text}")
    
    return " | ".join(texts)


async def retrieve_for_live_suggestion(
    transcript_chunks: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Retrieve chunks for live response suggestion.
    Prefers sales and general doc types.
    
    Args:
        transcript_chunks: Recent transcript chunks.
        
    Returns:
        Retrieved chunks.
    """
    query = extract_transcript_for_retrieval(transcript_chunks)
    
    if not query:
        return []
    
    return await retrieve(
        query_text=query,
        doc_type_filter=None,
    )


async def retrieve_for_compliance(
    transcript_chunks: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Retrieve chunks for compliance monitoring.
    Prefers compliance doc type.
    
    Args:
        transcript_chunks: Recent transcript chunks.
        
    Returns:
        Retrieved chunks.
    """
    query = extract_transcript_for_retrieval(transcript_chunks)
    
    if not query:
        return []
    
    return await retrieve(
        query_text=query,
        doc_type_filter="compliance",
    )


async def retrieve_for_objection(
    transcript_chunks: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Retrieve chunks for objection handling.
    Prefers sales doc type.
    
    Args:
        transcript_chunks: Recent transcript chunks.
        
    Returns:
        Retrieved chunks.
    """
    query = extract_transcript_for_retrieval(transcript_chunks)
    
    if not query:
        return []
    
    return await retrieve(
        query_text=query,
        doc_type_filter="sales",
    )


async def retrieve_for_summary(
    transcript_chunks: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Retrieve chunks for post-call summary.
    Can include all doc types.
    
    Args:
        transcript_chunks: Full transcript chunks.
        
    Returns:
        Retrieved chunks.
    """
    query = extract_transcript_for_retrieval(transcript_chunks, last_n=0)
    
    if not query:
        return []
    
    return await retrieve(
        query_text=query,
        doc_type_filter=None,
    )
