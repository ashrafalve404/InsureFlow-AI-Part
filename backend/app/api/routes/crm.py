"""
CRM API routes for contact lookup and status.
"""
import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import Field

from app.core.config import settings
from app.schemas.crm import CRMContactResponse, CRMStatusResponse
from app.services import crm_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/crm", tags=["CRM"])


@router.get("/status", response_model=CRMStatusResponse)
async def get_crm_status():
    """
    Get the current CRM integration status.
    """
    token_present = bool(settings.GHL_PRIVATE_INTEGRATION_TOKEN)
    configured = settings.CRM_ENABLED and token_present and settings.GHL_LOCATION_ID
    
    return CRMStatusResponse(
        enabled=settings.CRM_ENABLED,
        provider=settings.CRM_PROVIDER,
        configured=configured,
        token_present=token_present,
    )


@router.get("/contact/by-phone", response_model=CRMContactResponse)
async def lookup_by_phone(
    phone: str = Query(..., description="Phone number in E.164 format"),
):
    """
    Look up a CRM contact by phone number.
    """
    if not settings.CRM_ENABLED:
        return CRMContactResponse(contact_found=False)
    
    if not settings.GHL_PRIVATE_INTEGRATION_TOKEN:
        return CRMContactResponse(contact_found=False)
    
    try:
        contact = await crm_service.lookup_contact_by_phone(phone)
        return CRMContactResponse(
            contact_found=contact.contact_found,
            contact_id=contact.contact_id,
            full_name=contact.full_name,
            first_name=contact.first_name,
            last_name=contact.last_name,
            phone=contact.phone,
            email=contact.email,
            tags=contact.tags,
            notes_summary=contact.notes_summary,
            custom_fields=contact.custom_fields,
            pipeline_stage=contact.pipeline_stage,
            opportunities=contact.opportunities,
            source=contact.source,
        )
    except Exception as exc:
        logger.error("CRM lookup failed: %s", exc)
        return CRMContactResponse(contact_found=False)


@router.get("/contact/by-email", response_model=CRMContactResponse)
async def lookup_by_email(
    email: str = Query(..., description="Email address"),
):
    """
    Look up a CRM contact by email.
    """
    if not settings.CRM_ENABLED:
        return CRMContactResponse(contact_found=False)
    
    if not settings.GHL_PRIVATE_INTEGRATION_TOKEN:
        return CRMContactResponse(contact_found=False)
    
    try:
        contact = await crm_service.lookup_contact_by_email(email)
        return CRMContactResponse(
            contact_found=contact.contact_found,
            contact_id=contact.contact_id,
            full_name=contact.full_name,
            first_name=contact.first_name,
            last_name=contact.last_name,
            phone=contact.phone,
            email=contact.email,
            tags=contact.tags,
            notes_summary=contact.notes_summary,
            custom_fields=contact.custom_fields,
            pipeline_stage=contact.pipeline_stage,
            opportunities=contact.opportunities,
            source=contact.source,
        )
    except Exception as exc:
        logger.error("CRM lookup failed: %s", exc)
        return CRMContactResponse(contact_found=False)