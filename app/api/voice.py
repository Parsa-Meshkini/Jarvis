import asyncio
import logging
import os
import json
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import Response
from app.core.config import settings
from app.services.auth_service import get_current_user
import httpx
import redis as redis_sync
from typing import Any
import re
from datetime import datetime, timezone

logger        = logging.getLogger(__name__)
router        = APIRouter()
conversations: dict[str, list] = {}
_ngrok_url:   str = ""

_PLACEHOLDER_NAMES = {
    "my client",
    "client",
    "the client",
    "unknown",
    "n/a",
    "na",
}


def _is_placeholder_name(name: str) -> bool:
    n = (name or "").strip().lower()
    return (not n) or (n in _PLACEHOLDER_NAMES)


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


def _sync_booking_transcript(call_sid: str, history: list) -> None:
    """Keep outbound booking_calls in sync for the dashboard."""
    try:
        from app.tools.calling import booking_calls

        if call_sid in booking_calls:
            booking_calls[call_sid]["transcript"] = [
                {"role": m["role"], "content": m["content"]} for m in history
            ]
    except Exception as exc:
        logger.debug(f"Booking transcript sync skipped: {exc}")


def _save_history(call_sid: str, history: list) -> None:
    r = _get_redis_client()
    if r:
        try:
            r.setex(f"voice:{call_sid}", 3600, json.dumps(history))
            logger.info(f"[Memory] Saved {len(history)} turns for {call_sid}")
            conversations[call_sid] = history
            _sync_booking_transcript(call_sid, history)
            return
        except Exception as exc:
            logger.error(f"[Memory] Save failed: {exc}")
    conversations[call_sid] = history
    _sync_booking_transcript(call_sid, history)
    # Persist summary meta for cross-process dashboard visibility.
    last = history[-1]["content"] if history else ""
    _set_meta(call_sid, {"turns": len(history), "last_message": last})


# ── Redis call state (slot filling) ───────────────────────────────────────────

def _get_state(call_sid: str) -> dict[str, Any]:
    """
    Per-call slot state to keep the voice agent stable.
    Stored in Redis when available; falls back to in-memory.
    """
    r = _get_redis_client()
    if r:
        try:
            data = r.get(f"voice_state:{call_sid}")
            if data:
                return json.loads(data)
        except Exception as exc:
            logger.error(f"[State] Load failed: {exc}")
    return conversations.get(f"{call_sid}:state", {}) or {}


def _save_state(call_sid: str, state: dict[str, Any]) -> None:
    r = _get_redis_client()
    if r:
        try:
            r.setex(f"voice_state:{call_sid}", 3600, json.dumps(state))
            conversations[f"{call_sid}:state"] = state
            return
        except Exception as exc:
            logger.error(f"[State] Save failed: {exc}")
    conversations[f"{call_sid}:state"] = state


