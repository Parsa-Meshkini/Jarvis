import logging
import uuid

from arq.connections import RedisSettings

from app.config import settings
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


def _redis_settings() -> RedisSettings:
    url        = settings.redis_url.replace("redis://", "")
    host, port = url.split(":")
    return RedisSettings(host=host, port=int(port))


def build_tool_registry() -> dict:
    from app.tools.search_tool import SearchBusinessesTool
    from app.tools.calendar_tool import CheckCalendarTool, CreateCalendarEventTool

    tools = [
        SearchBusinessesTool(),
        CheckCalendarTool(),
        CreateCalendarEventTool(),
    ]
    return {tool.name: tool for tool in tools}


async def run_agent_task(ctx: dict, task_id: str) -> str:
    logger.info(f"[Worker] Picked up task: {task_id}")

    async with AsyncSessionLocal() as db:
        from app.models.task import Task
        task = await db.get(Task, uuid.UUID(task_id))

        if not task:
            logger.error(f"[Worker] Task {task_id} not found")
            return "not_found"

        from app.agents.executor import AgentExecutor
        executor = AgentExecutor(db=db, tool_registry=build_tool_registry())
        await executor.run(task)

    return "completed"


class WorkerSettings:
    functions      = [run_agent_task]
    redis_settings = _redis_settings()
    max_jobs       = 10
    job_timeout    = 300