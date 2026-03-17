import asyncio
import logging
import os
import json
from fastapi import APIRouter, Request, Form
from fastapi.responses import Response
from app.core.config import settings
import httpx
import redis as redis_sync

logger        = logging.getLogger(__name__)
router        = APIRouter()
conversations: dict[str, list] = {}
_ngrok_url:   str = ""


# ── ngrok ─────────────────────────────────────────────────────────────────────

async def get_ngrok_url() -> str:
    global _ngrok_url
    if _ngrok_url:
        return _ngrok_url
    for _ in range(10):
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                res  = await client.get("http://ngrok:4040/api/tunnels")
                data = res.json()
                for tunnel in data.get("tunnels", []):
                    if tunnel.get("proto") == "https":
                        _ngrok_url = tunnel["public_url"]
                        logger.info(f"ngrok URL: {_ngrok_url}")
                        return _ngrok_url
        except Exception:
            pass
        await asyncio.sleep(2)
    return os.getenv("NGROK_URL", "")


# ── Redis history ──────────────────────────────────────────────────────────────

def _get_redis_client():
    try:
        url        = settings.REDIS_URL.replace("redis://", "")
        host, port = url.split(":")
        return redis_sync.Redis(
            host=host, port=int(port),
            decode_responses=True,
            socket_connect_timeout=3,
        )
    except Exception as exc:
        logger.error(f"Redis connection failed: {exc}")
        return None


def _get_history(call_sid: str) -> list:
    r = _get_redis_client()
    if r:
        try:
            data = r.get(f"voice:{call_sid}")
            if data:
                history = json.loads(data)
                logger.info(f"[Memory] Loaded {len(history)} turns for {call_sid}")
                return history
        except Exception as exc:
            logger.error(f"[Memory] Load failed: {exc}")
    return conversations.get(call_sid, [])


def _save_history(call_sid: str, history: list) -> None:
    r = _get_redis_client()
    if r:
        try:
            r.setex(f"voice:{call_sid}", 3600, json.dumps(history))
            logger.info(f"[Memory] Saved {len(history)} turns for {call_sid}")
            return
        except Exception as exc:
            logger.error(f"[Memory] Save failed: {exc}")
    conversations[call_sid] = history


# ── OpenAI brain ───────────────────────────────────────────────────────────────

async def _get_jarvis_reply(user_input: str, history: list, call_sid: str) -> str:
    from openai import AsyncOpenAI
    from app.agents.memory import build_user_context

    client  = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    context = await build_user_context()

    # Build a rich system prompt with user's actual details
    system = f"""You are Jarvis, a helpful AI assistant on a phone call.

ABOUT THE USER:
- Name: {context.get('name', 'unknown')}
- Location: {context.get('location', 'unknown')}
- Preferred time: {context.get('preferred_time', 'afternoon')}
- Phone: {context.get('phone', 'not provided')}

RULES:
- Keep responses SHORT — 1 to 3 sentences maximum
- Never use markdown, bullet points, asterisks, or special characters
- Speak naturally as if talking on the phone
- Be warm, helpful and decisive
- When asked for a name, give the user's name: {context.get('name', 'unknown')}
- When asked for a phone number, say you will follow up by message

BOOKING FLOW:
- When given available times, PICK THE FIRST ONE and confirm immediately
- When user says yes, confirm and wrap up
- Do NOT ask for the same information twice"""

    messages = [{"role": "system", "content": system}]
    for msg in history[:-1]:
        messages.append({
            "role": "assistant" if msg["role"] == "assistant" else "user",
            "content": msg["content"],
        })
    messages.append({"role": "user", "content": user_input})

    logger.info(f"[{call_sid}] OpenAI — {len(messages)} messages, user={context.get('name')}")

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=150,
            temperature=0.7,
        )
        reply = (response.choices[0].message.content
                 .strip()
                 .replace("*", "")
                 .replace("#", "")
                 .replace("`", ""))
        logger.info(f"[{call_sid}] Jarvis replied: '{reply}'")
        return reply
    except Exception as exc:
        logger.error(f"[{call_sid}] OpenAI error: {exc}")
        return "I am having a little trouble, could you say that again please?"


