"""
Twilio integration service.

For MVP: provides clean method stubs and integration-ready placeholders.
All methods are documented with TODO markers showing exactly where
live Twilio SDK calls should be wired in.

When you're ready for production:
  pip install twilio
  from twilio.rest import Client
"""
import logging
from datetime import datetime, timezone

from app.core.config import settings

logger = logging.getLogger(__name__)


class TwilioService:
    """
    Wrapper around Twilio interactions.
    Instantiate once and inject as a dependency or use the module-level singleton.
    """

    def __init__(self) -> None:
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.phone_number = settings.TWILIO_PHONE_NUMBER
        self._client = None  # Lazy-init live Twilio client

    def _get_client(self):
        """
        Return a live Twilio REST client.
        TODO: Uncomment when twilio package is installed.
        """
        if self._client is None:
            # TODO: from twilio.rest import Client
            # TODO: self._client = Client(self.account_sid, self.auth_token)
            logger.warning("Twilio client not initialised — running in stub mode.")
        return self._client

    def is_configured(self) -> bool:
        """Return True if Twilio credentials are present in settings."""
        return bool(self.account_sid and self.auth_token and self.phone_number)

    def parse_webhook_event(self, form_data: dict) -> dict:
        """
        Parse raw Twilio webhook form data into a normalised event dict.

        Twilio sends form-encoded POST bodies. FastAPI parses these as Request
        form fields; pass them here as a plain dict.
        """
        return {
            "call_sid": form_data.get("CallSid"),
            "call_status": form_data.get("CallStatus"),
            "from_number": form_data.get("From"),
            "to_number": form_data.get("To"),
            "direction": form_data.get("Direction"),
            "account_sid": form_data.get("AccountSid"),
            "received_at": datetime.now(tz=timezone.utc).isoformat(),
        }

    def parse_transcript_event(self, payload: dict) -> dict:
        """
        Normalise a Twilio transcript streaming payload.
        Currently accepts simulated events; adapt for live Media Streams data.

        TODO: Support Twilio Media Streams / Transcription webhook format.
        """
        return {
            "call_sid": payload.get("call_sid"),
            "speaker": payload.get("speaker", "agent"),
            "text": payload.get("text", ""),
            "timestamp": payload.get(
                "timestamp", datetime.now(tz=timezone.utc).isoformat()
            ),
        }

    async def initiate_outbound_call(
        self, to: str, twiml_url: str
    ) -> dict:
        """
        Initiate an outbound call via Twilio.

        TODO: Implement with live Twilio client:
            call = self._get_client().calls.create(
                to=to,
                from_=self.phone_number,
                url=twiml_url,
            )
            return {"call_sid": call.sid, "status": call.status}
        """
        logger.info("STUB: initiate_outbound_call to=%s url=%s", to, twiml_url)
        return {
            "call_sid": "STUB_CA_NOT_IMPLEMENTED",
            "status": "stub",
            "message": "Live Twilio call initiation not yet configured.",
        }

    async def fetch_call_details(self, call_sid: str) -> dict:
        """
        Fetch live call status from Twilio by call SID.

        TODO: Implement with live Twilio client:
            call = self._get_client().calls(call_sid).fetch()
            return {"status": call.status, "duration": call.duration}
        """
        logger.info("STUB: fetch_call_details call_sid=%s", call_sid)
        return {
            "call_sid": call_sid,
            "status": "stub",
            "message": "Live Twilio call fetch not yet configured.",
        }

    def build_twiml_response(self, message: str = "") -> str:
        """
        Build a minimal TwiML XML response.
        Used to acknowledge Twilio webhook calls.
        """
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say>{message}</Say>
</Response>"""


# Module-level singleton
twilio_service = TwilioService()
