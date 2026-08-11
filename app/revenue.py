from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from threading import Lock
from typing import Any

from fastapi import APIRouter

from app.billing import PLANS, _SUBSCRIPTIONS

router = APIRouter(prefix="/revenue", tags=["revenue"])
_lock = Lock()
_events: Counter[str] = Counter()


def record_revenue_event(name: str, **fields: Any) -> None:
    with _lock:
        _events[name] += 1


def _active_subscriptions() -> list[Any]:
    return [s for s in _SUBSCRIPTIONS.values() if s.status in {"active", "trialing"} and s.plan in PLANS]


@router.get("/metrics")
def revenue_metrics() -> dict[str, Any]:
    active = _active_subscriptions()
    mrr = sum(PLANS[s.plan].monthly_usd for s in active)
    paid = [s for s in active if s.plan != "free"]
    arpu = round(mrr / len(paid), 2) if paid else 0
    return {
        "mrr_usd": mrr,
        "arr_usd": mrr * 12,
        "arpu_usd": arpu,
        "paid_subscriptions": len(paid),
        "active_subscriptions": len(active),
        "churned_subscriptions": sum(1 for s in _SUBSCRIPTIONS.values() if s.status == "canceled"),
        "ai_cost_usd": 0,
        "gross_margin_pct": 100 if mrr else 0,
        "calculated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/events")
def revenue_events() -> dict[str, Any]:
    with _lock:
        return {"events": dict(_events)}