def _merge_state(old: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    out = dict(old or {})
    for k, v in (patch or {}).items():
        if v is None:
            continue
        if isinstance(v, str) and not v.strip():
            continue
        out[k] = v
    return out


def _get_owner(call_sid: str) -> str:
    r = _get_redis_client()
    if r:
        try:
            return r.get(f"voice_owner:{call_sid}") or ""
        except Exception:
            return ""
    return ""


def _set_owner(call_sid: str, user_id: str) -> None:
    if not user_id:
        return
    r = _get_redis_client()
    if r:
        try:
            r.setex(f"voice_owner:{call_sid}", 3600, user_id)
        except Exception:
            pass


def _get_meta(call_sid: str) -> dict[str, Any]:
    r = _get_redis_client()
    if r:
        try:
            data = r.get(f"voice_meta:{call_sid}")
            return json.loads(data) if data else {}
        except Exception:
            return {}
    return {}


def _set_meta(call_sid: str, patch: dict[str, Any]) -> None:
    r = _get_redis_client()
    if not r:
        return
    try:
        meta = _get_meta(call_sid)
        meta.update({k: v for k, v in (patch or {}).items() if v is not None})
        meta["updated_at"] = datetime.now(timezone.utc).isoformat()
        r.setex(f"voice_meta:{call_sid}", 3600, json.dumps(meta))
    except Exception:
        pass


# ── OpenAI brain ───────────────────────────────────────────────────────────────

async def _get_jarvis_reply(user_input: str, history: list, call_sid: str) -> str:
    from openai import AsyncOpenAI
    from app.agents.memory import build_user_context

    client  = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    context = await build_user_context()

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


async def _extract_booking_signal(
    business_utterance: str,
    history: list,
    call_sid: str,
    state: dict[str, Any],
) -> dict[str, Any]:
    """
    JSON-only classifier/extractor to reduce hallucinations.
    It decides what the business is asking for, and extracts any concrete details.
    """
    from openai import AsyncOpenAI
    from app.agents.memory import build_user_context

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    system = """You are a JSON-only extractor for a phone booking assistant.
Return ONLY valid JSON (no markdown, no extra text).

Decide what the other person (the business) is asking for, and extract details.

Output schema:
{
  "asked_for": "client_name" | "phone" | "client_details" | "service" | "date" | "time" | "confirm" | "availability" | "other",
  "update_state": {
    "client_name": string|null,
    "service": string|null,
    "date": string|null,
    "time": string|null,
    "phone": string|null,
    "business_offered_times": string|null
  },
  "confidence": number
}

Rules:
- If the business asks \"name\" / \"who is it for\" => asked_for=client_name.
- If the business asks for BOTH name and phone/number/contact => asked_for=client_details.
- If the business offers times (e.g. \"we have 2pm or 3pm\") => asked_for=availability and put it in business_offered_times.
- If unclear => asked_for=other.
"""

    try:
        user_ctx = await build_user_context(user_id=state.get("user_id", "default"))
        context = {
            "known_state": {
                "client_name": state.get("client_name") or user_ctx.get("name") or "",
                "service": state.get("service") or "",
                "date": state.get("date") or "",
                "time": state.get("time") or state.get("preferred_time") or user_ctx.get("preferred_time") or "",
                "phone": state.get("phone") or user_ctx.get("phone") or "",
            },
            "last_business_utterance": business_utterance,
        }
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(context)},
            ],
            max_tokens=200,
            temperature=0.0,
        )
        raw = (resp.choices[0].message.content or "").strip()
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("Extractor did not return a JSON object")
        return data
    except Exception as exc:
        logger.error(f"[{call_sid}] Extractor error: {exc}")
        return {"asked_for": "other", "update_state": {}, "confidence": 0.0}


