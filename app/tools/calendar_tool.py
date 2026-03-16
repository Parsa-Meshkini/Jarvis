import asyncio
import json
import logging
from datetime import datetime, timedelta
from app.core.config import settings

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _get_service():
    """Build an authenticated Google Calendar client."""
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    creds_dict = json.loads(settings.GOOGLE_CALENDAR_CREDENTIALS)
    creds = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=SCOPES
    )
    return build("calendar", "v3", credentials=creds)


def _is_configured() -> bool:
    return bool(
        settings.GOOGLE_CALENDAR_CREDENTIALS and
        settings.GOOGLE_CALENDAR_ID and
        settings.GOOGLE_CALENDAR_CREDENTIALS != ""
    )


async def check_calendar(params: dict = {}) -> dict:
    """Check real Google Calendar for availability."""
    date_str   = params.get("date", "tomorrow")
    time_range = params.get("time_range", params.get("time_preference", "afternoon"))

    if not _is_configured():
        return {
            "status":    "success",
            "available": True,
            "message":   f"[Stub] Calendar checked: free on {date_str} {time_range}",
            "note":      "Add GOOGLE_CALENDAR_CREDENTIALS to .env for real calendar",
        }

    try:
        # Parse natural date strings
        if date_str.lower() == "tomorrow":
            date = datetime.now() + timedelta(days=1)
        elif date_str.lower() == "today":
            date = datetime.now()
        else:
            date = datetime.strptime(date_str, "%Y-%m-%d")

        time_min = date.replace(hour=0, minute=0, second=0).isoformat() + "Z"
        time_max = date.replace(hour=23, minute=59, second=59).isoformat() + "Z"

        loop   = asyncio.get_event_loop()
        events = await loop.run_in_executor(
            None, _fetch_events, time_min, time_max
        )

        busy = [
            {
                "title": e.get("summary", "Busy"),
                "start": e["start"].get("dateTime", e["start"].get("date")),
                "end":   e["end"].get("dateTime",   e["end"].get("date")),
            }
            for e in events
        ]

        return {
            "status":     "success",
            "date":       date_str,
            "time_range": time_range,
            "available":  len(busy) == 0,
            "busy_slots": busy,
            "message":    f"{'Free' if len(busy) == 0 else f'{len(busy)} events'} on {date_str}",
        }

    except Exception as exc:
        logger.error(f"Calendar check failed: {exc}")
        return {"status": "error", "message": str(exc), "available": True}


def _fetch_events(time_min: str, time_max: str) -> list:
    service = _get_service()
    result  = (
        service.events()
        .list(
            calendarId=settings.GOOGLE_CALENDAR_ID,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    return result.get("items", [])


async def add_to_calendar(params: dict = {}) -> dict:
    """Add a real event to Google Calendar."""
    title = params.get("title") or params.get("event_details", "Appointment")
    date  = params.get("date", "tomorrow")
    time  = params.get("time", params.get("time_preference", "14:00"))
    name  = params.get("name") or params.get("salon_name", "")

    if name and name not in title:
        title = f"{title} at {name}"

    if not _is_configured():
        return {
            "status":  "success",
            "message": f"[Stub] '{title}' added to calendar on {date} at {time}",
            "note":    "Add GOOGLE_CALENDAR_CREDENTIALS to .env for real calendar",
        }

    try:
        # Parse date
        if date.lower() == "tomorrow":
            event_date = datetime.now() + timedelta(days=1)
        elif date.lower() == "today":
            event_date = datetime.now()
        else:
            event_date = datetime.strptime(date, "%Y-%m-%d")

        # Parse time
        try:
            if ":" in str(time):
                hour, minute = str(time).split(":")
                event_date = event_date.replace(hour=int(hour), minute=int(minute), second=0)
            elif time in ("morning", "am"):
                event_date = event_date.replace(hour=10, minute=0, second=0)
            elif time in ("afternoon", "pm"):
                event_date = event_date.replace(hour=14, minute=0, second=0)
            elif time == "evening":
                event_date = event_date.replace(hour=18, minute=0, second=0)
            else:
                event_date = event_date.replace(hour=14, minute=0, second=0)
        except Exception:
            event_date = event_date.replace(hour=14, minute=0, second=0)

        end_date = event_date + timedelta(hours=1)

        event_body = {
            "summary": title,
            "start":   {"dateTime": event_date.isoformat(), "timeZone": "America/Toronto"},
            "end":     {"dateTime": end_date.isoformat(),   "timeZone": "America/Toronto"},
            "description": "Booked by Jarvis AI assistant",
        }

        loop    = asyncio.get_event_loop()
        created = await loop.run_in_executor(None, _create_event, event_body)

        return {
            "status":   "created",
            "event_id": created.get("id"),
            "title":    title,
            "start":    event_date.isoformat(),
            "link":     created.get("htmlLink"),
            "message":  f"'{title}' added to your Google Calendar",
        }

    except Exception as exc:
        logger.error(f"Calendar create failed: {exc}")
        return {"status": "error", "message": str(exc)}


def _create_event(event_body: dict) -> dict:
    service = _get_service()
    return (
        service.events()
        .insert(calendarId=settings.GOOGLE_CALENDAR_ID, body=event_body)
        .execute()
    )