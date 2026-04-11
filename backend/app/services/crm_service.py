"""
CRM Service — GoHighLevel (GHL) API integration.

Provides contact lookup and context retrieval for AI-assisted calls.
"""
import logging
import re
from typing import Optional, Dict, Any, List
import httpx

from app.core.config import settings
from app.schemas.crm import CRMContact

logger = logging.getLogger(__name__)

_crm_configured: Optional[bool] = None


def _is_configured() -> bool:
    """Check if CRM is properly configured."""
    global _crm_configured
    if _crm_configured is None:
        _crm_configured = (
            settings.CRM_ENABLED
            and settings.GHL_PRIVATE_INTEGRATION_TOKEN
            and settings.GHL_LOCATION_ID
        )
    return _crm_configured


async def lookup_contact_by_phone(phone: str) -> CRMContact:
    """
    Look up a contact in GHL by phone number.
    
    Args:
        phone: Phone number in E.164 format (e.g., +15551234567)
        
    Returns:
        CRMContact with contact data or empty contact if not found.
    """
    if not _is_configured():
        return _empty_contact()
    
    if not phone:
        return _empty_contact()
    
    clean_phone = _normalize_phone(phone)
    
    headers = {
        "Authorization": f"Bearer {settings.GHL_PRIVATE_INTEGRATION_TOKEN}",
        "Content-Type": "application/json",
        "Version": settings.GHL_API_VERSION,
    }
    
    url = f"{settings.GHL_API_BASE_URL}/api/v1/contacts/phones/{clean_phone}"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 404:
                logger.debug("Contact not found for phone: %s", phone)
                return _empty_contact()
            
            if response.status_code != 200:
                logger.warning("GHL API error: %s - %s", response.status_code, response.text)
                return _empty_contact()
            
            data = response.json()
            contact = data.get("contact", {})
            
            if not contact:
                return _empty_contact()
            
            return _normalize_contact(contact)
    
    except Exception as exc:
        logger.error("CRM lookup failed for phone %s: %s", phone, exc)
        return _empty_contact()


async def lookup_contact_by_email(email: str) -> CRMContact:
    """
    Look up a contact in GHL by email.
    
    Args:
        email: Email address
        
    Returns:
        CRMContact with contact data or empty contact if not found.
    """
    if not _is_configured():
        return _empty_contact()
    
    if not email:
        return _empty_contact()
    
    headers = {
        "Authorization": f"Bearer {settings.GHL_PRIVATE_INTEGRATION_TOKEN}",
        "Content-Type": "application/json",
        "Version": settings.GHL_API_VERSION,
    }
    
    url = f"{settings.GHL_API_BASE_URL}/api/v1/contacts/emails/{email}"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 404:
                logger.debug("Contact not found for email: %s", email)
                return _empty_contact()
            
            if response.status_code != 200:
                logger.warning("GHL API error: %s - %s", response.status_code, response.text)
                return _empty_contact()
            
            data = response.json()
            contact = data.get("contact", {})
            
            if not contact:
                return _empty_contact()
            
            return _normalize_contact(contact)
    
    except Exception as exc:
        logger.error("CRM lookup failed for email %s: %s", email, exc)
        return _empty_contact()


async def get_contact_by_id(contact_id: str) -> CRMContact:
    """
    Get a contact by GHL contact ID.
    
    Args:
        contact_id: GHL contact ID
        
    Returns:
        CRMContact with contact data or empty contact if not found.
    """
    if not _is_configured():
        return _empty_contact()
    
    if not contact_id:
        return _empty_contact()
    
    headers = {
        "Authorization": f"Bearer {settings.GHL_PRIVATE_INTEGRATION_TOKEN}",
        "Content-Type": "application/json",
        "Version": settings.GHL_API_VERSION,
    }
    
    url = f"{settings.GHL_API_BASE_URL}/api/v1/contacts/{contact_id}"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 404:
                logger.debug("Contact not found: %s", contact_id)
                return _empty_contact()
            
            if response.status_code != 200:
                logger.warning("GHL API error: %s - %s", response.status_code, response.text)
                return _empty_contact()
            
            contact = response.json()
            
            if not contact:
                return _empty_contact()
            
            return _normalize_contact(contact)
    
    except Exception as exc:
        logger.error("CRM lookup failed for contact_id %s: %s", contact_id, exc)
        return _empty_contact()


async def build_crm_context(
    phone: Optional[str] = None,
    email: Optional[str] = None,
) -> CRMContact:
    """
    Build CRM context by looking up contact by phone or email.
    
    Priority: phone > email
    
    Args:
        phone: Customer phone number
        email: Customer email address
        
    Returns:
        CRMContact with contact data or empty contact.
    """
    if not _is_configured():
        return _empty_contact()
    
    if phone:
        contact = await lookup_contact_by_phone(phone)
        if contact.contact_found:
            return contact
    
    if email:
        contact = await lookup_contact_by_email(email)
        if contact.contact_found:
            return contact
    
    return _empty_contact()


