from fastapi import APIRouter
from pydantic import BaseModel
from app.agents.planner import plan_task
from app.agents.executor import execute_plan

router = APIRouter()


class CommandRequest(BaseModel):
    user_input: str


@router.post("/command")
async def command(body: CommandRequest):
    """
    Main endpoint. Takes a natural language command,
    generates a plan, executes it, returns full results.
    """
    plan    = await plan_task(body.user_input)
    results = await execute_plan(plan)

    return {
        "request":   body.user_input,
        "plan":      plan,
        "execution": results,
    }