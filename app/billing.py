from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Cookie, HTTPException, Request
from pydantic import BaseModel

from app.auth_api import current_user

router = APIRouter(prefix="/billing", tags=["billing"])


@dataclass(frozen=True)
class Plan:
    key: str
    name: str
    monthly_usd: int
    stripe_price_env: str | None


PLANS = {
    "free": Plan("free", "Free", 0, None),
    "pro": Plan("pro", "Pro", 29, "STRIPE_PRICE_PRO"),
    "team": Plan("team", "Team", 99, "STRIPE_PRICE_TEAM"),
}


@dataclass
class Subscription:
    id: str
    workspace_id: str
    plan: str
    status: str
    provider_subscription_id: str | None = None
    provider_customer_id: str | None = None
    latest_payment_intent: str | None = None
    cancel_at_period_end: bool = False
    current_period_end: str | None = None


_SUBSCRIPTIONS: dict[str, Subscription] = {}
_CUSTOMERS: dict[str, str] = {}
_PROCESSED_EVENTS: set[str] = set()


class CheckoutRequest(BaseModel):
    plan: str


class CancelRequest(BaseModel):
    cancel_at_period_end: bool = True


class RefundRequest(BaseModel):
    amount: int | None = None


def _workspace_id(session: str | None) -> str:
    user = current_user(session)
    if not user.workspace_id:
        raise HTTPException(status_code=400, detail="workspace required")
    return user.workspace_id


def _stripe_request(path: str, data: dict[str, str]) -> dict[str, Any]:
    key = os.getenv("STRIPE_SECRET_KEY")
    if not key:
        raise HTTPException(status_code=503, detail="billing provider is not configured")
    encoded = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(
        f"https://api.stripe.com/v1/{path}",
        data=encoded,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except Exception as exc:
        raise HTTPException(status_code=502, detail="billing provider request failed") from exc


def _ensure_customer(workspace_id: str, email: str) -> str:
    if workspace_id in _CUSTOMERS:
        return _CUSTOMERS[workspace_id]
    customer = _stripe_request("customers", {"email": email, "metadata[workspace_id]": workspace_id})
    customer_id = customer["id"]
    _CUSTOMERS[workspace_id] = customer_id
    return customer_id


def _signature_valid(payload: bytes, header: str, secret: str) -> bool:
    timestamp = None
    signatures: list[str] = []
    for part in header.split(","):
        key, _, value = part.partition("=")
        if key == "t":
            timestamp = value
        elif key == "v1":
            signatures.append(value)
    if not timestamp or not signatures:
        return False
    try:
        if abs(time.time() - int(timestamp)) > 300:
            return False
    except ValueError:
        return False
    expected = hmac.new(secret.encode(), f"{timestamp}.".encode() + payload, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, signature) for signature in signatures)


@router.get("/plans")
def plans() -> dict[str, Any]:
    return {"plans": [{"key": p.key, "name": p.name, "monthly_usd": p.monthly_usd} for p in PLANS.values()]}


@router.get("/subscription")
def subscription(nexus_session: str | None = Cookie(default=None)) -> dict[str, Any]:
    workspace_id = _workspace_id(nexus_session)
    sub = _SUBSCRIPTIONS.get(workspace_id)
    if not sub:
        return {"plan": "free", "status": "active", "cancel_at_period_end": False}
    return sub.__dict__


@router.post("/checkout")
def checkout(payload: CheckoutRequest, nexus_session: str | None = Cookie(default=None)) -> dict[str, Any]:
    workspace_id = _workspace_id(nexus_session)
    plan = PLANS.get(payload.plan)
    if not plan or plan.key == "free":
        raise HTTPException(status_code=400, detail="a paid plan is required")
    price_id = os.getenv(plan.stripe_price_env or "")
    if not price_id:
        raise HTTPException(status_code=503, detail=f"{plan.key} billing price is not configured")
    user = current_user(nexus_session)
    customer_id = _ensure_customer(workspace_id, user.email)
    base = os.getenv("NEXUS_PUBLIC_URL", "http://localhost:8000").rstrip("/")
    session = _stripe_request("checkout/sessions", {
        "mode": "subscription",
        "customer": customer_id,
        "line_items[0][price]": price_id,
        "line_items[0][quantity]": "1",
        "subscription_data[metadata][workspace_id]": workspace_id,
        "subscription_data[metadata][plan]": plan.key,
        "metadata[workspace_id]": workspace_id,
        "metadata[plan]": plan.key,
        "success_url": f"{base}/web/billing.html?success=1",
        "cancel_url": f"{base}/web/billing.html?canceled=1",
    })
    return {"checkout_url": session.get("url"), "session_id": session.get("id")}


