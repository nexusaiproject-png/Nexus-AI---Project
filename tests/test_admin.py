from fastapi.testclient import TestClient

from main import app
from app import auth_api
from app.auth import AuthStore


def signup_verify_login_workspace(client, email, name="Admin"):
    response = client.post("/auth/signup", json={"email": email, "name": name, "password": "password123"})
    assert response.status_code == 201
    user = auth_api.store.get_user(response.json()["user_id"])
    assert user is not None
    client.post("/auth/verify-email", json={"token": user["verification_token"]})
    assert client.post("/auth/login", json={"email": email, "password": "password123"}).status_code == 200
    assert client.post("/auth/workspace", json={"name": "Admin Workspace", "purpose": "support"}).status_code == 201


def test_admin_console_requires_allowlisted_email(tmp_path, monkeypatch):
    monkeypatch.setattr(auth_api, "store", AuthStore(tmp_path / "auth.db"))
    monkeypatch.setenv("NEXUS_ADMIN_EMAILS", "admin@example.com")
    with TestClient(app) as client:
        signup_verify_login_workspace(client, "admin@example.com")
        overview = client.get("/admin/overview")
        assert overview.status_code == 200
        assert overview.json()["users"][0]["email"] == "admin@example.com"
        assert client.get("/admin/users").status_code == 200
        assert client.get("/admin/workspaces").status_code == 200
        assert client.get("/admin/subscriptions").status_code == 200
        assert client.get("/admin/usage").status_code == 200
        assert client.get("/admin/health").json()["status"] == "ok"


def test_admin_console_denies_non_admin(tmp_path, monkeypatch):
    monkeypatch.setattr(auth_api, "store", AuthStore(tmp_path / "auth.db"))
    monkeypatch.setenv("NEXUS_ADMIN_EMAILS", "admin@example.com")
    with TestClient(app) as client:
        signup_verify_login_workspace(client, "user@example.com", "User")
        assert client.get("/admin/overview").status_code == 403
