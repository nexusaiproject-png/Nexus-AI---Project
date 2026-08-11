import hashlib
import hmac
import json
import time

from fastapi.testclient import TestClient

from app.billing import _signature_valid
from main import app


def test_billing_plans_are_public():
    with TestClient(app) as client:
        response = client.get("/billing/plans")
    assert response.status_code == 200
    assert [plan["key"] for plan in response.json()["plans"]] == ["free", "pro", "team"]


def test_webhook_signature_validation():
    payload = b'{"id":"evt_test"}'
    secret = "whsec_test"
    timestamp = str(int(time.time()))
    digest = hmac.new(secret.encode(), f"{timestamp}.".encode() + payload, hashlib.sha256).hexdigest()
    assert _signature_valid(payload, f"t={timestamp},v1={digest}", secret)
    assert not _signature_valid(payload, f"t={timestamp},v1=bad", secret)


def test_webhook_rejects_invalid_signature(monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
    with TestClient(app) as client:
        response = client.post("/billing/webhook", content=json.dumps({"id": "evt_test"}), headers={"stripe-signature": "bad"})
    assert response.status_code == 400
