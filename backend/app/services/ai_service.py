"""
AI Service — all OpenAI interaction is isolated here.

Design principles:
- Every public method is async and independently callable.
- All methods use defensive parsing so a malformed AI response never crashes the app.
- Prompts are imported from app/prompts/sales_assistant.py.
- The OpenAI client is instantiated once (lazy singleton).
"""
import logging
from typing import Any, Optional, Union, List, Dict, Tuple, Any

from openai import AsyncOpenAI, APIError

from app.core.config import settings
from app.prompts.sales_assistant import (
    CALL_STAGE_DETECTION_SYSTEM_PROMPT,
    COMPLIANCE_MONITORING_SYSTEM_PROMPT,
    LIVE_ASSISTANCE_SYSTEM_PROMPT,
    OBJECTION_DETECTION_SYSTEM_PROMPT,
    POST_CALL_SUMMARY_SYSTEM_PROMPT,
)
from app.schemas.suggestion import LiveAIOutput, PostCallSummaryResponse
from app.utils.constants import CallStage, ObjectionLabel
from app.utils.helpers import format_transcript_for_prompt, safe_parse_json

try:
    from app.rag import retriever as rag_module
except ImportError:
    rag_module = None

try:
    from app.services import crm_service
except ImportError:
    crm_service = None

logger = logging.getLogger(__name__)

# ── OpenAI client singleton ────────────────────────────────────────────────────

_client: Optional[AsyncOpenAI] = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


# ── Internal helper ────────────────────────────────────────────────────────────

async def _chat(system_prompt: str, user_content: str) -> str:
    """
    Call the OpenAI Chat Completions API and return the raw assistant text.
    Raises on API errors so callers can apply their own fallback logic.
    """
    client = _get_client()
    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        temperature=settings.AI_TEMPERATURE,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )
    return response.choices[0].message.content or ""


# ── Public service methods ─────────────────────────────────────────────────────

async def generate_live_assistance(
    transcript_chunks: List[Dict[str, Any]],
    customer_phone: Optional[str] = None,
    customer_email: Optional[str] = None,
) -> LiveAIOutput:
    """
    Analyze recent transcript chunks and return a structured live suggestion.
    Optionally uses RAG to retrieve relevant knowledge context.
    Optionally uses CRM to retrieve customer context.

    Falls back to safe defaults if the AI call fails or response is malformed.
    """
    conversation = format_transcript_for_prompt(transcript_chunks)
    
    crm_context = ""
    if settings.CRM_ENABLED and crm_service is not None and (customer_phone or customer_email):
        try:
            crm_contact = await crm_service.build_crm_context(
                phone=customer_phone,
                email=customer_email,
            )
            if crm_contact.contact_found:
                crm_context = crm_service.format_crm_context(crm_contact)
                logger.debug("Retrieved CRM context for %s", customer_phone or customer_email)
        except Exception as exc:
            logger.warning("CRM lookup failed, continuing without context: %s", exc)
    
    knowledge_context = ""
    if settings.RAG_ENABLED and rag_module is not None:
        try:
            rag_chunks = await rag_module.retrieve_for_live_suggestion(transcript_chunks)
            if rag_chunks:
                knowledge_context = rag_module.format_retrieved_context(rag_chunks)
                logger.debug("Retrieved %d RAG chunks for live assistance", len(rag_chunks))
        except Exception as exc:
            logger.warning("RAG retrieval failed, continuing without context: %s", exc)
    
    user_content = f"Recent conversation:\n{conversation}\n\n"
    if crm_context:
        user_content += f"{crm_context}\n\n"
    if knowledge_context:
        user_content += f"{knowledge_context}\n\n"
    user_content += "Provide your analysis."

    try:
        raw = await _chat(LIVE_ASSISTANCE_SYSTEM_PROMPT, user_content)
        data = safe_parse_json(raw)
        return LiveAIOutput(
            suggested_response=str(
                data.get("suggested_response", "Please continue — I'm listening.")
            ),
            objection_label=_safe_objection_label(data.get("objection_label")),
            compliance_warning=data.get("compliance_warning") or None,
            call_stage=_safe_call_stage(data.get("call_stage")),
        )
    except APIError as exc:
        logger.error("OpenAI API error in generate_live_assistance: %s", exc)
        return _fallback_live_output()
    except Exception as exc:
        logger.exception("Unexpected error in generate_live_assistance: %s", exc)
        return _fallback_live_output()


async def detect_objection(customer_text: str) -> Dict[str, Any]:
    """
    Detect the objection label from a customer utterance using AI.
    Returns {"objection_label": str, "confidence": float}.
    """
    try:
        raw = await _chat(
            OBJECTION_DETECTION_SYSTEM_PROMPT,
            f"Customer said: \"{customer_text}\"",
        )
        data = safe_parse_json(raw)
        return {
            "objection_label": _safe_objection_label(data.get("objection_label")),
            "confidence": float(data.get("confidence", 0.0)),
        }
    except Exception as exc:
        logger.warning("AI objection detection failed: %s", exc)
        return {"objection_label": ObjectionLabel.NONE, "confidence": 0.0}


