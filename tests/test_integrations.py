from fastapi.testclient import TestClient

from main import app
from app.integrations import store


def signup(client, email):
    response = client.post("/auth/signup", json={"name": "Test", "email": email, "password": "password123"})
    assert response.status_code in {200, 201}
    return response


def test_connection_lifecycle_and_tenant_isolation():
    with TestClient(app) as client:
        signup(client, "integration-a@example.com")
        login = client.post("/auth/login", json={"email": "integration-a@example.com", "password": "password123"})
        assert login.status_code == 200
        connection = client.post("/integrations", json={"provider": "gmail", "access_token": "secret", "scopes": ["mail.read"]})
        assert connection.status_code == 200
        item_id = connection.json()["id"]
        listed = client.get("/integrations")
        assert listed.status_code == 200
        assert listed.json()["connections"][0]["provider"] == "gmail"
        assert "access_token" not in listed.json()["connections"][0]
        refreshed = client.post(f"/integrations/{item_id}/refresh", json={"access_token": "new-secret"})
        assert refreshed.status_code == 200
        assert client.delete(f"/integrations/{item_id}").status_code == 200

        signup(client, "integration-b@example.com")
        client.post("/auth/login", json={"email": "integration-b@example.com", "password": "password123"})
        assert client.get("/integrations").json()["connections"] == []