# ── TwiML helpers ──────────────────────────────────────────────────────────────

def _respond_with_voice(
    text: str, gather_action: str, call_sid: str, ngrok_url: str = ""
) -> str:
    if settings.ELEVENLABS_API_KEY and ngrok_url:
        audio_url = _generate_elevenlabs_audio(text, call_sid, ngrok_url)
        if audio_url:
            return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{audio_url}</Play>
    <Gather input="speech"
            action="{gather_action}"
            method="POST"
            speechTimeout="4"
            speechModel="phone_call"
            enhanced="true"
            language="en-US"
            profanityFilter="false">
    </Gather>
    <Redirect method="POST">{gather_action}</Redirect>
</Response>"""

    safe = (text.replace("&", "and")
               .replace("<", "")
               .replace(">", "")
               .replace('"', ""))
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="speech"
            action="{gather_action}"
            method="POST"
            speechTimeout="4"
            speechModel="phone_call"
            enhanced="true"
            language="en-US"
            profanityFilter="false">
        <Say voice="Polly.Joanna-Neural" rate="90%">{safe}</Say>
    </Gather>
    <Redirect method="POST">{gather_action}</Redirect>
</Response>"""


def _end_call(text: str) -> str:
    safe = (text.replace("&", "and")
               .replace("<", "")
               .replace(">", "")
               .replace('"', ""))
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna-Neural" rate="95%">{safe}</Say>
    <Hangup/>
