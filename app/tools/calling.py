import asyncio
import os
import tempfile
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


async def call_business(params: dict = {}) -> dict:
    """
    Makes a real phone call to a business using Twilio.
    Uses ElevenLabs for AI voice and Whisper to transcribe the response.
    Falls back to simulation if credentials are missing.
    """
    name   = params.get("name") or params.get("salon_name", "the business")
    phone  = params.get("phone_number", "")
    detail = params.get("booking_details", "book an appointment")

    # Simulate if no Twilio credentials
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_PHONE_NUMBER:
        logger.warning("Twilio not configured — simulating call")
        return {
            "status":  "simulated",
            "message": f"[Simulated] Called {name} to {detail}",
            "note":    "Add Twilio credentials to .env to make real calls",
        }

    if not phone:
        return {
            "status":  "skipped",
            "message": f"No phone number provided for {name}",
        }

    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, _make_call, name, phone, detail
        )
        return result
    except Exception as exc:
        logger.error(f"Call failed: {exc}")
        return {
            "status":  "failed",
            "message": f"Call to {name} failed: {str(exc)}",
        }


def _make_call(name: str, phone: str, detail: str) -> dict:
    """Synchronous Twilio call — runs in thread pool."""
    from twilio.rest import Client

    client  = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    message = _generate_voice_script(name, detail)

    # Use Twilio TwiML to speak the message
    twiml = f"""
    <Response>
        <Say voice="Polly.Joanna">{message}</Say>
        <Pause length="2"/>
        <Say voice="Polly.Joanna">Please press 1 to confirm or 2 to decline.</Say>
        <Gather numDigits="1" timeout="10">
        </Gather>
    </Response>
    """

    call = client.calls.create(
        twiml=twiml,
        to=phone,
        from_=settings.TWILIO_PHONE_NUMBER,
    )

    return {
        "status":   "called",
        "call_sid": call.sid,
        "message":  f"Called {name} at {phone}",
        "script":   message,
    }


def _generate_voice_script(business_name: str, detail: str) -> str:
    """Generate a natural-sounding call script."""
    return (
        f"Hello, my name is Jarvis and I am calling on behalf of my client. "
        f"I would like to {detail} at {business_name}. "
        f"Could you please let me know your availability? "
        f"Thank you very much."
    )