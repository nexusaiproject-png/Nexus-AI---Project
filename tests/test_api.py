import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import router
from app.container import AppContainer
from app.gmail_registry import build_gmail_registry
from app.gmail_tools import GmailToolFactory
from app.permissions import AllowListPermissionChecker
from app.tools import ToolDefinition, ToolRegistry
from main import app


class FakeClient:
    async def list_messages(self, max_results: int = 20, query: str | None = None):
        return {"max_results": max_results, "query": query}

    async def get_message(self, message_id: str):
        return {"message_id": message_id}


class FakeConnection:
    async def client_for(self, account_id: str):
        return FakeClient()


class FakeContainer:
    def __init__(self, tools):
        self.tools = tools


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_tool_router_lists_tools(client: TestClient) -> None:
    response = client.get("/tools")

    assert response.status_code == 200
    assert response.json() == {
        "tools": [
            "calendar.create_event", "calendar.delete_event", "calendar.get_event", "calendar.list_events", "calendar.update_event",
            "files.create_file", "files.delete_file", "files.list_files", "files.read_file", "files.update_file",
            "gmail.get_message", "gmail.list_messages",
            "meetings.connect", "meetings.create", "meetings.delete", "meetings.get", "meetings.list", "meetings.update",
            "tasks.create_task", "tasks.delete_task", "tasks.get_task", "tasks.list_tasks", "tasks.update_task",
        ]
    }


def test_tool_router_returns_403_for_denied_tool(client: TestClient) -> None:
    factory = GmailToolFactory(FakeConnection())
    denied_registry = build_gmail_registry(factory, AllowListPermissionChecker(frozenset()))
    app.state.container = FakeContainer(denied_registry)
    response = client.post("/tools/gmail.list_messages/execute", json={"subject_id": "account-1", "arguments": {"account_id": "account-1"}})
    assert response.status_code == 403


def make_echo_client() -> TestClient:
    registry = ToolRegistry()
    async def echo(arguments):
        return {"echo": arguments["value"]}
    registry.register(ToolDefinition("echo", "Echo", echo))
    test_app = FastAPI()
    test_app.state.container = AppContainer(tools=registry)
    test_app.include_router(router)
    return TestClient(test_app)


def test_echo_tool_http_boundary() -> None:
    with make_echo_client() as client:
        response = client.post("/tools/echo/execute", json={"subject_id": "account-1", "arguments": {"value": "hello"}})
    assert response.status_code == 200
    assert response.json() == {"result": {"echo": "hello"}}


def test_unknown_tool_returns_404() -> None:
    with make_echo_client() as client:
        response = client.post("/tools/missing/execute", json={"subject_id": "account-1", "arguments": {}})
    assert response.status_code == 404


def test_unexpected_tool_failure_returns_502() -> None:
    registry = ToolRegistry()
    async def fail(_: dict[str, object]):
        raise RuntimeError("boom")
    registry.register(ToolDefinition("fail", "Fail", fail))
    test_app = FastAPI()
    test_app.state.container = AppContainer(tools=registry)
    test_app.include_router(router)
    with TestClient(test_app, raise_server_exceptions=False) as client:
        response = client.post("/tools/fail/execute", json={"subject_id": "account-1", "arguments": {}})
    assert response.status_code == 502
    assert response.json()["detail"] == "tool execution failed: boom"
