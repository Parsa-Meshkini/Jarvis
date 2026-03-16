import logging
from app.tools.calendar_tool import check_calendar, add_to_calendar
from app.tools.search_tool   import search_salons, call_salon, confirm_booking
from app.tools.calling       import call_business

logger = logging.getLogger(__name__)

TOOL_MAP = {
    # Generic search — works for anything
    "search_places":   search_salons,
    "search_salons":   search_salons,

    "call_salon":      call_salon,
    "call_business":   call_business,
    "confirm_booking": confirm_booking,
    "check_calendar":  check_calendar,
    "add_to_calendar": add_to_calendar,
}


async def execute_plan(plan: dict) -> dict:
    steps   = plan.get("steps", [])
    results = []
    context = {}

    for i, step in enumerate(steps):
        tool_name = step.get("tool")
        params    = step.get("params", {})
        reason    = step.get("reason", "")

        logger.info(f"Step {i+1}/{len(steps)}: {tool_name}")

        merged_params = {**context, **params}
        tool = TOOL_MAP.get(tool_name)

        if not tool:
            results.append({
                "step":   i + 1,
                "tool":   tool_name,
                "status": "failed",
                "reason": f"Tool '{tool_name}' not found",
            })
            logger.warning(f"Unknown tool: {tool_name}")
            continue

        try:
            output = await tool(merged_params)
            results.append({
                "step":   i + 1,
                "tool":   tool_name,
                "reason": reason,
                "status": "completed",
                "output": output,
            })
            if isinstance(output, dict):
                if output.get("top_pick"):
                    context["name"]       = output["top_pick"].get("name")
                    context["salon_name"] = output["top_pick"].get("name")
                if output.get("date"):
                    context["date"] = output["date"]
                if output.get("time"):
                    context["time"] = output["time"]
                context.update({k: v for k, v in output.items() if v})

        except Exception as exc:
            results.append({
                "step":   i + 1,
                "tool":   tool_name,
                "status": "failed",
                "error":  str(exc),
            })
            logger.error(f"Tool {tool_name} failed: {exc}")

    return {
        "goal":    plan.get("goal", "unknown"),
        "total":   len(steps),
        "results": results,
        "status":  "completed" if all(
            r["status"] == "completed" for r in results
        ) else "partial",
    }