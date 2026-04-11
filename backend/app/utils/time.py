"""
Time-related utility functions.
"""
from typing import Any, Optional, Union, List, Dict, Tuple
from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return the current UTC datetime (timezone-aware)."""
    return datetime.now(tz=timezone.utc)


def utcnow_naive() -> datetime:
    """
    Return current UTC datetime without timezone info.
    Use this for SQLite-compatible datetime columns (SQLite doesn't store tz).
    """
    return datetime.utcnow()


def format_iso(dt: Optional[datetime]) -> Optional[str]:
    """Format a datetime to ISO 8601 string, or return None if dt is None."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Assume UTC for naive datetimes from the database
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def duration_seconds(start: Optional[datetime], end: Optional[datetime]) -> Optional[int]:
    """
    Calculate duration in seconds between two datetimes.
    Returns None if either datetime is missing.
    """
    if start is None or end is None:
        return None
    # Normalize: strip tzinfo for arithmetic if both are naive
    if start.tzinfo is None and end.tzinfo is None:
        return int((end - start).total_seconds())
    if start.tzinfo is not None and end.tzinfo is not None:
        return int((end - start).total_seconds())
    # Mixed — normalize to naive UTC
    s = start.replace(tzinfo=None)
    e = end.replace(tzinfo=None)
    return int((e - s).total_seconds())
