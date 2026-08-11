import hashlib
import hmac
import json
import time

from fastapi.testclient import TestClient

from main import app
from app import auth_api
from app.auth import AuthStore


def _signup_verify_login_workspace(client, email):
    signup = client.post("/auth/signup", json={"email": email, "password": "password123", "name": "Paid"})
    assert signup.status_code in {200, 201}
    token = signup.json()["verification_token"]
    assert client.post("/auth/verify", json={"token": token}).status_code == 200
    assert client.post("/auth/login", json={"email": email, "password": "password123"}).status_code == 200
    assert client.post("/auth/workspace", json={"name": "Paid Workspace"}).status_code == 201


def _webhook(client, event, secret="test-secret"):
    body = json.dumps(event).encode()
    timestamp = str(int(time.time()))
    digest = hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()
    return client.post("/billing/webhook", content=body, headers={"stripe-signature": f"t={timestamp},v1={digest}"})


def test_paid_billing_contract(monkeypatch, tmp_path):
    monkeypatch.setattr(auth_api, "store", AuthStore(tmp_path / "auth.db"))
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "test-secret")
    with TestClient(app) as client:
        _signup_verify_login_workspace(client, "paid@example.com")
        plans = client.get("/billing/plans")
        assert plans.status_code == 200
        assert {p["key"] for p in plans.json()["plans"]} == {"free", "pro", "team"}
        assert client.get("/billing/subscription").json()["plan"] == "free"

        event = {"id": "evt_paid_1", "type": "customer.subscription.created", "data": {"object": {"id": "sub_1", "customer": "cus_1", "status": "active", "metadata": {"workspace_id": "workspace-1", "plan": "pro"}}}}
        # Signature/idempotency contract is tested independently of provider credentials.
        response = _webhook(client, event)
        assert response.status_code == 200
        assert _webhook(client, event).status_code == 200
