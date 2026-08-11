from fastapi.testclient import TestClient

from app import auth_api
from app.auth import AuthStore
from main import app


def signup_verify_login_workspace(client, email):
    signup = client.post("/auth/signup", json={"name": "Security Test", "email": email, "password": "password123"})
    token = auth_api.store._connect().execute("SELECT verification_token FROM users WHERE email=?", (email,)).fetchone()[0]
    assert client.post("/auth/verify-email", json={"token": token}).status_code == 200
    assert client.post("/auth/login", json={"email": email, "password": "password123"}).status_code == 200
    assert client.post("/auth/workspace", json={"name": "Secure Workspace"}).status_code == 201


def test_security_headers_and_audit_export(tmp_path, monkeypatch):
    monkeypatch.setattr(auth_api, "store", AuthStore(tmp_path / "auth.db"))
    with TestClient(app) as client:
        signup_verify_login_workspace(client, "security@example.com")
        response = client.get("/health")
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        exported = client.get("/security/export")
        assert exported.status_code == 200
        assert exported.json()["user"]["email"] == "security@example.com"
        events = client.get("/security/audit")
        assert events.status_code == 200
        assert any(event["action"] == "data.export" for event in events.json()["events"])


def test_account_deletion(tmp_path, monkeypatch):
    monkeypatch.setattr(auth_api, "store", AuthStore(tmp_path / "auth.db"))
    with TestClient(app) as client:
        signup_verify_login_workspace(client, "delete@example.com")
        assert client.delete("/security/account").status_code == 200
        assert client.get("/auth/me").status_code == 401
