async def check_calendar(params: dict = {}) -> dict:
    date = params.get("date", "tomorrow")
    return {
        "status": "success",
        "available": True,
        "message": f"Calendar checked: free on {date} afternoon"
    }


async def add_to_calendar(params: dict = {}) -> dict:
    title = params.get("title", "Appointment")
    date  = params.get("date", "tomorrow")
    time  = params.get("time", "afternoon")
    return {
        "status": "success",
        "message": f"'{title}' added to calendar on {date} at {time}"
    }