import asyncio
import logging
import time
from app.core.config import settings

logger = logging.getLogger(__name__)


async def call_business(params: dict = {}) -> dict:
    """
    Makes a real phone call to a business to book an appointment.
    Uses Twilio with a conversational script.
    """
    name    = params.get("name") or params.get("salon_name", "the business")
    phone   = params.get("phone_number") or os.getenv("TEST_BUSINESS_PHONE", "")
    date    = params.get("date", "tomorrow")
    time_   = params.get("time", params.get("time_preference", "afternoon"))
    service = params.get("service", "haircut")

    if not settings.TWILIO_ACCOUNT_SID:
        return {
            "status":  "simulated",
            "message": f"[Simulated] Called {name} to book {service} on {date} at {time_}",
        }

    if not phone:
        return {
            "status":  "skipped",
            "message": "No phone number provided",
        }

    try:
        loop   = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, _make_booking_call, name, phone, date, time_, service
        )
        return result
    except Exception as exc:
        logger.error(f"Call failed: {exc}")
        return {"status": "failed", "message": str(exc)}


def _make_booking_call(
    name: str, phone: str, date: str, time_: str, service: str
) -> dict:
    from twilio.rest import Client
    import os

    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    # Build the conversation script
    # Twilio will speak this, gather a response, then speak again
    script = _build_booking_script(name, service, date, time_)

    call = client.calls.create(
        twiml=script,
        to=phone,
        from_=settings.TWILIO_PHONE_NUMBER,
        # Record the call so you can review it
        record=True,
    )

    logger.info(f"Call placed to {phone}, SID: {call.sid}")

    # Wait and check the call status
    time.sleep(3)
    updated_call = client.calls(call.sid).fetch()

    return {
        "status":       "called",
        "call_sid":     call.sid,
        "call_status":  updated_call.status,
        "to":           phone,
        "business":     name,
        "service":      service,
        "date":         date,
        "time":         time_,
        "message":      f"Called {name} at {phone} to book {service} on {date}",
        "recording":    "Check Twilio console for call recording",
    }


def _build_booking_script(
    name: str, service: str, date: str, time_: str
) -> str:
    """
    Builds a TwiML script that handles the full booking conversation.
    Twilio speaks each line and waits for responses.
    """
    return f"""
    <Response>
        <Say voice="Polly.Joanna" rate="95%">
            Hello, my name is Jarvis and I am calling on behalf of my client
            to book a {service} appointment.
        </Say>

        <Pause length="1"/>

        <Say voice="Polly.Joanna" rate="95%">
            I would like to schedule a {service} for {date}.
            Do you have availability in the {time_}?
        </Say>

        <Pause length="1"/>

        <Say voice="Polly.Joanna" rate="95%">
            My client is flexible between 1pm and 5pm if the {time_} is fully booked.
        </Say>

        <Pause length="1"/>

        <Say voice="Polly.Joanna" rate="95%">
            Could you please let me know what times are available?
            I can be reached at this number to confirm the booking.
            Thank you very much for your time.
        </Say>
    </Response>
    """