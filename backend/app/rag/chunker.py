"""
Text chunker — splits clean text into meaningful chunks for embedding.
"""
import logging
import uuid
from typing import List, Dict, Any, Optional
from app.rag.cleaner import split_into_paragraphs

logger = logging.getLogger(__name__)


class TextChunker:
    """
    Text chunker with configurable size and overlap.
    
    Default settings:
    - chunk_size: 1000 characters
    - chunk_overlap: 150 characters
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
        min_chunk_size: int = 100,
    ):
        """
        Initialize the chunker.
        
        Args:
            chunk_size: Target size for each chunk in characters.
            chunk_overlap: Number of characters to overlap between chunks.
            min_chunk_size: Minimum chunk size to keep (smaller chunks discarded).
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        
        if chunk_overlap >= chunk_size:
            logger.warning(
                "chunk_overlap (%d) >= chunk_size (%d). "
                "Setting overlap to chunk_size // 3",
                chunk_overlap, chunk_size
            )
            self.chunk_overlap = chunk_size // 3
    
    def chunk_text(
        self,
        text: str,
        source_filename: str,
        doc_type: str = "general",
    ) -> List[Dict[str, Any]]:
        """
        Chunk text into overlapping pieces with metadata.
        
        Args:
            text: Cleaned text to chunk.
            source_filename: Source document filename.
            doc_type: Document type (sales, compliance, general).
            
        Returns:
            List of chunk dictionaries with text and metadata.
        """
        if not text:
            return []
        
        paragraphs = split_into_paragraphs(text)
        
        if not paragraphs:
            paragraphs = [text]
        
        chunks = []
        chunk_id = str(uuid.uuid4())[:8]
        chunk_index = 0
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            if len(current_chunk) + len(para) + 2 <= self.chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
            else:
                if current_chunk:
                    if len(current_chunk) >= self.min_chunk_size:
                        chunks.append({
                            "text": current_chunk,
                            "metadata": {
                                "source_filename": source_filename,
                                "doc_type": doc_type,
                                "chunk_id": f"{chunk_id}_{chunk_index}",
                                "chunk_index": chunk_index,
                            }
                        })
                        chunk_index += 1
                    else:
                        logger.debug("Skipping small chunk: %d chars", len(current_chunk))
                
                current_chunk = para
        
        if current_chunk and len(current_chunk) >= self.min_chunk_size:
            chunks.append({
                "text": current_chunk,
                "metadata": {
                    "source_filename": source_filename,
                    "doc_type": doc_type,
                    "chunk_id": f"{chunk_id}_{chunk_index}",
                    "chunk_index": chunk_index,
                }
            })
            chunk_index += 1
        
        for chunk in chunks:
            chunk["metadata"]["total_chunks"] = chunk_index
        
        logger.info(
            "Chunked %s | paragraphs=%d chunks=%d",
            source_filename, len(paragraphs), len(chunks)
        )
        
        return chunks
    
    def chunk_texts(
        self,
        documents: List[tuple[str, str]],
        doc_type_map: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Chunk multiple documents.
        
        Args:
            documents: List of (filename, text) tuples.
            doc_type_map: Optional mapping of filename -> doc_type.
            
        Returns:
            Flat list of all chunks.
        """
        doc_type_map = doc_type_map or {}
        all_chunks = []
        
        for filename, text in documents:
            doc_type = doc_type_map.get(filename, self._infer_doc_type(filename))
            chunks = self.chunk_text(text, filename, doc_type)
            all_chunks.extend(chunks)
        
        logger.info("Total chunks created: %d", len(all_chunks))
        return all_chunks
    
    @staticmethod
    def _infer_doc_type(filename: str) -> str:
        """Infer doc type from filename."""
        lower = filename.lower()
        if "sales" in lower:
            return "sales"
        elif "compliance" in lower:
            return "compliance"
        return "general"
