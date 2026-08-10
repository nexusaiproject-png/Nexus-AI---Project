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
