"""
Embeddings generator using OpenAI API.
"""
import logging
from typing import List, Optional, Dict, Any
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

_client: Optional[AsyncOpenAI] = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


async def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding for a single text using OpenAI embeddings API.
    
    Args:
        text: Text to embed.
        
    Returns:
        Embedding vector as list of floats.
    """
    client = _get_client()
    
    try:
        response = await client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=text,
        )
        embedding = response.data[0].embedding
        logger.debug("Generated embedding | length=%d", len(embedding))
        return embedding
    
    except Exception as exc:
        logger.error("Embedding generation failed: %s", exc)
        raise


async def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple texts in batch.
    
    Args:
        texts: List of texts to embed.
        
    Returns:
        List of embedding vectors.
    """
    if not texts:
        return []
    
    client = _get_client()
    
    try:
        response = await client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=texts,
        )
        
        embeddings = [item.embedding for item in response.data]
        logger.debug("Generated embeddings | count=%d", len(embeddings))
        return embeddings
    
    except Exception as exc:
        logger.error("Batch embedding generation failed: %s", exc)
        raise


async def embed_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Add embeddings to a list of chunks.
    
    Args:
        chunks: List of chunk dictionaries with 'text' and 'metadata'.
        
    Returns:
        List of chunks with 'embedding' field added.
    """
    if not chunks:
        return []
    
    texts = [chunk["text"] for chunk in chunks]
    
    embeddings = await generate_embeddings(texts)
    
    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding
    
    logger.info("Embedded %d chunks", len(chunks))
    return chunks
