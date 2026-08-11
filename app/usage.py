from __future__ import annotations

import time
from dataclasses import dataclass, field
from threading import Lock

from fastapi import APIRouter, Cookie, HTTPException
from pydantic import BaseModel, Field

from app.auth_api import current_user
from app.billing import PLANS


@dataclass(frozen=True)
class UsageLimit:
    ai: int
    agent: int
    automation: int
    storage_bytes: int
    requests_per_minute: int


LIMITS = {
    "free": UsageLimit(ai=100, agent=25, automation=50, storage_bytes=100 * 1024 * 1024, requests_per_minute=30),
    "pro": UsageLimit(ai=5000, agent=1000, automation=5000, storage_bytes=10 * 1024**3, requests_per_minute=120),
    "team": UsageLimit(ai=25000, agent=5000, automation=25000, storage_bytes=100 * 1024**3, requests_per_minute=300),
}


@dataclass
class Usage:
    ai: int = 0
    agent: int = 0
    automation: int = 0
    storage_bytes: int = 0
    window_started: float = field(default_factory=time.monotonic)
    requests: int = 0


class UsageLimitExceeded(Exception):
    def __init__(self, metric: str, limit: int) -> None:
        self.metric = metric
        self.limit = limit
        super().__init__(f"{metric} usage limit exceeded ({limit})")


class UsageStore:
    def __init__(self) -> None:
        self._usage: dict[str, Usage] = {}
        self._lock = Lock()

    def _get(self, workspace_id: str) -> Usage:
        return self._usage.setdefault(workspace_id, Usage())

    def snapshot(self, workspace_id: str) -> Usage:
        with self._lock:
            current = self._get(workspace_id)
            return Usage(current.ai, current.agent, current.automation, current.storage_bytes, current.window_started, current.requests)

    def consume(self, workspace_id: str, plan: str, metric: str, amount: int = 1) -> Usage:
        if amount <= 0:
            raise ValueError("amount must be positive")
        limits = LIMITS[plan]
        with self._lock:
            usage = self._get(workspace_id)
            if metric == "storage_bytes":
                new_value = usage.storage_bytes + amount
            else:
                current = getattr(usage, metric)
                new_value = current + amount
            limit = getattr(limits, metric)
            if new_value > limit:
                raise UsageLimitExceeded(metric, limit)
            setattr(usage, metric, new_value)
            return self.snapshot(workspace_id)

    def allow_request(self, workspace_id: str, plan: str) -> bool:
        limit = LIMITS[plan].requests_per_minute
        now = time.monotonic()
        with self._lock:
            usage = self._get(workspace_id)
            if now - usage.window_started >= 60:
                usage.window_started = now
                usage.requests = 0
            if usage.requests >= limit:
                return False
            usage.requests += 1
            return True


store = UsageStore()
router = APIRouter(prefix="/usage", tags=["usage"])


class ConsumeRequest(BaseModel):
    metric: str = Field(pattern="^(ai|agent|automation|storage_bytes)$")
    amount: int = Field(default=1, gt=0)


def _workspace(session: str | None) -> tuple[str, str]:
    user = current_user(session)
    if not user.workspace_id:
        raise HTTPException(status_code=400, detail="workspace required")
    from app.billing import _SUBSCRIPTIONS
    sub = _SUBSCRIPTIONS.get(user.workspace_id)
    plan = sub.plan if sub and sub.status in {"active", "trialing"} else "free"
    if plan not in PLANS:
        plan = "free"
    return user.workspace_id, plan


@router.get("")
def usage(nexus_session: str | None = Cookie(default=None)) -> dict:
    workspace_id, plan = _workspace(nexus_session)
    current = store.snapshot(workspace_id)
    limit = LIMITS[plan]
    return {
        "workspace_id": workspace_id,
        "plan": plan,
        "usage": {"ai": current.ai, "agent": current.agent, "automation": current.automation, "storage_bytes": current.storage_bytes},
        "limits": {"ai": limit.ai, "agent": limit.agent, "automation": limit.automation, "storage_bytes": limit.storage_bytes, "requests_per_minute": limit.requests_per_minute},
    }


@router.post("/consume")
def consume(payload: ConsumeRequest, nexus_session: str | None = Cookie(default=None)) -> dict:
    workspace_id, plan = _workspace(nexus_session)
    try:
        current = store.consume(workspace_id, plan, payload.metric, payload.amount)
    except UsageLimitExceeded as exc:
        raise HTTPException(status_code=429, detail={"metric": exc.metric, "limit": exc.limit, "code": "usage_limit_exceeded"}) from exc
    return {"metric": payload.metric, "amount": payload.amount, "usage": current.__dict__}


@router.post("/rate-limit")
def rate_limit(nexus_session: str | None = Cookie(default=None)) -> dict:
    workspace_id, plan = _workspace(nexus_session)
    if not store.allow_request(workspace_id, plan):
        raise HTTPException(status_code=429, detail={"code": "rate_limit_exceeded", "retry_after": 60})
    return {"allowed": True}
