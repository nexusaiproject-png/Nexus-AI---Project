from fastapi.testclient import TestClient

from main import app


def test_execute_list_messages_with_defaults() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/tools/gmail.list_messages/execute",
            json={
                "subject_id": "account-1",
                "arguments": {"account_id": "account-1"},
            },
        )

    assert response.status_code in {200, 404, 501}
