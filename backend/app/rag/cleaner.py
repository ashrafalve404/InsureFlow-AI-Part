"""
Text cleaner — normalizes extracted text from DOCX files.
"""
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """
    Clean and normalize extracted text.
    
    Operations:
    - Strip leading/trailing whitespace
    - Collapse multiple blank lines into single line breaks
    - Remove empty paragraphs
    - Normalize internal whitespace (multiple spaces -> single space)
    - Preserve paragraph structure with double line breaks
    
    Args:
        text: Raw text extracted from DOCX.
        
    Returns:
        Cleaned and normalized text.
    """
    if not text:
        return ""
    
    cleaned = text
    
    cleaned = cleaned.strip()
    
    cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)
    
    lines = cleaned.split('\n')
    non_empty_lines = [line.strip() for line in lines if line.strip()]
    cleaned = '\n\n'.join(non_empty_lines)
    
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    
    logger.debug("Cleaned text | original_len=%d cleaned_len=%d", len(text), len(cleaned))
    
    return cleaned


def split_into_paragraphs(text: str) -> list[str]:
    """
    Split text into paragraphs for chunking.
    
    Args:
        text: Cleaned text.
        
    Returns:
        List of paragraph strings.
    """
    paragraphs = text.split('\n\n')
    return [p.strip() for p in paragraphs if p.strip()]


def truncate_for_logging(text: str, max_length: int = 200) -> str:
    """Truncate text for logging purposes."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."
