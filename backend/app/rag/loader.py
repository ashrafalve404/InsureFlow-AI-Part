"""
DOCX file loader — extracts plain text from .docx files.
"""
import logging
from pathlib import Path
from typing import List, Optional
import docx

logger = logging.getLogger(__name__)


def load_docx(file_path: Path) -> str:
    """
    Load a DOCX file and extract all paragraph text.
    
    Args:
        file_path: Path to the .docx file.
        
    Returns:
        Extracted text with paragraph breaks preserved.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"DOCX file not found: {file_path}")
    
    if file_path.suffix.lower() != ".docx":
        raise ValueError(f"Expected .docx file, got: {file_path.suffix}")
    
    try:
        doc = docx.Document(str(file_path))
        paragraphs = []
        
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                paragraphs.append(text)
        
        extracted_text = "\n\n".join(paragraphs)
        logger.debug("Loaded DOCX: %s | paragraphs: %d", file_path.name, len(paragraphs))
        
        return extracted_text
    
    except Exception as exc:
        logger.error("Failed to load DOCX %s: %s", file_path, exc)
        raise


def load_all_docx(directory: Path) -> List[tuple[str, str]]:
    """
    Load all .docx files from a directory.
    
    Args:
        directory: Path to directory containing .docx files.
        
    Returns:
        List of tuples (filename, extracted_text).
    """
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    docx_files = sorted(directory.glob("*.docx"))
    
    if not docx_files:
        logger.warning("No .docx files found in: %s", directory)
        return []
    
    results = []
    for file_path in docx_files:
        try:
            text = load_docx(file_path)
            results.append((file_path.name, text))
            logger.info("Loaded: %s", file_path.name)
        except Exception as exc:
            logger.error("Skipping %s due to error: %s", file_path.name, exc)
    
    return results


def infer_doc_type(filename: str) -> str:
    """
    Infer document type from filename.
    
    Args:
        filename: Name of the document file.
        
    Returns:
        doc_type: 'sales', 'compliance', or 'general'.
    """
    lower_name = filename.lower()
    
    if "sales" in lower_name:
        return "sales"
    elif "compliance" in lower_name:
        return "compliance"
    else:
        return "general"
