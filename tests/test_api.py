import pytest
from fastapi.testclient import TestClient

from app.gmail_tools import GmailToolFactory
from app.gmail_registry import build_gmail_registry
from app.permissions import AllowListPermissionChecker
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
        "tools": ["gmail.get_message", "gmail.list_messages"]
    }


def test_tool_router_returns_403_for_denied_tool(client: TestClient) -> None:
    factory = GmailToolFactory(FakeConnection())
    denied_registry = build_gmail_registry(
        factory, AllowListPermissionChecker(frozenset())
    )
    app.state.container = FakeContainer(denied_registry)

    response = client.post(
        "/tools/gmail.list_messages/execute",
        json={
            "subject_id": "account-1",
            "arguments": {"account_id": "account-1"},
        },
    )

    assert response.status_code == 403
