import json
from app.services.llm_service import generate_plan
from app.agents.prompts import SYSTEM_PROMPT


async def plan_task(user_input: str):
    """
    Uses LLM to create execution plan.
    """

    raw_response = await generate_plan(
        user_input,
        SYSTEM_PROMPT
    )

    try:
        plan = json.loads(raw_response)
        return plan
    except Exception:
        return {
            "goal": "error",
            "steps": [],
            "raw_output": raw_response
        }