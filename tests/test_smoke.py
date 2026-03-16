import pytest
from fastapi.testclient import TestClient


def test_imports():
    from app.config import settings
    from app.database import Base
    from app.models.task import Task, TaskStep, TaskStatus
    from app.tools.base_tool import BaseTool
    from app.tools.search_tool import SearchBusinessesTool
    from app.tools.calendar_tool import CheckCalendarTool, CreateCalendarEventTool
    from app.agents.planner import AVAILABLE_TOOLS
    from app.agents.executor import AgentExecutor
    from app.workers.agent_worker import WorkerSettings, build_tool_registry
    assert True


def test_health():
    from main import app
    client   = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_task_status_values():
    from app.models.task import TaskStatus
    assert TaskStatus.QUEUED    == "queued"
    assert TaskStatus.COMPLETED == "completed"
    assert TaskStatus.FAILED    == "failed"


def test_base_tool_require():
    from app.tools.base_tool import BaseTool
    import asyncio

    class Dummy(BaseTool):
        name = "dummy"
        description = "test"
        async def run(self, params: dict) -> dict:
            self.require(params, "query", "location")
            return {"ok": True}

    with pytest.raises(ValueError, match="Missing required params"):
        asyncio.run(Dummy().run({"query": "salon"}))


def test_tool_registry_keys():
    from app.workers.agent_worker import build_tool_registry
    registry = build_tool_registry()
    assert "search_businesses"     in registry
    assert "check_calendar"        in registry
    assert "create_calendar_event" in registry
```

---

## Final folder structure

Your repo should look exactly like this when done:
```
Jarvis/
├── main.py
├── run.py
├── requirements.txt
├── docker-compose.yml
├── alembic.ini
├── .env.example
├── .gitignore
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/          ← empty folder, just create it
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── planner.py
│   │   └── executor.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base_tool.py
│   │   ├── search_tool.py
│   │   └── calendar_tool.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── task.py
│   ├── workers/
│   │   ├── __init__.py
│   │   └── agent_worker.py
│   ├── services/          ← empty folder for Phase 3
│   │   └── __init__.py
│   └── api/
│       ├── __init__.py
│       └── routes/
│           ├── __init__.py
│           └── tasks.py
└── tests/
    ├── __init__.py
    └── test_smoke.py