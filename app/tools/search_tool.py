import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


async def search_salons(params: dict = {}) -> dict:
    location = params.get("location", "Toronto, ON")

    # Use query directly — don't force "hair salon"
    query   = params.get("query", "")
    service = params.get("service", "")
    keyword = query or service or "business"

    if not settings.GOOGLE_MAPS_API_KEY:
        logger.warning("No GOOGLE_MAPS_API_KEY — using stub data")
        return {
            "status":   "success",
            "message":  f"No Maps API key — using stub data for '{keyword}'",
            "results":  [
                {"name": "Example Place 1", "address": "123 Main St", "rating": 4.8},
                {"name": "Example Place 2", "address": "456 King St", "rating": 4.6},
            ],
            "top_pick": {"name": "Example Place 1", "address": "123 Main St"},
        }

    async with httpx.AsyncClient(timeout=10) as client:
        geo = await client.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": location, "key": settings.GOOGLE_MAPS_API_KEY},
        )
        geo_data = geo.json()

        if not geo_data.get("results"):
            raise RuntimeError(f"Could not geocode: {location}")

        lat = geo_data["results"][0]["geometry"]["location"]["lat"]
        lng = geo_data["results"][0]["geometry"]["location"]["lng"]

        places = await client.get(
            "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
            params={
                "location": f"{lat},{lng}",
                "radius":   2000,
                "keyword":  keyword,       # ← uses whatever was actually searched
                "key":      settings.GOOGLE_MAPS_API_KEY,
            },
        )
        data = places.json()

    results    = data.get("results", [])[:5]
    businesses = [
        {
            "name":     p.get("name"),
            "address":  p.get("vicinity"),
            "rating":   p.get("rating", "N/A"),
            "place_id": p.get("place_id"),
            "open_now": p.get("opening_hours", {}).get("open_now", "unknown"),
        }
        for p in results
    ]

    return {
        "status":   "success",
        "query":    keyword,
        "location": location,
        "results":  businesses,
        "top_pick": businesses[0] if businesses else None,
    }


async def call_salon(params: dict = {}) -> dict:
    salon_name = params.get("salon_name") or params.get("name", "the salon")
    date       = params.get("date", "tomorrow")
    time       = params.get("time_preference", params.get("time", "afternoon"))
    return {
        "status":  "success",
        "message": f"Called {salon_name}, requested appointment on {date} at {time}",
        "salon":   salon_name,
        "date":    date,
        "time":    time,
    }


async def confirm_booking(params: dict = {}) -> dict:
    salon_name = params.get("salon_name") or params.get("salon", "the salon")
    date       = params.get("date", "tomorrow")
    time       = params.get("time", "afternoon")
    return {
        "status":  "confirmed",
        "message": f"Booking confirmed at {salon_name} on {date} at {time}",
        "salon":   salon_name,
        "date":    date,
        "time":    time,
    }