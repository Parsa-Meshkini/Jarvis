async def search_salons(params: dict = {}) -> dict:
    location = params.get("location", "nearby")
    query    = params.get("query", "hair salon")
    return {
        "status": "success",
        "message": f"Found 3 {query}s in {location}",
        "results": [
            {"name": "Style Studio",   "address": "123 Main St", "rating": 4.8},
            {"name": "The Hair Lounge","address": "456 King St", "rating": 4.6},
            {"name": "Cuts & Co",      "address": "789 Queen St","rating": 4.5},
        ]
    }


async def call_salon(params: dict = {}) -> dict:
    salon_name = params.get("salon_name", "the salon")
    date       = params.get("date", "tomorrow")
    time       = params.get("time", "afternoon")
    return {
        "status": "success",
        "message": f"Called {salon_name}, requested appointment on {date} at {time}"
    }


async def confirm_booking(params: dict = {}) -> dict:
    salon_name = params.get("salon_name", "the salon")
    date       = params.get("date", "tomorrow")
    time       = params.get("time", "afternoon")
    return {
        "status": "confirmed",
        "message": f"Booking confirmed at {salon_name} on {date} at {time}"
    }