async def add_contact_note(contact_id: str, note: str) -> bool:
    """
    Add a note to a contact (future-ready placeholder).
    
    Args:
        contact_id: GHL contact ID
        note: Note content
        
    Returns:
        True if successful, False otherwise.
    """
    if not _is_configured():
        return False
    
    if not contact_id or not note:
        return False
    
    logger.info("Add contact note placeholder called for contact_id=%s", contact_id)
    return False


async def push_call_summary(contact_id: str, summary: str) -> bool:
    """
    Push call summary to CRM (future-ready placeholder).
    
    Args:
        contact_id: GHL contact ID
        summary: Call summary text
        
    Returns:
        True if successful, False otherwise.
    """
    if not _is_configured():
        return False
    
    if not contact_id or not summary:
        return False
    
    logger.info("Push call summary placeholder called for contact_id=%s", contact_id)
    return False


def _empty_contact() -> CRMContact:
    """Return an empty CRM contact."""
    return CRMContact(contact_found=False)


def _normalize_phone(phone: str) -> str:
    """Normalize phone number for API call."""
    clean = re.sub(r'[^\d+]', '', phone)
    if clean.startswith('+'):
        return clean
    if len(clean) == 10:
        return f"+{clean}"
    if len(clean) == 11:
        return f"+{clean}"
    return clean


def _normalize_contact(ghl_contact: Dict[str, Any]) -> CRMContact:
    """Normalize GHL contact response to internal format."""
    contact_id = ghl_contact.get("id") or ghl_contact.get("contact_id")
    
    first_name = ghl_contact.get("firstName") or ""
    last_name = ghl_contact.get("lastName") or ""
    full_name = f"{first_name} {last_name}".strip() or None
    
    phone = ghl_contact.get("phone") or ghl_contact.get("phoneNumber")
    if isinstance(phone, list) and phone:
        phone = phone[0]
    
    email = ghl_contact.get("email")
    if isinstance(email, list) and email:
        email = email[0]
    
    tags = ghl_contact.get("tags") or []
    if isinstance(tags, list):
        tags = [t.get("name", t) if isinstance(t, dict) else str(t) for t in tags]
    
    notes = ghl_contact.get("notes") or []
    notes_summary = None
    if notes:
        note_texts = []
        for note in notes[-3:]:
            if isinstance(note, dict):
                note_texts.append(note.get("body", "")[:200])
            elif isinstance(note, str):
                note_texts.append(note[:200])
        if note_texts:
            notes_summary = " | ".join(note_texts)
    
    custom_fields = ghl_contact.get("customFields") or {}
    if isinstance(custom_fields, list):
        custom_fields = {
            cf.get("id", ""): cf.get("value") for cf in custom_fields
            if isinstance(cf, dict)
        }
    
    pipeline_stage = ghl_contact.get("pipelineStage") or ghl_contact.get("stage")
    if isinstance(pipeline_stage, dict):
        pipeline_stage = pipeline_stage.get("name")
    
    opportunities = ghl_contact.get("opportunities") or []
    if isinstance(opportunities, list):
        opportunities = [
            opp.get("name", "") for opp in opportunities
            if isinstance(opp, dict) and opp.get("name")
        ]
    
    return CRMContact(
        contact_found=True,
        contact_id=contact_id,
        full_name=full_name,
        first_name=first_name or None,
        last_name=last_name or None,
        phone=phone,
        email=email,
        tags=tags,
        notes_summary=notes_summary,
        custom_fields=custom_fields,
        pipeline_stage=pipeline_stage,
        opportunities=opportunities,
        source="gohighlevel",
    )


def format_crm_context(contact: CRMContact) -> str:
    """
    Format CRM contact for AI prompts.
    
    Args:
        contact: CRMContact object
        
    Returns:
        Formatted context string.
    """
    if not contact.contact_found:
        return "No CRM context available."
    
    parts = ["=== CRM CONTEXT ==="]
    
    if contact.full_name:
        parts.append(f"Name: {contact.full_name}")
    
    if contact.pipeline_stage:
        parts.append(f"Pipeline Stage: {contact.pipeline_stage}")
    
    if contact.tags:
        parts.append(f"Tags: {', '.join(contact.tags)}")
    
    if contact.notes_summary:
        parts.append(f"Notes: {contact.notes_summary}")
    
    if contact.custom_fields:
        field_lines = []
        for key, value in contact.custom_fields.items():
            if value:
                field_lines.append(f"{key}: {value}")
        if field_lines:
            parts.append(f"Custom Fields: {'; '.join(field_lines)}")
    
    if contact.opportunities:
        parts.append(f"Opportunities: {', '.join(contact.opportunities)}")
    
    parts.append(f"=== END CRM CONTEXT ===")
    
    return "\n".join(parts)