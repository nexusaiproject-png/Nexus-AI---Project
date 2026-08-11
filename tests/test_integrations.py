from fastapi.testclient import TestClient

from app import auth_api
from app.auth import AuthStore
from main import app


def signup_and_verify(client, email):
    response = client.post("/auth/signup", json={"name": "Test", "email": email, "password": "password123"})
    assert response.status_code == 201
    token = auth_api.store._connect().execute("SELECT verification_token FROM users WHERE email = ?", (email,)).fetchone()[0]
    verify = client.post("/auth/verify-email", json={"token": token})
    assert verify.status_code == 200


def test_connection_lifecycle_and_tenant_isolation(tmp_path, monkeypatch):
    monkeypatch.setattr(auth_api, "store", AuthStore(tmp_path / "auth.db"))
    with TestClient(app) as client:
        signup_and_verify(client, "integration-a@example.com")
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

        client.post("/auth/logout")
        signup_and_verify(client, "integration-b@example.com")
        login = client.post("/auth/login", json={"email": "integration-b@example.com", "password": "password123"})
        assert login.status_code == 200
        assert client.get("/integrations").json()["connections"] == []
