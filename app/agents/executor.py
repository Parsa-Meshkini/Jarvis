import logging
from app.tools.calendar import check_calendar, add_to_calendar
from app.tools.search import search_salons, call_salon, confirm_booking
from app.tools.calling import call_business

logger = logging.getLogger(__name__)

TOOL_MAP = {
    "check_calendar":  check_calendar,
    "search_salons":   search_salons,
    "call_salon":      call_salon,
    "call_business":   call_business,
    "confirm_booking": confirm_booking,
    "add_to_calendar": add_to_calendar,
}


async def execute_plan(plan: dict) -> dict:
    """
    Executes each step in the plan sequentially.
    Passes params from the plan into each tool.
    Returns a full execution report.
    """
    steps   = plan.get("steps", [])
    results = []
    context = {}   # carries outputs between steps (e.g. salon name → next step)

    for i, step in enumerate(steps):
        tool_name = step.get("tool")
        params    = step.get("params", {})
        reason    = step.get("reason", "")

        logger.info(f"Step {i+1}/{len(steps)}: {tool_name}")

        # Merge in any context from previous steps
        merged_params = {**context, **params}

        tool = TOOL_MAP.get(tool_name)

        if not tool:
            result = {
                "step":   i + 1,
                "tool":   tool_name,
                "status": "failed",
                "reason": f"Tool '{tool_name}' not found in registry",
            }
            results.append(result)
            logger.warning(f"Unknown tool: {tool_name}")
            continue

        try:
            output = await tool(merged_params)
            result = {
                "step":   i + 1,
                "tool":   tool_name,
                "reason": reason,
                "status": "completed",
                "output": output,
            }
            # Make output available to subsequent steps
            context.update(output if isinstance(output, dict) else {})

        except Exception as exc:
            result = {
                "step":   i + 1,
                "tool":   tool_name,
                "status": "failed",
                "error":  str(exc),
            }
            logger.error(f"Tool {tool_name} failed: {exc}")

        results.append(result)

    return {
        "goal":    plan.get("goal", "unknown"),
        "total":   len(steps),
        "results": results,
        "status":  "completed" if all(r["status"] == "completed" for r in results) else "partial",
    }