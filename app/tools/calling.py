import asyncio
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


async def call_business(params: dict = {}) -> dict:
    """
    Calls YOUR phone number to notify you about a booking.
    In a real system this would call the actual business.
    """
    name   = params.get("name") or params.get("salon_name", "the business")
    phone  = params.get("phone_number") or settings.YOUR_PHONE_NUMBER
    detail = params.get("booking_details", "book an appointment")
    date   = params.get("date", "tomorrow")
    time   = params.get("time", params.get("time_preference", "afternoon"))

    if not settings.TWILIO_ACCOUNT_SID:
        return {
            "status":  "simulated",
            "message": f"[Simulated] Called {name} about {detail}",
        }

    if not phone:
        return {
            "status":  "skipped",
            "message": "No phone number available",
        }

    try:
        loop   = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, _make_call, name, phone, detail, date, time
        )
        return result
    except Exception as exc:
        logger.error(f"Call failed: {exc}")
        return {"status": "failed", "message": str(exc)}


def _make_call(name: str, phone: str, detail: str, date: str, time: str) -> dict:
    from twilio.rest import Client

    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    script = (
        f"Hello! This is Jarvis, your personal AI assistant. "
        f"I have completed your request. "
        f"I found {name} and have arranged to {detail} "
        f"on {date} in the {time}. "
        f"Your appointment has been added to your calendar. "
        f"Is there anything else you need? Goodbye!"
    )

    call = client.calls.create(
        twiml=f"<Response><Say voice='Polly.Joanna'>{script}</Say></Response>",
        to=phone,
        from_=settings.TWILIO_PHONE_NUMBER,
    )

    logger.info(f"Call placed to {phone}, SID: {call.sid}")

    return {
        "status":   "called",
        "call_sid": call.sid,
        "to":       phone,
        "message":  f"Called {phone} — confirmed {name} on {date} at {time}",
        "script":   script,
    }

def _generate_voice_script(business_name: str, detail: str) -> str:
    """Generate a natural-sounding call script."""
    return (
        f"Hello, my name is Jarvis and I am calling on behalf of my client. "
        f"I would like to {detail} at {business_name}. "
        f"Could you please let me know your availability? "
        f"Thank you very much."
    )