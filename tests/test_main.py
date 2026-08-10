from fastapi.testclient import TestClient

from main import app


def test_tools_endpoint_exposes_application_registry() -> None:
    with TestClient(app) as client:
        response = client.get("/tools")

    assert response.status_code == 200
    assert response.json() == {
        "tools": [
            "gmail.get_message",
            "gmail.list_messages",
        ]
    }


def test_tool_execution_endpoint_runs_allowed_gmail_tool() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/tools/gmail.list_messages/execute",
            json={
                "subject_id": "account-1",
                "arguments": {"account_id": "account-1", "max_results": 5},
            },
        )

    assert response.status_code == 200


def test_tool_execution_endpoint_rejects_unknown_tool() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/tools/not-a-tool/execute",
            json={"subject_id": "account-1", "arguments": {}},
        )

    assert response.status_code == 404
