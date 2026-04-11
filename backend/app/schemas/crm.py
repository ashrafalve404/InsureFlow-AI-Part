"""
CRM data schemas for normalized CRM responses.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CRMContact(BaseModel):
    """Normalized CRM contact context."""
    contact_found: bool = False
    contact_id: Optional[str] = None
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    notes_summary: Optional[str] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    pipeline_stage: Optional[str] = None
    opportunities: List[str] = Field(default_factory=list)
    source: str = "gohighlevel"


class CRMStatusResponse(BaseModel):
    """CRM status response."""
    enabled: bool
    provider: str
    configured: bool
    token_present: bool


class CRMContactResponse(BaseModel):
    """CRM contact lookup response."""
    contact_found: bool
    contact_id: Optional[str] = None
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    notes_summary: Optional[str] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    pipeline_stage: Optional[str] = None
    opportunities: List[str] = Field(default_factory=list)
    source: str = "gohighlevel"