from app.tools.calendar import check_calendar, add_to_calendar
from app.tools.search import search_salons, call_salon, confirm_booking


TOOL_MAP = {
    "check_calendar": check_calendar,
    "search_salons": search_salons,
    "call_salon": call_salon,
    "confirm_booking": confirm_booking,
    "add_to_calendar": add_to_calendar,
}


async def execute_plan(plan: dict):
    results = []

    for step in plan.get("steps", []):
        tool_name = step["tool"]

        tool = TOOL_MAP.get(tool_name)

        if not tool:
            results.append({
                "tool": tool_name,
                "status": "failed",
                "reason": "tool not found"
            })
            continue

        result = await tool()

        results.append({
            "tool": tool_name,
            "result": result
        })

    return results