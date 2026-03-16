import uuid

from arq.connections import ArqRedis, RedisSettings, create_pool
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.models.task import Task, TaskStatus

router = APIRouter()


class CreateTaskRequest(BaseModel):
    user_request: str


class StepResponse(BaseModel):
    name:   str
    status: str
    output: str | None


class TaskResponse(BaseModel):
    task_id:      str
    status:       str
    user_request: str
    message:      str = "Task queued. Poll /api/tasks/{task_id} for updates."


class TaskDetailResponse(BaseModel):
    task_id:      str
    status:       str
    user_request: str
    result:       str | None
    steps:        list[StepResponse]


async def _get_arq() -> ArqRedis:
    url        = settings.redis_url.replace("redis://", "")
    host, port = url.split(":")
    return await create_pool(RedisSettings(host=host, port=int(port)))


def _to_detail(task: Task) -> TaskDetailResponse:
    return TaskDetailResponse(
        task_id=str(task.id),
        status=task.status,
        user_request=task.user_request,
        result=task.result,
        steps=[
            StepResponse(name=s.step_name, status=s.status, output=s.output)
            for s in task.steps
        ],
    )


@router.post("/", response_model=TaskResponse, status_code=202)
async def create_task(
    body: CreateTaskRequest,
    db: AsyncSession = Depends(get_db),
):
    task = Task(user_request=body.user_request, status=TaskStatus.QUEUED)
    db.add(task)
    await db.commit()
    await db.refresh(task)

    redis = await _get_arq()
    await redis.enqueue_job("run_agent_task", str(task.id))
    await redis.aclose()

    return TaskResponse(
        task_id=str(task.id),
        status=task.status,
        user_request=task.user_request,
    )


@router.get("/", response_model=list[TaskDetailResponse])
async def list_tasks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Task)
        .options(selectinload(Task.steps))
        .order_by(Task.created_at.desc())
        .limit(20)
    )
    return [_to_detail(t) for t in result.scalars().all()]


@router.get("/{task_id}", response_model=TaskDetailResponse)
async def get_task(task_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Task).options(selectinload(Task.steps)).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return _to_detail(task)