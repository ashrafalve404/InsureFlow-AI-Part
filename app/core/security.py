"""
Security utilities (JWT token helpers, API key validation, etc.).
Extend this module as auth requirements grow beyond MVP.
"""
import hashlib
import hmac

from app.core.config import settings


def verify_twilio_signature(signature: str, url: str, params: dict) -> bool:
    """
    Validate an incoming Twilio webhook signature.
    https://www.twilio.com/docs/usage/webhooks/webhooks-security

    In production, install `twilio` and use:
        twilio.request_validator.RequestValidator
    For MVP this provides the structural placeholder.
    """
    # TODO: Replace with full Twilio RequestValidator in production
    auth_token = settings.TWILIO_AUTH_TOKEN
    if not auth_token:
        return True  # Skip validation if not configured (dev mode)

    # Build the validation string: url + sorted key/value pairs
    s = url
    for key in sorted(params.keys()):
        s += key + params[key]

    mac = hmac.new(
        auth_token.encode("utf-8"), s.encode("utf-8"), hashlib.sha1
    ).digest()

    import base64
    expected = base64.b64encode(mac).decode("utf-8")
    return hmac.compare_digest(expected, signature)


def generate_api_key(prefix: str = "iflow") -> str:
    """Generate a random API key string (for future agent auth)."""
    import secrets
    token = secrets.token_urlsafe(32)
    return f"{prefix}_{token}"
