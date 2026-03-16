import json
from app.services.llm_service import generate_plan
from app.agents.prompts import SYSTEM_PROMPT


async def plan_task(user_input: str) -> dict:
    """
    Uses LLM to create an execution plan from a natural language request.
    """
    plan = await generate_plan(
        user_input=user_input,       # fixed — was swapped before
        system_prompt=SYSTEM_PROMPT
    )

    # Ensure the response has the shape we expect
    if "steps" not in plan:
        return {
            "goal": "unknown",
            "steps": [],
            "raw_output": plan
        }

    return plan