async def detect_compliance_risk(
    text: str,
    transcript_chunks: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Detect compliance/risk issues in transcript text using AI.
    Optionally uses RAG to retrieve compliance knowledge context.
    
    Returns {"has_risk": bool, "warning": Optional[str], "trigger_phrase": Optional[str]}.
    """
    knowledge_context = ""
    if settings.RAG_ENABLED and rag_module is not None and transcript_chunks:
        try:
            rag_chunks = await rag_module.retrieve_for_compliance(transcript_chunks)
            if rag_chunks:
                knowledge_context = rag_module.format_retrieved_context(rag_chunks)
                logger.debug("Retrieved %d RAG chunks for compliance", len(rag_chunks))
        except Exception as exc:
            logger.warning("RAG retrieval for compliance failed: %s", exc)
    
    user_content = f"Text to review: \"{text}\""
    if knowledge_context:
        user_content += f"\n\n{knowledge_context}"
    
    try:
        raw = await _chat(
            COMPLIANCE_MONITORING_SYSTEM_PROMPT,
            user_content,
        )
        data = safe_parse_json(raw)
        return {
            "has_risk": bool(data.get("has_risk", False)),
            "warning": data.get("warning") or None,
            "trigger_phrase": data.get("trigger_phrase") or None,
        }
    except Exception as exc:
        logger.warning("AI compliance detection failed: %s", exc)
        return {"has_risk": False, "warning": None, "trigger_phrase": None}


async def detect_call_stage(transcript_chunks: List[Dict[str, Any]]) -> str:
    """
    Infer the current call stage from recent transcript chunks.
    Returns one of the CallStage constants.
    """
    conversation = format_transcript_for_prompt(transcript_chunks)
    try:
        raw = await _chat(
            CALL_STAGE_DETECTION_SYSTEM_PROMPT,
            f"Transcript:\n{conversation}",
        )
        data = safe_parse_json(raw)
        return _safe_call_stage(data.get("call_stage"))
    except Exception as exc:
        logger.warning("AI call stage detection failed: %s", exc)
        return CallStage.UNKNOWN


async def generate_post_call_summary(
    transcript_chunks: List[Dict[str, Any]],
    session_id: int,
) -> PostCallSummaryResponse:
    """
    Generate a structured post-call summary from the full transcript.
    Falls back to a minimal safe response on failure.
    """
    conversation = format_transcript_for_prompt(transcript_chunks)
    try:
        raw = await _chat(
            POST_CALL_SUMMARY_SYSTEM_PROMPT,
            f"Full call transcript:\n{conversation}",
        )
        data = safe_parse_json(raw)
        return PostCallSummaryResponse(
            session_id=session_id,
            overall_summary=str(data.get("overall_summary", "Summary unavailable.")),
            main_concerns=_safe_list(data.get("main_concerns")),
            objections_raised=_safe_list(data.get("objections_raised")),
            compliance_warnings=_safe_list(data.get("compliance_warnings")),
            suggested_next_action=str(
                data.get("suggested_next_action", "Follow up with the customer.")
            ),
        )
    except Exception as exc:
        logger.exception("Post-call summary generation failed: %s", exc)
        return PostCallSummaryResponse(
            session_id=session_id,
            overall_summary="Summary could not be generated.",
            main_concerns=[],
            objections_raised=[],
            compliance_warnings=[],
            suggested_next_action="Review transcript manually and follow up.",
        )


# ── Private helpers ────────────────────────────────────────────────────────────

def _safe_objection_label(value: Any) -> str:
    valid = {
        ObjectionLabel.PRICE,
        ObjectionLabel.NOT_INTERESTED,
        ObjectionLabel.NEEDS_TIME,
        ObjectionLabel.ALREADY_HAVE_SOLUTION,
        ObjectionLabel.HESITANT,
        ObjectionLabel.NONE,
    }
    if isinstance(value, str) and value.lower() in valid:
        return value.lower()
    return ObjectionLabel.NONE


def _safe_call_stage(value: Any) -> str:
    valid = {
        CallStage.OPENING,
        CallStage.DISCOVERY,
        CallStage.QUALIFICATION,
        CallStage.PITCH,
        CallStage.OBJECTION_HANDLING,
        CallStage.CLOSING,
        CallStage.UNKNOWN,
    }
    if isinstance(value, str) and value.lower() in valid:
        return value.lower()
    return CallStage.UNKNOWN


def _safe_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _fallback_live_output() -> LiveAIOutput:
    return LiveAIOutput(
        suggested_response="Please continue — I'm here to help.",
        objection_label=ObjectionLabel.NONE,
        compliance_warning=None,
        call_stage=CallStage.UNKNOWN,
    )
