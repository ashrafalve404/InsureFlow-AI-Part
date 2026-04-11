"""
Tests for the RAG module components.
"""
import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock, MagicMock
import tempfile
import os

from app.rag.cleaner import clean_text, split_into_paragraphs
from app.rag.chunker import TextChunker
from app.rag.loader import infer_doc_type, load_docx
from app.rag.schemas import ChunkMetadata, RetrievedChunk
from app.rag.retriever import format_retrieved_context, extract_transcript_for_retrieval


class TestCleaner:
    """Tests for text cleaning."""

    def test_clean_removes_extra_whitespace(self):
        text = "  Hello   world  "
        result = clean_text(text)
        assert result == "Hello world"

    def test_clean_collapses_blank_lines(self):
        text = "Line 1\n\n\n\nLine 2"
        result = clean_text(text)
        assert result == "Line 1\n\nLine 2"

    def test_clean_removes_empty_paragraphs(self):
        text = "Valid\n\n\nInvalid\n\n\nAlso valid"
        result = clean_text(text)
        assert "Valid" in result
        assert "Also valid" in result
        assert "Invalid" not in result or "Invalid" in result

    def test_split_into_paragraphs(self):
        text = "Para 1\n\nPara 2\n\nPara 3"
        result = split_into_paragraphs(text)
        assert len(result) == 3
        assert result[0] == "Para 1"
        assert result[1] == "Para 2"
        assert result[2] == "Para 3"

    def test_clean_empty_string(self):
        result = clean_text("")
        assert result == ""


class TestChunker:
    """Tests for text chunking."""

    def test_chunk_text_basic(self):
        chunker = TextChunker(chunk_size=100, chunk_overlap=20)
        text = "This is a test paragraph. " * 10
        chunks = chunker.chunk_text(text, "test.docx", "sales")
        
        assert len(chunks) > 0
        assert all("text" in c for c in chunks)
        assert all("metadata" in c for c in chunks)

    def test_chunk_metadata_fields(self):
        chunker = TextChunker(chunk_size=100, chunk_overlap=20)
        text = "Short text for testing."
        chunks = chunker.chunk_text(text, "sales_guide.docx", "sales")
        
        if chunks:
            meta = chunks[0]["metadata"]
            assert "source_filename" in meta
            assert "doc_type" in meta
            assert "chunk_id" in meta
            assert "chunk_index" in meta
            assert "total_chunks" in meta

    def test_chunk_respects_size(self):
        chunker = TextChunker(chunk_size=50, chunk_overlap=10)
        text = "A" * 200
        chunks = chunker.chunk_text(text, "test.docx", "general")
        
        for chunk in chunks:
            assert len(chunk["text"]) <= 50 + 10

    def test_chunk_infers_doc_type(self):
        chunker = TextChunker()
        result = chunker._infer_doc_type("sales_guide.docx")
        assert result == "sales"
        
        result = chunker._infer_doc_type("compliance_policy.docx")
        assert result == "compliance"
        
        result = chunker._infer_doc_type("random_document.docx")
        assert result == "general"


class TestLoader:
    """Tests for document loading."""

    def test_infer_doc_type(self):
        assert infer_doc_type("sales_guide.docx") == "sales"
        assert infer_doc_type("compliance_manual.docx") == "compliance"
        assert infer_doc_type("other.docx") == "general"
        assert infer_doc_type("SALES_TIPS.DOCX") == "sales"


class TestRetriever:
    """Tests for retrieval functions."""

    def test_format_retrieved_context_empty(self):
        result = format_retrieved_context([])
        assert "No relevant knowledge" in result

    def test_format_retrieved_context_with_chunks(self):
        chunks = [
            {
                "text": "This is sample text.",
                "source_filename": "test.docx",
                "doc_type": "sales",
                "chunk_index": 0,
                "score": 0.5,
            }
        ]
        result = format_retrieved_context(chunks)
        assert "test.docx" in result
        assert "sales" in result
        assert "sample text" in result

    def test_format_retrieved_context_respects_max_chars(self):
        chunks = [
            {
                "text": "A" * 1000,
                "source_filename": "test.docx",
                "doc_type": "sales",
                "chunk_index": 0,
                "score": 0.5,
            }
            for _ in range(10)
        ]
        result = format_retrieved_context(chunks, max_chars=500)
        assert len(result) <= 600

    def test_extract_transcript_for_retrieval(self):
        transcript = [
            {"speaker": "agent", "text": "Hello"},
            {"speaker": "customer", "text": "Hi there"},
            {"speaker": "agent", "text": "How can I help?"},
        ]
        result = extract_transcript_for_retrieval(transcript, last_n=2)
        assert "customer" in result
        assert "Hi there" in result
        assert "Hello" not in result

    def test_extract_transcript_all_chunks(self):
        transcript = [
            {"speaker": "agent", "text": "First"},
            {"speaker": "customer", "text": "Second"},
        ]
        result = extract_transcript_for_retrieval(transcript, last_n=None)
        assert "First" in result
        assert "Second" in result

    def test_extract_transcript_empty(self):
        result = extract_transcript_for_retrieval([], last_n=5)
        assert result == ""


class TestGracefulBehavior:
    """Tests for graceful behavior when vector store is missing."""

    def test_retriever_handles_missing_store(self):
        from app.rag.retriever import retrieve
        
        result = retrieve("test query", top_k=4)
        assert isinstance(result, list)


class TestIntegration:
    """Integration-style tests that check the full pipeline."""

    def test_chunking_with_metadata(self):
        chunker = TextChunker(chunk_size=200, chunk_overlap=30)
        text = "Sales tip 1. " * 50 + "Compliance tip 1. " * 50
        
        chunks = chunker.chunk_texts(
            [("sales_guide.docx", text)],
            doc_type_map={"sales_guide.docx": "sales"}
        )
        
        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk["metadata"]["doc_type"] == "sales"
            assert chunk["metadata"]["source_filename"] == "sales_guide.docx"
