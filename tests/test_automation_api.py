from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import router as tools_router
from app.automation_api import router as automation_router
from app.container import AppContainer
from app.tools import ToolDefinition, ToolRegistry


def make_app() -> FastAPI:
    registry = ToolRegistry()

    async def echo(arguments):
        return {"echo": arguments["value"]}

    registry.register(ToolDefinition("echo", "Echo", echo))
    from app.automation import AutomationRunner, AutomationStore

    store = AutomationStore()
    app = FastAPI()
    app.state.container = AppContainer(
        tools=registry,
        automations=store,
        automation_runner=AutomationRunner(store, registry),
    )
    app.include_router(tools_router)
    app.include_router(automation_router)
    return app


def test_automation_http_crud_and_subject_isolation() -> None:
    with TestClient(make_app()) as client:
        payload = {
            "subject_id": "s1",
            "name": "Echo when ready",
            "trigger": {"kind": "event", "config": {"name": "task.updated"}},
            "conditions": [{"field": "status", "operator": "eq", "value": "ready"}],
            "actions": [{"tool_name": "echo", "arguments": {"value": "done"}}],
        }
        created = client.post("/automations", json=payload)
        assert created.status_code == 200
        automation_id = created.json()["id"]

        assert client.get("/automations", params={"subject_id": "s2"}).json() == {"automations": []}
        assert client.get("/automations", params={"subject_id": "s1"}).json()["automations"][0]["id"] == automation_id
        assert client.get(f"/automations/{automation_id}", params={"subject_id": "s2"}).status_code == 404

        updated = client.patch(
            f"/automations/{automation_id}",
            json={"subject_id": "s1", "enabled": False},
        )
        assert updated.status_code == 200
        assert updated.json()["enabled"] is False

        assert client.delete(f"/automations/{automation_id}", params={"subject_id": "s1"}).json() == {"deleted": True}


def test_automation_rejects_invalid_trigger_and_empty_actions() -> None:
    with TestClient(make_app()) as client:
        response = client.post(
            "/automations",
            json={
                "subject_id": "s1",
                "name": "bad",
                "trigger": {"kind": "webhook", "config": {}},
                "actions": [],
            },
        )
        assert response.status_code == 422


def test_automation_run_executes_matching_action() -> None:
    with TestClient(make_app()) as client:
        created = client.post(
            "/automations",
            json={
                "subject_id": "s1",
                "name": "echo",
                "trigger": {"kind": "event", "config": {"name": "demo"}},
                "actions": [{"tool_name": "echo", "arguments": {"value": "hello"}}],
            },
        ).json()
        response = client.post(
            f"/automations/{created['id']}/run",
            json={"subject_id": "s1", "event": {"status": "ready"}},
        )
        assert response.status_code == 200
        assert response.json()["results"][0]["echo"] == "hello"
