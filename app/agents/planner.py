import json
from app.services.llm_service import generate_plan
from app.agents.prompts import SYSTEM_PROMPT
from app.agents.memory import build_user_context


async def plan_task(user_input: str) -> dict:
    """
    Uses LLM to create an execution plan.
    Enriches the request with user memory context.
    """
    # Load user preferences from DB
    context = await build_user_context()

    # Build context string for the prompt
    context_str = ""
    if any(context.values()):
        context_str = f"\n\nUSER CONTEXT (use this to personalise the plan):\n{json.dumps(context, indent=2)}"

    plan = await generate_plan(
        user_input=user_input + context_str,
        system_prompt=SYSTEM_PROMPT,
    )

    if "steps" not in plan:
        return {
            "goal":       "unknown",
            "steps":      [],
            "raw_output": plan,
        }

    return plan