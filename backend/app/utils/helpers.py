"""
General utility helper functions.
"""
import json
import re
from typing import Any, Optional, List, Dict


def safe_parse_json(raw: str, fallback: Optional[dict] = None) -> dict:
    """
    Safely parse a JSON string. Strips markdown code fences if present.
    Returns `fallback` dict on any parse failure.
    """
    if fallback is None:
        fallback = {}

    try:
        # Strip markdown code fences like ```json ... ```
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
        return json.loads(cleaned.strip())
    except (json.JSONDecodeError, TypeError, AttributeError):
        return fallback


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to a maximum character length, appending ellipsis if needed."""
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + "..."


def format_transcript_for_prompt(chunks: List[Dict[str, Any]]) -> str:
    """
    Convert a list of transcript chunk dicts into a readable conversation string
    suitable for passing to the AI prompt.
    """
    lines: List[str] = []
    for chunk in chunks:
        speaker = chunk.get("speaker", "unknown").upper()
        text = chunk.get("text", "")
        lines.append(f"{speaker}: {text}")
    return "\n".join(lines)


def extract_field(data: dict, key: str, default: Any = None) -> Any:
    """Safely extract a field from a dict with a fallback default."""
    return data.get(key, default)