</Response>"""


def _generate_elevenlabs_audio(text: str, call_sid: str, ngrok_url: str) -> str | None:
    try:
        from elevenlabs.client import ElevenLabs
        client   = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
        voice_id = settings.ELEVENLABS_VOICE_ID or "cjVigY5qzO86Huf0OWal"
        audio    = client.text_to_speech.convert(
            text=text, voice_id=voice_id, model_id="eleven_flash_v2_5"
        )
        filename = f"audio_{call_sid}_{abs(hash(text))}.mp3"
        filepath = f"/tmp/{filename}"
        with open(filepath, "wb") as f:
            for chunk in audio:
                f.write(chunk)
        return f"{ngrok_url}/voice/audio/{filename}"
    except Exception as exc:
        logger.error(f"ElevenLabs error: {exc}")
        return None


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.post("/voice/incoming")
async def voice_incoming(request: Request):
    form      = await request.form()
    call_sid  = form.get("CallSid", "unknown")
    logger.info(f"Incoming call: {call_sid}")

    ngrok_url = await get_ngrok_url()
    greeting  = "Hello, I am Jarvis your personal AI assistant. How can I help you today?"

    history = [{"role": "assistant", "content": greeting}]
    _save_history(call_sid, history)

    return Response(
        content=_respond_with_voice(
            text=greeting,
            gather_action=f"{ngrok_url}/voice/booking-respond",
            call_sid=call_sid,
            ngrok_url=ngrok_url,
        ),
        media_type="application/xml",
    )


@router.post("/voice/booking-respond")
async def voice_booking_respond(
    request:      Request,
    SpeechResult: str   = Form(default=""),
    CallSid:      str   = Form(default="unknown"),
    Confidence:   float = Form(default=0.0),
):
    logger.info(f"[{CallSid}] Heard: '{SpeechResult}' (confidence: {Confidence})")
    ngrok_url = await get_ngrok_url()

    # Handle empty speech
    if not SpeechResult.strip():
        empty_count = conversations.get(f"{CallSid}_empty", 0) + 1
        conversations[f"{CallSid}_empty"] = empty_count
        if empty_count >= 3:
            conversations.pop(f"{CallSid}_empty", None)
            return Response(
                content=_end_call("I could not hear you clearly. Please call back when you are ready. Goodbye!"),
                media_type="application/xml",
            )
        return Response(
            content=_respond_with_voice(
                text="I am still here, please go ahead.",
                gather_action=f"{ngrok_url}/voice/booking-respond",
                call_sid=CallSid,
                ngrok_url=ngrok_url,
            ),
            media_type="application/xml",
        )

    # Reset empty counter
    conversations.pop(f"{CallSid}_empty", None)

    # Load history → add user turn → get reply → save
    history = _get_history(CallSid)
    logger.info(f"[{CallSid}] History has {len(history)} previous turns")

    history.append({"role": "user", "content": SpeechResult})
    reply = await _get_jarvis_reply(SpeechResult, history, CallSid)
    history.append({"role": "assistant", "content": reply})
    _save_history(CallSid, history)

    # End call if user says goodbye
    end_phrases = ["goodbye", "bye", "hang up", "that's all", "thanks bye", "thank you goodbye"]
    if any(p in SpeechResult.lower() for p in end_phrases):
        return Response(content=_end_call(reply), media_type="application/xml")

    return Response(
        content=_respond_with_voice(
            text=reply,
            gather_action=f"{ngrok_url}/voice/booking-respond",
            call_sid=CallSid,
            ngrok_url=ngrok_url,
        ),
        media_type="application/xml",
    )


# ── Status endpoints ───────────────────────────────────────────────────────────

@router.get("/voice/status/{call_sid}")
async def voice_status(call_sid: str):
    history = _get_history(call_sid)
    return {
        "call_sid":   call_sid,
        "active":     bool(history),
        "turns":      len(history),
        "transcript": history,
    }


@router.get("/voice/active")
async def active_calls():
    from app.tools.calling import booking_calls

    # Combine inbound conversations + outbound booking calls
    active = []

    for sid, h in conversations.items():
        if not sid.endswith("_empty"):
            active.append({
                "call_sid":     sid,
                "turns":        len(h),
                "last_message": h[-1]["content"] if h else "",
                "type":         "inbound",
            })

    for sid, ctx in booking_calls.items():
        transcript = ctx.get("transcript", [])
        active.append({
            "call_sid":     sid,
            "turns":        len(transcript),
            "last_message": transcript[-1]["content"] if transcript else ctx.get("status", "calling"),
            "type":         "outbound",
            "business":     ctx.get("business_name", ""),
            "status":       ctx.get("status", "calling"),
        })

    return {"active_calls": active}


@router.get("/voice/status/{call_sid}")
async def voice_status(call_sid: str):
    from app.tools.calling import booking_calls

    # Check inbound conversations first
    history = _get_history(call_sid)
    if history:
        return {
            "call_sid":   call_sid,
            "active":     True,
            "turns":      len(history),
            "transcript": history,
            "type":       "inbound",
        }

    # Check outbound booking calls
    ctx = booking_calls.get(call_sid, {})
    if ctx:
        transcript = ctx.get("transcript", [])
        return {
            "call_sid":   call_sid,
            "active":     ctx.get("status") == "calling",
            "turns":      len(transcript),
            "transcript": transcript,
            "type":       "outbound",
            "business":   ctx.get("business_name", ""),
            "booked_time": ctx.get("booked_time", ""),
            "status":     ctx.get("status", "unknown"),
        }

    return {
        "call_sid":   call_sid,
        "active":     False,
        "turns":      0,
        "transcript": [],
    }

async def call_business(params: dict = {}) -> dict:
    name    = params.get("name") or params.get("salon_name", "the business")
    phone   = params.get("phone_number") or params.get("phone", "")
    date    = params.get("date", "tomorrow")
    time_   = params.get("time", params.get("time_preference", "afternoon"))
    service = params.get("service", "haircut")
    client_name = params.get("client_name", params.get("name", "my client"))

    if not settings.TWILIO_ACCOUNT_SID:
        return {
            "status":  "simulated",
            "message": f"Jarvis would call {name} to book {service} on {date} at {time_}",
            "note":    "Add Twilio credentials to enable real calling",
        }

    if not phone:
        # No phone number — try to get it from Google Maps
        return {
            "status":  "no_phone",
            "message": f"Found {name} but no phone number available. Please call them directly or provide a phone number.",
            "business": name,
            "address": params.get("address", ""),
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
        return {
            "status":  "failed",
            "message": f"Could not reach {name}. You may want to call them directly.",
            "business": name,
            "phone": phone,
        }