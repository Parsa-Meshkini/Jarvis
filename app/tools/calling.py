import asyncio
import logging
import os
import time
from app.core.config import settings

logger = logging.getLogger(__name__)

# Store active booking call state
booking_calls: dict[str, dict] = {}


async def call_business(params: dict = {}) -> dict:
    name    = params.get("name") or params.get("salon_name", "the business")
    phone   = params.get("phone_number") or os.getenv("TEST_BUSINESS_PHONE", "")
    date    = params.get("date", "tomorrow")
    time_   = params.get("time", params.get("time_preference", "afternoon"))
    service = params.get("service", "haircut")
    client_name = params.get("client_name", "my client")

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
            None, _make_negotiation_call,
            name, phone, date, time_, service, client_name
        )
        return result
    except Exception as exc:
        logger.error(f"Call failed: {exc}")
        return {"status": "failed", "message": str(exc)}


def _make_negotiation_call(
    name: str, phone: str, date: str,
    time_: str, service: str, client_name: str
) -> dict:
    from twilio.rest import Client

    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    # Get ngrok URL for webhook callbacks
    ngrok_url = os.getenv("NGROK_URL", "")
    if not ngrok_url:
        logger.warning("No NGROK_URL — using one-way call")
        return _make_one_way_call(client, name, phone, date, time_, service)

    # Store call context so the webhook can access it
    call_context = {
        "business_name": name,
        "date":          date,
        "time":          time_,
        "service":       service,
        "client_name":   client_name,
        "transcript":    [],
        "status":        "calling",
        "booked_time":   None,
    }

    # Initial TwiML — Jarvis speaks the opening and listens for response
    opening = (
        f"Hello, my name is Jarvis and I am calling on behalf of "
        f"my client {client_name} to book a {service} appointment. "
        f"I would like to schedule this for {date}. "
        f"Do you have any availability in the {time_}?"
    )

    twiml = _build_gather_twiml(
        text=opening,
        action_url=f"{ngrok_url}/voice/booking-respond",
        voice_id=settings.ELEVENLABS_VOICE_ID,
    )

    # Make the outbound call
    call = client.calls.create(
        twiml=twiml,
        to=phone,
        from_=settings.TWILIO_PHONE_NUMBER,
        record=True,
    )

    # Store context keyed by call SID
    booking_calls[call.sid] = call_context

    logger.info(f"Negotiation call started: {call.sid} to {phone}")

    # Wait for call to progress
    time.sleep(5)
    updated = client.calls(call.sid).fetch()

    return {
        "status":    "calling",
        "call_sid":  call.sid,
        "to":        phone,
        "business":  name,
        "message":   f"Calling {name} — Jarvis will negotiate and report back",
    }


def _make_one_way_call(client, name, phone, date, time_, service):
    """Fallback when no ngrok URL available."""
    call = client.calls.create(
        twiml=f"""<Response>
    <Say voice="Polly.Joanna-Neural" rate="90%">
        Hello, my name is Jarvis calling to book a {service} at {name}
        for {date} in the {time_}.
        Please call back this number to confirm. Thank you.
    </Say>
</Response>""",
        to=phone,
        from_=settings.TWILIO_PHONE_NUMBER,
    )
    return {"status": "called", "call_sid": call.sid, "message": f"Called {name}"}


def _build_gather_twiml(text: str, action_url: str, voice_id: str = "") -> str:
    """Build TwiML that speaks and then listens for a response."""

    # Try ElevenLabs
    audio_url = _generate_audio(text)
    safe_text = text.replace("&", "and").replace("<", "").replace(">", "").replace('"', "")

    if audio_url:
        speech_block = f"<Play>{audio_url}</Play>"
    else:
        speech_block = f'<Say voice="Polly.Joanna-Neural" rate="90%">{safe_text}</Say>'

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="speech"
            action="{action_url}"
            method="POST"
            speechTimeout="3"
            speechModel="phone_call"
            enhanced="true"
            language="en-US">
        {speech_block}
    </Gather>
    <Redirect method="POST">{action_url}?no_input=true</Redirect>
</Response>"""


def _generate_audio(text: str) -> str | None:
    """Generate ElevenLabs audio, return public URL or None."""
    try:
        if not settings.ELEVENLABS_API_KEY:
            return None
        ngrok_url = os.getenv("NGROK_URL", "")
        if not ngrok_url:
            return None

        from elevenlabs.client import ElevenLabs
        import hashlib

        client   = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
        voice_id = settings.ELEVENLABS_VOICE_ID or "cjVigY5qzO86Huf0OWal"

        audio    = client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id="eleven_flash_v2_5",
        )

        filename = f"booking_{hashlib.md5(text.encode()).hexdigest()[:8]}.mp3"
        filepath = f"/tmp/{filename}"

        with open(filepath, "wb") as f:
            for chunk in audio:
                f.write(chunk)

        return f"{ngrok_url}/voice/audio/{filename}"
    except Exception as exc:
        logger.error(f"ElevenLabs error: {exc}")
        return None