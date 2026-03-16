import pytest
from fastapi.testclient import TestClient


def test_imports():
    from app.core.config import settings
    from app.agents.planner import plan_task
    from app.agents.executor import execute_plan
    from app.tools.calendar_tool import check_calendar, add_to_calendar
    from app.tools.search_tool import search_salons, call_salon, confirm_booking
    from app.tools.calling import call_business
    assert True


def test_health():
    from app.main import app
    client   = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_root():
    from app.main import app
    client   = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200


def test_tool_params():
    import asyncio

    from app.tools.search_tool import search_salons
    result = asyncio.run(search_salons({"query": "hair salon", "location": "Toronto"}))
    assert result["status"] == "success"
    assert "results" in result