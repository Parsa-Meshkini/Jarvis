from fastapi import FastAPI
from app.api.routes import router
from app.core.config import settings
from app.agents.executor import execute_plan
from app.agents.planner import plan_task

app = FastAPI(title=settings.APP_NAME)

app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Jarvis Agent Running"}

@app.post("/command")
async def command(user_input: str):

    plan = await plan_task(user_input)

    execution_results = await execute_plan(plan)

    return {
        "plan": plan,
        "execution": execution_results
    }