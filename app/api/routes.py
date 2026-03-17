import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from arq.connections import ArqRedis, RedisSettings, create_pool

from app.agents.planner import plan_task
from app.agents.executor import execute_plan
from app.database import get_db
from app.models.task import Task, TaskStep, TaskStatus
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


class CommandRequest(BaseModel):
    user_input: str


async def _get_arq() -> ArqRedis:
    url        = settings.REDIS_URL.replace("redis://", "")
    host, port = url.split(":")
    return await create_pool(RedisSettings(host=host, port=int(port)))


@router.post("/command")
async def command(
    body: CommandRequest,
    db: AsyncSession = Depends(get_db),
):
    task = Task(user_request=body.user_input, status=TaskStatus.QUEUED)
    db.add(task)
    await db.commit()
    await db.refresh(task)

    try:
        redis = await _get_arq()
        await redis.enqueue_job("run_agent_task", str(task.id), body.user_input)
        await redis.aclose()
        return {
            "task_id": str(task.id),
            "status":  "queued",
            "message": "Task queued. Poll /tasks/{task_id} for updates.",
            "request": body.user_input,
        }
    except Exception:
        logger.warning("Redis unavailable — running task synchronously")
        try:
            task.status = TaskStatus.PLANNING
            await db.commit()

            plan = await plan_task(body.user_input)

            # Check if LLM returned an error plan
            if plan.get("goal") in ("rate_limit_error", "llm_error", "parse_error"):
                task.status = TaskStatus.FAILED
                task.result = plan.get("error", "LLM error")
                await db.commit()
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=429 if plan.get("goal") == "rate_limit_error" else 500,
                    detail=plan.get("error", "LLM error — try again in a moment")
                )

            task.status = TaskStatus.EXECUTING
            await db.commit()

            execution   = await execute_plan(plan)
            task.status = TaskStatus.COMPLETED
            task.result = execution.get("status", "completed")
            await db.commit()

            return {
                "task_id":   str(task.id),
                "request":   body.user_input,
                "plan":      plan,
                "execution": execution,
            }

        except Exception as exc:
            task.status = TaskStatus.FAILED
            task.result = str(exc)
            await db.commit()
            raise

@router.get("/tasks")
async def list_tasks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Task)
        .options(selectinload(Task.steps))
        .order_by(Task.created_at.desc())
        .limit(20)
    )
    tasks = result.scalars().all()
    return [
        {
            "task_id":    str(t.id),
            "request":    t.user_request,
            "status":     t.status,
            "result":     t.result,
            "created_at": t.created_at.isoformat(),
            "steps": [
                {"name": s.step_name, "status": s.status, "output": s.output}
                for s in t.steps
            ],
        }
        for t in tasks
    ]


@router.get("/tasks/{task_id}")
async def get_task(task_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Task)
        .options(selectinload(Task.steps))
        .where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "task_id":    str(task.id),
        "request":    task.user_request,
        "status":     task.status,
        "result":     task.result,
        "created_at": task.created_at.isoformat(),
        "steps": [
            {"name": s.step_name, "status": s.status, "output": s.output}
            for s in task.steps
        ],
    }

# ── Memory routes ─────────────────────────────────────────────────────────────

class MemoryRequest(BaseModel):
    key:   str
    value: str


@router.get("/memory")
async def get_memory():
    """Get all stored user preferences."""
    from app.agents.memory import get_all_preferences
    prefs = await get_all_preferences()
    return {"preferences": prefs}


@router.post("/memory")
async def set_memory(body: MemoryRequest):
    """Save a user preference."""
    from app.agents.memory import save_preference
    await save_preference(key=body.key, value=body.value)
    return {"status": "saved", "key": body.key, "value": body.value}


@router.delete("/memory/{key}")
async def delete_memory(key: str):
    """Delete a user preference."""
    from app.agents.memory import delete_preference
    await delete_preference(key=key)
    return {"status": "deleted", "key": key}

class CallTestRequest(BaseModel):
    business_name:  str
    phone_number:   str
    service:        str = "haircut"
    date:           str = "tomorrow"
    preferred_time: str = "afternoon"


@router.post("/test-call")
async def test_call(body: CallTestRequest):
    """
    Directly triggers a real phone call to a business.
    Use this to test voice calling without running the full agent.
    """
    from app.tools.calling import call_business

    result = await call_business({
        "name":            body.business_name,
        "phone_number":    body.phone_number,
        "service":         body.service,
        "date":            body.date,
        "time_preference": body.preferred_time,
    })

    return result