@router.post("/cancel")
def cancel(payload: CancelRequest, nexus_session: str | None = Cookie(default=None)) -> dict[str, Any]:
    workspace_id = _workspace_id(nexus_session)
    sub = _SUBSCRIPTIONS.get(workspace_id)
    if not sub or not sub.provider_subscription_id:
        raise HTTPException(status_code=404, detail="active paid subscription not found")
    _stripe_request(f"subscriptions/{sub.provider_subscription_id}", {"cancel_at_period_end": str(payload.cancel_at_period_end).lower()})
    sub.cancel_at_period_end = payload.cancel_at_period_end
    return sub.__dict__


@router.post("/refund")
def refund(payload: RefundRequest, nexus_session: str | None = Cookie(default=None)) -> dict[str, Any]:
    workspace_id = _workspace_id(nexus_session)
    sub = _SUBSCRIPTIONS.get(workspace_id)
    if not sub or not sub.latest_payment_intent:
        raise HTTPException(status_code=404, detail="refundable payment not found")
    data = {"payment_intent": sub.latest_payment_intent}
    if payload.amount is not None:
        if payload.amount <= 0:
            raise HTTPException(status_code=400, detail="refund amount must be positive")
        data["amount"] = str(payload.amount)
    result = _stripe_request("refunds", data)
    return {"refund_id": result.get("id"), "status": result.get("status")}


@router.post("/portal")
def portal(nexus_session: str | None = Cookie(default=None)) -> dict[str, Any]:
    workspace_id = _workspace_id(nexus_session)
    customer_id = _CUSTOMERS.get(workspace_id)
    if not customer_id:
        raise HTTPException(status_code=404, detail="billing customer not found")
    base = os.getenv("NEXUS_PUBLIC_URL", "http://localhost:8000").rstrip("/")
    session = _stripe_request("billing_portal/sessions", {"customer": customer_id, "return_url": f"{base}/web/billing.html"})
    return {"portal_url": session.get("url")}


@router.post("/webhook")
async def webhook(request: Request) -> dict[str, bool]:
    payload = await request.body()
    secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    signature = request.headers.get("stripe-signature", "")
    if not secret or not _signature_valid(payload, signature, secret):
        raise HTTPException(status_code=400, detail="invalid webhook signature")
    event = json.loads(payload)
    event_id = event.get("id")
    if not event_id:
        raise HTTPException(status_code=400, detail="event id required")
    if event_id in _PROCESSED_EVENTS:
        return {"received": True}
    event_type = event.get("type")
    obj = event.get("data", {}).get("object", {})
    workspace_id = obj.get("metadata", {}).get("workspace_id")
    if workspace_id:
        if event_type in {"checkout.session.completed", "customer.subscription.created", "customer.subscription.updated"}:
            plan = obj.get("metadata", {}).get("plan", "pro")
            _SUBSCRIPTIONS[workspace_id] = Subscription(
                id=str(uuid.uuid4()), workspace_id=workspace_id, plan=plan,
                status=obj.get("status", "active"),
                provider_subscription_id=obj.get("subscription") or obj.get("id"),
                provider_customer_id=obj.get("customer"),
                cancel_at_period_end=bool(obj.get("cancel_at_period_end", False)),
                current_period_end=datetime.fromtimestamp(obj["current_period_end"], tz=timezone.utc).isoformat() if obj.get("current_period_end") else None,
            )
        elif event_type == "invoice.paid":
            sub = _SUBSCRIPTIONS.get(workspace_id)
            if sub:
                sub.status = "active"
                sub.latest_payment_intent = obj.get("payment_intent")
        elif event_type in {"customer.subscription.deleted", "invoice.payment_failed"}:
            sub = _SUBSCRIPTIONS.get(workspace_id)
            if sub:
                sub.status = "canceled" if event_type.endswith("deleted") else "past_due"
    _PROCESSED_EVENTS.add(event_id)
    return {"received": True}
