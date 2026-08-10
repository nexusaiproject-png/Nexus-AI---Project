from fastapi.testclient import TestClient

from main import app


def test_tool_router_lists_tools() -> None:
    with TestClient(app) as client:
        response = client.get("/tools")

    assert response.status_code == 200
    assert response.json() == {
        "tools": ["gmail.get_message", "gmail.list_messages"]
    }


def test_tool_router_returns_403_for_denied_tool() -> None:
    with TestClient(app) as client:
        app.state.container.tools._permission_checker.allowed_tools = frozenset()
        response = client.post(
            "/tools/gmail.list_messages/execute",
            json={
                "subject_id": "account-1",
                "arguments": {"account_id": "account-1"},
            },
        )

    assert response.status_code == 403
