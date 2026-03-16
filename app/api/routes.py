# app/api/routes.py
import uuid
import logging
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.planner import plan_task
from app.agents.executor import execute_plan
from app.database import get_db
from app.models.task import Task, TaskStep, TaskStatus

logger = logging.getLogger(__name__)
router = APIRouter()


class CommandRequest(BaseModel):
    user_input: str


@router.post("/command")
async def command(
    body: CommandRequest,
    db: AsyncSession = Depends(get_db),
):
    # 1. Create task record
    task = Task(
        user_request=body.user_input,
        status=TaskStatus.PLANNING,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    try:
        # 2. Generate plan
        plan = await plan_task(body.user_input)

        # 3. Save each step to DB
        task.status = TaskStatus.EXECUTING
        for step_data in plan.get("steps", []):
            step = TaskStep(
                task_id=task.id,
                step_name=step_data.get("tool", "unknown"),
                status="pending",
            )
            db.add(step)
        await db.commit()

        # 4. Execute the plan
        execution = await execute_plan(plan)

        # 5. Update step statuses in DB
        for i, result in enumerate(execution.get("results", [])):
            step_result = await db.execute(
                select(TaskStep)
                .where(TaskStep.task_id == task.id)
                .order_by(TaskStep.created_at)
                .offset(i)
                .limit(1)
            )
            step = step_result.scalar_one_or_none()
            if step:
                step.status = result.get("status", "unknown")
                step.output = str(result.get("output", ""))

        # 6. Mark task complete
        task.status  = TaskStatus.COMPLETED
        task.result  = execution.get("status", "completed")
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
        logger.error(f"Task failed: {exc}")
        raise


@router.get("/tasks")
async def list_tasks(db: AsyncSession = Depends(get_db)):
    """Get the last 20 tasks with their steps."""
    result = await db.execute(
        select(Task)
        .options(selectinload(Task.steps))
        .order_by(Task.created_at.desc())
        .limit(20)
    )
    tasks = result.scalars().all()

    return [
        {
            "task_id":     str(t.id),
            "request":     t.user_request,
            "status":      t.status,
            "created_at":  t.created_at.isoformat(),
            "steps": [
                {"name": s.step_name, "status": s.status, "output": s.output}
                for s in t.steps
            ],
        }
        for t in tasks
    ]


@router.get("/tasks/{task_id}")
async def get_task(task_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get a single task by ID."""
    result = await db.execute(
        select(Task)
        .options(selectinload(Task.steps))
        .where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        from fastapi import HTTPException
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