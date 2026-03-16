import logging
import uuid
from arq.connections import RedisSettings
from app.core.config import settings

logger = logging.getLogger(__name__)


def _redis_settings() -> RedisSettings:
    url        = settings.REDIS_URL.replace("redis://", "")
    host, port = url.split(":")
    return RedisSettings(host=host, port=int(port))


async def run_agent_task(ctx: dict, task_id: str, user_input: str) -> str:
    """
    ARQ job function.
    Called by the worker when a job is dequeued from Redis.
    """
    from app.database import AsyncSessionLocal
    from app.models.task import Task, TaskStatus
    from app.agents.planner import plan_task
    from app.agents.executor import execute_plan
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    logger.info(f"[Worker] Processing task: {task_id}")

    async with AsyncSessionLocal() as db:
        # Fetch task
        result = await db.execute(
            select(Task).where(Task.id == uuid.UUID(task_id))
        )
        task = result.scalar_one_or_none()
        if not task:
            logger.error(f"[Worker] Task {task_id} not found")
            return "not_found"

        try:
            # Update status to planning
            task.status = TaskStatus.PLANNING
            await db.commit()

            # Generate plan
            plan = await plan_task(user_input)

            # Update to executing
            task.status = TaskStatus.EXECUTING
            await db.commit()

            # Execute plan
            execution = await execute_plan(plan)

            # Save result
            task.status = TaskStatus.COMPLETED
            task.result = execution.get("status", "completed")
            await db.commit()

            logger.info(f"[Worker] Task {task_id} completed")
            return "completed"

        except Exception as exc:
            task.status = TaskStatus.FAILED
            task.result = str(exc)
            await db.commit()
            logger.error(f"[Worker] Task {task_id} failed: {exc}")
            raise


class WorkerSettings:
    """ARQ reads this class to configure the worker."""
    functions      = [run_agent_task]
    redis_settings = _redis_settings()
    max_jobs       = 10
    job_timeout    = 300