"""
FAISS vector store for local embedding storage and retrieval.
"""
import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS not available. Vector store disabled.")


class FAISSVectorStore:
    """
    Local FAISS vector store with metadata persistence.
    """
    
    def __init__(self, vector_dir: str = "knowledge/vector_store"):
        """
        Initialize the vector store.
        
        Args:
            vector_dir: Directory to store FAISS index and metadata.
        """
        self.vector_dir = Path(vector_dir)
        self.index_path = self.vector_dir / "index.faiss"
        self.metadata_path = self.vector_dir / "metadata.json"
        
        self.index: Optional[faiss.Index] = None
        self.metadata: List[Dict[str, Any]] = []
        
        self._dimension = 0
        self._loaded = False
    
    def exists(self) -> bool:
        """Check if vector store exists on disk."""
        return self.index_path.exists() and self.metadata_path.exists()
    
    def load(self) -> bool:
        """
        Load existing index and metadata from disk.
        
        Returns:
            True if loaded successfully, False otherwise.
        """
        if not self.exists():
            logger.info("Vector store does not exist")
            return False
        
        try:
            self.index = faiss.read_index(str(self.index_path))
            self._dimension = self.index.d
            
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
            
            logger.info(
                "Loaded vector store | dimension=%d chunks=%d",
                self._dimension, len(self.metadata)
            )
            self._loaded = True
            return True
        
        except Exception as exc:
            logger.error("Failed to load vector store: %s", exc)
            return False
    
    def create(self, dimension: int) -> None:
        """
        Create a new FAISS index.
        
        Args:
            dimension: Embedding dimension.
        """
        self._dimension = dimension
        
        self.vector_dir.mkdir(parents=True, exist_ok=True)
        
        self.index = faiss.IndexFlatL2(dimension)
        
        logger.info("Created FAISS index | dimension=%d", dimension)
    
    def add(self, chunks: List[Dict[str, Any]]) -> None:
        """
        Add embedded chunks to the index.
        
        Args:
            chunks: List of chunks with 'embedding' field.
        """
        if not chunks:
            return
        
        if self.index is None:
            first_embedding = chunks[0]["embedding"]
            self.create(len(first_embedding))
        
        embeddings = np.array([chunk["embedding"] for chunk in chunks]).astype("float32")
        
        self.index.add(embeddings)
        
        for chunk in chunks:
            self.metadata.append({
                "chunk_id": chunk["metadata"]["chunk_id"],
                "text": chunk["text"],
                "source_filename": chunk["metadata"]["source_filename"],
                "doc_type": chunk["metadata"]["doc_type"],
                "chunk_index": chunk["metadata"]["chunk_index"],
                "total_chunks": chunk["metadata"]["total_chunks"],
            })
        
        logger.info("Added %d chunks to index", len(chunks))
    
    def save(self) -> None:
        """Persist index and metadata to disk."""
        if self.index is None:
            logger.warning("No index to save")
            return
        
        self.vector_dir.mkdir(parents=True, exist_ok=True)
        
        faiss.write_index(self.index, str(self.index_path))
        
        with open(self.metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        
        logger.info("Saved vector store | chunks=%d", len(self.metadata))
    
    def search(
        self,
        query_embedding: List[float],
        k: int = 4,
        doc_type_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks.
        
        Args:
            query_embedding: Query embedding vector.
            k: Number of results to return.
            doc_type_filter: Optional filter by doc_type.
            
        Returns:
            List of retrieved chunks with scores.
        """
        if self.index is None or not self.metadata:
            logger.warning("No index available for search")
            return []
        
        query_vector = np.array([query_embedding]).astype("float32")
        
        search_k = k * 3 if doc_type_filter else k
        
        distances, indices = self.index.search(query_vector, min(search_k, len(self.metadata)))
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            
            chunk = self.metadata[idx]
            
            if doc_type_filter and chunk.get("doc_type") != doc_type_filter:
                continue
            
            results.append({
                "text": chunk["text"],
                "source_filename": chunk["source_filename"],
                "doc_type": chunk["doc_type"],
                "chunk_index": chunk["chunk_index"],
                "score": float(dist),
            })
            
            if len(results) >= k:
                break
        
        logger.debug(
            "Search completed | k=%d doc_type=%s results=%d",
            k, doc_type_filter, len(results)
        )
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        return {
            "indexed_file_count": len(set(m.get("source_filename") for m in self.metadata)),
            "total_chunks": len(self.metadata),
            "dimension": self._dimension,
        }
    
    def clear(self) -> None:
        """Clear the index and metadata."""
        self.index = None
        self.metadata = []
        self._loaded = False
        self._dimension = 0
        
        if self.exists():
            self.index_path.unlink()
            self.metadata_path.unlink()
        
        logger.info("Cleared vector store")


_vector_store: Optional[FAISSVectorStore] = None


def get_vector_store() -> FAISSVectorStore:
    """Get or create the global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = FAISSVectorStore(settings.RAG_VECTOR_DIR)
    return _vector_store


def load_vector_store() -> bool:
    """Load the vector store if it exists."""
    store = get_vector_store()
    return store.load()


def initialize_vector_store(force: bool = False) -> FAISSVectorStore:
    """
    Initialize the vector store, loading existing or creating new.
    
    Args:
        force: If True, create new even if existing.
        
    Returns:
        The vector store instance.
    """
    store = get_vector_store()
    
    if force:
        store.clear()
        store.load()
    else:
        if not store.load():
            logger.info("No existing vector store found. Run ingest to create one.")
    
    return store
