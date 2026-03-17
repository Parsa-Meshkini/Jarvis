import asyncio
import logging
import os
from fastapi import APIRouter, Request, Form
from fastapi.responses import Response
from app.core.config import settings
import httpx

logger        = logging.getLogger(__name__)
router        = APIRouter()
conversations: dict[str, list] = {}

# Cache the ngrok URL so we don't fetch it on every request
_ngrok_url: str = ""


async def get_ngrok_url() -> str:
    """Fetches the current ngrok public URL from the ngrok API."""
    global _ngrok_url
    if _ngrok_url:
        return _ngrok_url

    # Try up to 10 times — ngrok takes a few seconds to start
    for attempt in range(10):
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                res  = await client.get("http://ngrok:4040/api/tunnels")
                data = res.json()
                tunnels = data.get("tunnels", [])
                for tunnel in tunnels:
                    if tunnel.get("proto") == "https":
                        _ngrok_url = tunnel["public_url"]
                        logger.info(f"ngrok URL: {_ngrok_url}")
                        return _ngrok_url
        except Exception:
            pass
        await asyncio.sleep(2)

    # Fallback to env var if ngrok API unreachable
    return os.getenv("NGROK_URL", "")


@router.post("/voice/incoming")
async def voice_incoming(request: Request):
    form     = await request.form()
    call_sid = form.get("CallSid", "unknown")
    logger.info(f"Incoming call: {call_sid}")

    conversations[call_sid] = []
    ngrok_url = await get_ngrok_url()

    greeting  = "Hello, I am Jarvis your personal AI assistant. How can I help you today?"
    twiml     = _respond_with_voice(
        text=greeting,
        gather_action=f"{ngrok_url}/voice/respond",
        call_sid=call_sid,
        ngrok_url=ngrok_url,
    )

    return Response(content=twiml, media_type="application/xml")


@router.post("/voice/respond")
async def voice_respond(
    request:      Request,
    SpeechResult: str   = Form(default=""),
    CallSid:      str   = Form(default="unknown"),
    Confidence:   float = Form(default=0.0),
):
    logger.info(f"[{CallSid}] User said: {SpeechResult}")
    ngrok_url = await get_ngrok_url()

    if not SpeechResult.strip():
        twiml = _respond_with_voice(
            text="I didn't catch that. Could you say that again?",
            gather_action=f"{ngrok_url}/voice/respond",
            call_sid=CallSid,
            ngrok_url=ngrok_url,
        )
        return Response(content=twiml, media_type="application/xml")

    history = conversations.get(CallSid, [])
    history.append({"role": "user", "content": SpeechResult})

    reply = await _get_jarvis_reply(SpeechResult, history, CallSid)
    history.append({"role": "assistant", "content": reply})
    conversations[CallSid] = history

    end_phrases = ["goodbye", "bye", "hang up", "end call", "that's all", "thank you goodbye"]
    if any(phrase in SpeechResult.lower() for phrase in end_phrases):
        twiml = _end_call(reply)
    else:
        twiml = _respond_with_voice(
            text=reply,
            gather_action=f"{ngrok_url}/voice/respond",
            call_sid=CallSid,
            ngrok_url=ngrok_url,
        )

    return Response(content=twiml, media_type="application/xml")


async def _get_jarvis_reply(user_input: str, history: list, call_sid: str) -> str:
    import google.generativeai as genai
    from concurrent.futures import ThreadPoolExecutor

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(
        os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    )

    system = """You are Jarvis, a helpful personal AI assistant on a phone call.

Rules:
- Keep responses SHORT — 1 to 3 sentences maximum
- Never use markdown, bullet points, or special characters
- Speak naturally as if talking out loud
- Be warm, helpful and conversational
- If asked to find something, say you are looking it up
- Always end with a follow-up question if the task is not complete
"""

    messages = []
    for msg in history[:-1]:
        messages.append(f"{msg['role'].upper()}: {msg['content']}")

    full_prompt = f"""{system}

CONVERSATION:
{chr(10).join(messages)}

USER: {user_input}

JARVIS:"""

    executor = ThreadPoolExecutor(max_workers=2)
    loop     = asyncio.get_event_loop()

    try:
        response = await loop.run_in_executor(
            executor,
            lambda: model.generate_content(full_prompt)
        )
        reply = response.text.strip()
        reply = reply.replace("*", "").replace("#", "").replace("`", "")
        return reply
    except Exception as exc:
        logger.error(f"Gemini error: {exc}")
        return "I am having a little trouble right now. Could you repeat that?"


def _respond_with_voice(
    text:          str,
    gather_action: str,
    call_sid:      str,
    ngrok_url:     str = "",
) -> str:
    # Try ElevenLabs first
    if settings.ELEVENLABS_API_KEY and ngrok_url:
        audio_url = _generate_elevenlabs_audio(text, call_sid, ngrok_url)
        if audio_url:
            return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{audio_url}</Play>
    <Gather input="speech"
            action="{gather_action}"
            method="POST"
            speechTimeout="2"
            speechModel="phone_call"
            enhanced="true"
            language="en-US">
    </Gather>
    <Redirect method="POST">{gather_action}</Redirect>
</Response>"""

    # Fallback to Twilio Polly Neural
    safe_text = (
        text.replace("&", "and")
            .replace("<", "")
            .replace(">", "")
            .replace('"', "")
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="speech"
            action="{gather_action}"
            method="POST"
            speechTimeout="2"
            speechModel="phone_call"
            enhanced="true"
            language="en-US">
        <Say voice="Polly.Joanna-Neural" rate="95%">{safe_text}</Say>
    </Gather>
    <Redirect method="POST">{gather_action}</Redirect>
</Response>"""


def _end_call(farewell_text: str) -> str:
    safe_text = (
        farewell_text.replace("&", "and")
                     .replace("<", "")
                     .replace(">", "")
                     .replace('"', "")
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna-Neural" rate="95%">{safe_text}</Say>
    <Hangup/>
</Response>"""


def _generate_elevenlabs_audio(
    text:      str,
    call_sid:  str,
    ngrok_url: str,
) -> str | None:
    try:
        from elevenlabs.client import ElevenLabs

        client   = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
        voice_id = settings.ELEVENLABS_VOICE_ID or "cjVigY5qzO86Huf0OWal"

        audio    = client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id="eleven_flash_v2_5",
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
    
@router.get("/voice/status/{call_sid}")
async def voice_status(call_sid: str):
    """Returns the current status of an active call."""
    history = conversations.get(call_sid, [])
    return {
        "call_sid":    call_sid,
        "active":      call_sid in conversations,
        "turns":       len(history),
        "transcript":  history,
    }


@router.get("/voice/active")
async def active_calls():
    """Returns all currently active calls."""
    return {
        "active_calls": [
            {
                "call_sid": sid,
                "turns":    len(history),
                "last_message": history[-1]["content"] if history else "",
            }
            for sid, history in conversations.items()
        ]
    }