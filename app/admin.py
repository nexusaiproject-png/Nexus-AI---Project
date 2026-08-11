from __future__ import annotations

import os
import sqlite3
from typing import Any

from fastapi import APIRouter, Cookie, HTTPException

from app import auth_api
from app.auth_api import current_user
from app.billing import _CUSTOMERS, _SUBSCRIPTIONS
from app.observability import _counts
from app.usage import LIMITS, store as usage_store

router = APIRouter(prefix="/admin", tags=["admin"])


def _admin(session: str | None):
    user = current_user(session)
    allowed = {value.strip().lower() for value in os.getenv("NEXUS_ADMIN_EMAILS", "").split(",") if value.strip()}
    if user.email.lower() not in allowed:
        raise HTTPException(status_code=403, detail="admin access required")
    return user


def _db_rows(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with sqlite3.connect(str(auth_api.store.db_path)) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute(query, params).fetchall()]


@router.get("/overview")
def overview(nexus_session: str | None = Cookie(default=None)) -> dict[str, Any]:
    _admin(nexus_session)
    users = _db_rows("SELECT id,email,name,email_verified FROM users ORDER BY id DESC")
    workspaces = _db_rows("SELECT id,name,owner_id,purpose,created_at FROM workspaces ORDER BY id DESC")
    subscriptions = [sub.__dict__.copy() for sub in _SUBSCRIPTIONS.values()]
    usage = {}
    with usage_store._lock:
        for workspace_id, value in usage_store._usage.items():
            usage[str(workspace_id)] = {"ai": value.ai, "agent": value.agent, "automation": value.automation, "storage_bytes": value.storage_bytes}
    return {
        "users": users,
        "workspaces": workspaces,
        "subscriptions": subscriptions,
        "payments": {"customers": len(_CUSTOMERS)},
        "usage": usage,
        "system": {"events": sum(_counts.values())},
    }


@router.get("/users")
def users(nexus_session: str | None = Cookie(default=None)) -> dict[str, Any]:
    _admin(nexus_session)
    return {"users": _db_rows("SELECT id,email,name,email_verified FROM users ORDER BY id DESC")}


@router.get("/workspaces")
def workspaces(nexus_session: str | None = Cookie(default=None)) -> dict[str, Any]:
    _admin(nexus_session)
    return {"workspaces": _db_rows("SELECT id,name,owner_id,purpose,created_at FROM workspaces ORDER BY id DESC")}


@router.get("/subscriptions")
def subscriptions(nexus_session: str | None = Cookie(default=None)) -> dict[str, Any]:
    _admin(nexus_session)
    return {"subscriptions": [sub.__dict__.copy() for sub in _SUBSCRIPTIONS.values()]}


@router.get("/usage")
def usage(nexus_session: str | None = Cookie(default=None)) -> dict[str, Any]:
    _admin(nexus_session)
    with usage_store._lock:
        return {"usage": {str(k): {"ai": v.ai, "agent": v.agent, "automation": v.automation, "storage_bytes": v.storage_bytes} for k, v in usage_store._usage.items()}, "limits": {k: v.__dict__ for k, v in LIMITS.items()}}


@router.get("/health")
def health(nexus_session: str | None = Cookie(default=None)) -> dict[str, Any]:
    _admin(nexus_session)
    return {"status": "ok", "database": auth_api.store.db_path.as_posix(), "customers": len(_CUSTOMERS), "events": sum(_counts.values())}
