from fastapi import APIRouter
from app.agents.planner import plan_task

router = APIRouter()

@router.post("/command")
async def command(user_input: str):
    plan = await plan_task(user_input)
    return {"plan": plan}