def _safe_business_response(signal: dict[str, Any], state: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """
    Deterministic, non-hallucinating responses for common booking questions.
    Keeps the conversation stable even with weird inputs.
    """
    asked_for = (signal or {}).get("asked_for") or "other"
    upd = (signal or {}).get("update_state") or {}
    state = _merge_state(state, upd)
    patch: dict[str, Any] = {}

    client_name = state.get("client_name") or ""
    service = state.get("service") or ""
    date = state.get("date") or ""
    time_pref = state.get("time") or state.get("preferred_time") or ""
    phone = state.get("phone") or ""
    booked_time = state.get("booked_time") or ""

    if asked_for == "client_name":
        if client_name and not _is_placeholder_name(client_name):
            return f"It is for {client_name}.", patch
        # Never invent.
        return "Sure — what name should I book it under?", patch

    if asked_for == "service":
        if service:
            return f"It is for a {service} appointment.", patch
        return "It is for a standard haircut appointment.", patch

    if asked_for in ("date", "time"):
        if date and time_pref:
            return f"For {date}, preferably in the {time_pref}. Do you have availability then?", patch
        if date:
            return f"For {date}. What times do you have available?", patch
        return "For tomorrow afternoon if possible. What times do you have available?", patch

    if asked_for == "availability":
        offered = state.get("business_offered_times") or upd.get("business_offered_times") or ""
        # Simple rule: pick the first offered slot (if we can see one) and remember it.
        if offered:
            m = re.search(r"\\b(\\d{1,2})(?::(\\d{2}))?\\s*(am|pm)\\b", offered, re.IGNORECASE)
            if m:
                t = f"{m.group(1)}{(':' + m.group(2)) if m.group(2) else ''}{m.group(3).lower()}"
                patch["booked_time"] = t
                patch["time"] = t
                return f"Great — {t} works. Please book it for {client_name or 'my client'}.", patch
            return f"Great — the first one works. Please book it for {client_name or 'my client'}.", patch
        return "Great — what is your earliest available time?", patch

    if asked_for == "phone":
        # Prefer explicit phone in memory/state; otherwise avoid making one up.
        if phone:
            return f"Yes — the phone number is {phone}.", patch
        return "I can provide the phone number shortly. Could we finalize the time first?", patch

    if asked_for == "client_details":
        has_name = client_name and not _is_placeholder_name(client_name)
        has_phone = bool(phone)
        if has_name and has_phone:
            return f"It is for {client_name}. The phone number is {phone}.", patch
        if has_name and not has_phone:
            return f"It is for {client_name}. I can provide the phone number shortly — could we confirm the time first?", patch
        if (not has_name) and has_phone:
            return f"The phone number is {phone}. What name should I book it under?", patch
        return "Sure — what name should I book it under, and what is the best number to put on the booking?", patch

    if asked_for == "confirm":
        patch["booking_stage"] = "confirmed"
        return "Yes, that works. Please confirm the appointment details and we are all set.", patch

    # Fallback: keep it short and ask a specific booking question.
    if booked_time:
        return "Thanks. Could you please confirm the appointment details?", patch
    if date and time_pref:
        return f"Thanks. Do you have availability on {date} in the {time_pref}?", patch
    return "Thanks. What is your earliest availability for tomorrow afternoon?", patch


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
    history   = [{"role": "assistant", "content": greeting}]
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

    conversations.pop(f"{CallSid}_empty", None)
    history = _get_history(CallSid)
    logger.info(f"[{CallSid}] History has {len(history)} previous turns")
    history.append({"role": "user", "content": SpeechResult})

    # Load and update call slot state (stabilizes responses).
    state = _get_state(CallSid)
    uid = request.query_params.get("uid") if hasattr(request, "query_params") else None
    if uid and not state.get("user_id"):
        state = _merge_state(state, {"user_id": uid})
    if not state.get("user_id"):
        owner = _get_owner(CallSid)
        if owner:
            state = _merge_state(state, {"user_id": owner})

    # Hydrate missing/placeholder slots from user memory (prevents loops like "my client").
    try:
        from app.agents.memory import build_user_context
        if state.get("user_id"):
            user_ctx = await build_user_context(user_id=str(state.get("user_id")))
            mem_name = (user_ctx.get("name") or "").strip()
            mem_phone = (user_ctx.get("phone") or "").strip()
            patch = {}
            if mem_name and _is_placeholder_name(state.get("client_name", "")):
                patch["client_name"] = mem_name
            if mem_phone and not (state.get("phone") or "").strip():
                patch["phone"] = mem_phone
            if (user_ctx.get("preferred_time") or "").strip() and not (state.get("preferred_time") or "").strip():
                patch["preferred_time"] = user_ctx.get("preferred_time")
            if patch:
                state = _merge_state(state, patch)
    except Exception:
        pass

    # If this is an outbound call, inherit known details from booking_calls.
    try:
        from app.tools.calling import booking_calls
        ctx = booking_calls.get(CallSid, {})
        if ctx:
            state = _merge_state(state, {
                "user_id": state.get("user_id") or ctx.get("user_id"),
                "client_name": state.get("client_name") or ctx.get("client_name"),
                "service": state.get("service") or ctx.get("service"),
                "date": state.get("date") or ctx.get("date"),
                "time": state.get("time") or ctx.get("time"),
            })
    except Exception:
        pass

    signal = await _extract_booking_signal(
        business_utterance=SpeechResult,
        history=history,
        call_sid=CallSid,
        state=state,
    )
    reply, patch = _safe_business_response(signal, state)

    # Persist state updates.
    state = _merge_state(state, (signal or {}).get("update_state") or {})
    state = _merge_state(state, patch)
    if state.get("user_id"):
        _set_owner(CallSid, str(state.get("user_id")))
        _set_meta(CallSid, {"status": "calling"})
    _save_state(CallSid, state)

    history.append({"role": "assistant", "content": reply})
    _save_history(CallSid, history)

    end_phrases = ["goodbye", "bye", "hang up", "that's all", "thanks bye", "thank you goodbye"]
    if any(p in SpeechResult.lower() for p in end_phrases):
        _set_meta(CallSid, {"status": "completed"})
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
async def voice_status(call_sid: str, user: dict = Depends(get_current_user)):
    from app.tools.calling import booking_calls

    user_id = str(user.get("sub"))
    ctx = booking_calls.get(call_sid, {})
    owner = str(ctx.get("user_id") or _get_owner(call_sid) or "")
    if owner != user_id:
        return {"call_sid": call_sid, "active": False, "turns": 0, "transcript": []}

    history = _get_history(call_sid)
    transcript = history if history else ctx.get("transcript", [])
    meta = _get_meta(call_sid)
    return {
        "call_sid":    call_sid,
        "active":      ctx.get("status") == "calling" if ctx else True,
        "turns":       len(transcript),
        "transcript":  transcript,
        "type":        "outbound",
        "business":    ctx.get("business_name", "") or meta.get("business_name", ""),
        "booked_time": ctx.get("booked_time", ""),
        "status":      ctx.get("status", "unknown") if ctx else meta.get("status", "unknown"),
    }


def _collect_active_voice_calls(user_id: str) -> list[dict]:
    """
    Merge outbound booking state, Redis-backed transcripts, and in-memory fallback.
    Historically only `conversations` was read, but transcripts live in Redis when
    Redis is enabled — so the dashboard saw zero active calls.
    """
    from app.tools.calling import booking_calls

    by_sid: dict[str, dict] = {}

    # Outbound: only current user's calls (from in-process ctx)
    for sid, ctx in booking_calls.items():
        if str(ctx.get("user_id") or "") != user_id:
            continue
        hist = _get_history(sid)
        transcript = hist if hist else ctx.get("transcript", [])
        business = ctx.get("business_name", "")
        by_sid[sid] = {
            "call_sid":     sid,
            "turns":        len(transcript),
            "last_message": transcript[-1]["content"] if transcript else f"Outbound → {business or 'business'}",
            "type":         "outbound",
            "business":     business,
            "status":       ctx.get("status", "calling"),
        }

    # Outbound calls may have been initiated in another process (worker).
    # Use Redis ownership keys to discover them for this user.
    r = _get_redis_client()
    if r:
        try:
            for key in r.scan_iter(match="voice_owner:*"):
                sid = key.split("voice_owner:", 1)[-1]
                owner = r.get(key) or ""
                if owner != user_id:
                    continue
                if sid in by_sid:
                    continue
                hist = _get_history(sid)
                meta = _get_meta(sid)
                # Only show truly active calls here.
                if (meta.get("status") and meta.get("status") != "calling") and len(hist) > 0:
                    continue
                by_sid[sid] = {
                    "call_sid":     sid,
                    "turns":        len(hist),
                    "last_message": hist[-1]["content"] if hist else meta.get("status", "calling"),
                    "type":         "outbound",
                    "business":     meta.get("business_name", ""),
                    "status":       meta.get("status", "calling"),
                }
        except Exception:
            pass

    return list(by_sid.values())


@router.get("/voice/active")
async def active_calls(user: dict = Depends(get_current_user)):
    return {"active_calls": _collect_active_voice_calls(str(user.get("sub")))}