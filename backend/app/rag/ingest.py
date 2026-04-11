"""
RAG ingestion script — loads, processes, and indexes DOCX files.

Run with:
    python -m app.rag.ingest
"""
import asyncio
import logging
from pathlib import Path
import sys

from app.core.config import settings
from app.rag.loader import load_all_docx, infer_doc_type
from app.rag.cleaner import clean_text
from app.rag.chunker import TextChunker
from app.rag.embeddings import embed_chunks
from app.rag.vectorstore import FAISSVectorStore, get_vector_store
from app.rag.schemas import IngestResult

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def run_ingest() -> IngestResult:
    """
    Main ingestion pipeline.
    
    Steps:
    1. Load DOCX files from knowledge/raw/
    2. Clean and normalize text
    3. Chunk text
    4. Generate embeddings
    5. Build FAISS index
    6. Persist to disk
    """
    raw_dir = Path(settings.RAG_RAW_DOCS_DIR)
    vector_dir = Path(settings.RAG_VECTOR_DIR)
    
    logger.info("=" * 50)
    logger.info("Starting RAG ingestion")
    logger.info("Raw docs dir: %s", raw_dir)
    logger.info("Vector store dir: %s", vector_dir)
    logger.info("=" * 50)
    
    if not raw_dir.exists():
        logger.error("Raw docs directory does not exist: %s", raw_dir)
        return IngestResult(
            files_processed=0,
            total_chunks=0,
            indexed=False,
            message=f"Directory not found: {raw_dir}",
        )
    
    logger.info("Loading DOCX files...")
    documents = load_all_docx(raw_dir)
    
    if not documents:
        logger.warning("No DOCX files found in %s", raw_dir)
        return IngestResult(
            files_processed=0,
            total_chunks=0,
            indexed=False,
            message="No DOCX files found. Place .docx files in knowledge/raw/",
        )
    
    logger.info("Found %d documents", len(documents))
    
    logger.info("Cleaning text...")
    cleaned_docs = []
    for filename, text in documents:
        cleaned = clean_text(text)
        cleaned_docs.append((filename, cleaned))
        logger.debug("Cleaned: %s | chars: %d", filename, len(cleaned))
    
    logger.info("Chunking text...")
    chunker = TextChunker(
        chunk_size=settings.RAG_CHUNK_SIZE,
        chunk_overlap=settings.RAG_CHUNK_OVERLAP,
    )
    
    doc_type_map = {
        "Sales Knowledge.docx": "sales",
        "The Chat Workflow.docx": "general",
    }
    
    all_chunks = chunker.chunk_texts(cleaned_docs, doc_type_map=doc_type_map)
    total_chunks = len(all_chunks)
    
    if total_chunks == 0:
        logger.error("No chunks created from documents")
        return IngestResult(
            files_processed=len(documents),
            total_chunks=0,
            indexed=False,
            message="Failed to create chunks from documents",
        )
    
    logger.info("Generated %d chunks", total_chunks)
    
    logger.info("Generating embeddings...")
    try:
        embedded_chunks = await embed_chunks(all_chunks)
    except Exception as exc:
        logger.error("Embedding generation failed: %s", exc)
        return IngestResult(
            files_processed=len(documents),
            total_chunks=total_chunks,
            indexed=False,
            message=f"Embedding failed: {exc}",
        )
    
    logger.info("Building FAISS index...")
    store = get_vector_store()
    store.clear()
    store.add(embedded_chunks)
    store.save()
    
    logger.info("=" * 50)
    logger.info("Ingestion complete!")
    logger.info("Files processed: %d", len(documents))
    logger.info("Total chunks: %d", total_chunks)
    logger.info("Vector store saved to: %s", vector_dir)
    logger.info("=" * 50)
    
    return IngestResult(
        files_processed=len(documents),
        total_chunks=total_chunks,
        indexed=True,
        message=f"Successfully indexed {len(documents)} documents with {total_chunks} chunks",
    )


def main():
    """Entry point for the ingest script."""
    result = asyncio.run(run_ingest())
    
    if result.indexed:
        print(f"\nSUCCESS: {result.message}")
        sys.exit(0)
    else:
        print(f"\nFAILED: {result.message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
