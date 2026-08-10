from fastapi.testclient import TestClient

from app.permissions import PermissionDeniedError
from app.tools import ToolArgumentError
from main import app


class FakeTools:
    def __init__(self, allowed: bool = True, invalid: bool = False) -> None:
        self.allowed = allowed
        self.invalid = invalid

    def names(self) -> tuple[str, ...]:
        return ("gmail.get_message", "gmail.list_messages")

    async def execute(self, name: str, arguments: dict[str, object], subject_id: str):
        if name != "gmail.list_messages":
            raise KeyError(f"tool not found: {name}")
        if not self.allowed:
            raise PermissionDeniedError(f"permission denied: {name}")
        if self.invalid:
            raise ToolArgumentError("invalid arguments")
        return {"max_results": arguments.get("max_results", 20)}


class FakeContainer:
    def __init__(self, allowed: bool = True, invalid: bool = False) -> None:
        self.tools = FakeTools(allowed=allowed, invalid=invalid)


def test_tools_endpoint_exposes_application_registry() -> None:
    with TestClient(app) as client:
        response = client.get("/tools")

    assert response.status_code == 200
    assert response.json() == {"tools": ["gmail.get_message", "gmail.list_messages"]}


def test_tool_execution_endpoint_runs_allowed_gmail_tool() -> None:
    with TestClient(app) as client:
        app.state.container = FakeContainer()
        response = client.post("/tools/gmail.list_messages/execute", json={
            "subject_id": "account-1",
            "arguments": {"account_id": "account-1", "max_results": 5},
        })

    assert response.status_code == 200
    assert response.json() == {"result": {"max_results": 5}}


def test_tool_execution_endpoint_rejects_unknown_tool() -> None:
    with TestClient(app) as client:
        app.state.container = FakeContainer()
        response = client.post("/tools/not-a-tool/execute", json={"subject_id": "account-1", "arguments": {}})

    assert response.status_code == 404


def test_tool_execution_endpoint_maps_permission_denial() -> None:
    with TestClient(app) as client:
        app.state.container = FakeContainer(allowed=False)
        response = client.post("/tools/gmail.list_messages/execute", json={
            "subject_id": "account-1",
            "arguments": {"account_id": "account-1"},
        })

    assert response.status_code == 403


def test_tool_execution_endpoint_maps_argument_errors() -> None:
    with TestClient(app) as client:
        app.state.container = FakeContainer(invalid=True)
        response = client.post("/tools/gmail.list_messages/execute", json={
            "subject_id": "account-1",
            "arguments": {"account_id": "account-1"},
        })

    assert response.status_code == 422
