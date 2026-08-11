from fastapi.testclient import TestClient

from app import auth_api
from app.auth import AuthStore
from main import app


def test_signup_verify_login_and_me(tmp_path, monkeypatch):
    monkeypatch.setattr(auth_api, "store", AuthStore(tmp_path / "auth.db"))
    client = TestClient(app)

    signup = client.post("/auth/signup", json={"email": "user@example.com", "name": "User", "password": "correct-horse"})
    assert signup.status_code == 201
    token = auth_api.store._connect().execute("SELECT verification_token FROM users").fetchone()[0]

    verify = client.post("/auth/verify-email", json={"token": token})
    assert verify.status_code == 200

    login = client.post("/auth/login", json={"email": "USER@example.com", "password": "correct-horse"})
    assert login.status_code == 200
    assert login.json()["workspace_id"] is None

    me = client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["email_verified"] is True


def test_unverified_login_and_invalid_password_are_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(auth_api, "store", AuthStore(tmp_path / "auth.db"))
    client = TestClient(app)
    client.post("/auth/signup", json={"email": "user@example.com", "name": "User", "password": "correct-horse"})
    assert client.post("/auth/login", json={"email": "user@example.com", "password": "correct-horse"}).status_code == 401
    assert client.post("/auth/verify-email", json={"token": "bad"}).status_code == 400


def test_workspace_onboarding_and_logout(tmp_path, monkeypatch):
    monkeypatch.setattr(auth_api, "store", AuthStore(tmp_path / "auth.db"))
    client = TestClient(app)
    client.post("/auth/signup", json={"email": "user@example.com", "name": "User", "password": "correct-horse"})
    token = auth_api.store._connect().execute("SELECT verification_token FROM users").fetchone()[0]
    client.post("/auth/verify-email", json={"token": token})
    client.post("/auth/login", json={"email": "user@example.com", "password": "correct-horse"})

    workspace = client.post("/auth/workspace", json={"name": "My Workspace", "purpose": "Work"})
    assert workspace.status_code == 201
    assert workspace.json()["role"] == "owner"

    onboarding = client.post("/auth/onboarding", json={"purpose": "Automate my work"})
    assert onboarding.status_code == 200
    assert onboarding.json()["onboarding_complete"] is True

    assert client.post("/auth/logout").status_code == 200
    assert client.get("/auth/me").status_code == 401


def test_password_reset_revokes_sessions(tmp_path, monkeypatch):
    monkeypatch.setattr(auth_api, "store", AuthStore(tmp_path / "auth.db"))
    client = TestClient(app)
    client.post("/auth/signup", json={"email": "user@example.com", "name": "User", "password": "old-password"})
    token = auth_api.store._connect().execute("SELECT verification_token FROM users").fetchone()[0]
    client.post("/auth/verify-email", json={"token": token})
    client.post("/auth/login", json={"email": "user@example.com", "password": "old-password"})

    reset = auth_api.store.request_password_reset("user@example.com")
    assert client.post("/auth/password-reset/confirm", json={"token": reset, "password": "new-password"}).status_code == 200
    assert client.get("/auth/me").status_code == 401
    assert client.post("/auth/login", json={"email": "user@example.com", "password": "new-password"}).status_code == 200
