from __future__ import annotations

import json
import os
import sqlite3
import time
from pathlib import Path
from threading import RLock
from typing import Any

from fastapi import APIRouter, Cookie, HTTPException, Request
from fastapi.responses import JSONResponse

from app import auth_api
from app.auth_api import current_user

router = APIRouter(prefix="/security", tags=["security"])


class AuditLog:
    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path or os.getenv("NEXUS_AUTH_DB", "data/auth.db"))
        self._lock = RLock()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS audit_log (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, workspace_id INTEGER, action TEXT NOT NULL, metadata TEXT NOT NULL, created_at INTEGER NOT NULL)")
            conn.commit()

    def bind_to_auth_store(self) -> None:
        self.db_path = Path(auth_api.store.db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS audit_log (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, workspace_id INTEGER, action TEXT NOT NULL, metadata TEXT NOT NULL, created_at INTEGER NOT NULL)")
            conn.commit()

    def record(self, user_id: int, workspace_id: int | None, action: str, metadata: dict[str, Any] | None = None) -> None:
        self.bind_to_auth_store()
        with self._lock, sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("INSERT INTO audit_log(user_id,workspace_id,action,metadata,created_at) VALUES(?,?,?,?,?)", (user_id, workspace_id, action, json.dumps(metadata or {}, sort_keys=True), int(time.time())))
            conn.commit()

    def list_for_user(self, user_id: int) -> list[dict[str, Any]]:
        self.bind_to_auth_store()
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT id,user_id,workspace_id,action,metadata,created_at FROM audit_log WHERE user_id=? ORDER BY id DESC", (user_id,)).fetchall()
        return [{**dict(row), "metadata": json.loads(row["metadata"])} for row in rows]


audit = AuditLog()


def _auth_db() -> Path:
    return Path(auth_api.store.db_path)


@router.get("/audit")
def audit_events(nexus_session: str | None = Cookie(default=None)) -> dict[str, Any]:
    user = current_user(nexus_session)
    return {"events": audit.list_for_user(user.id)}


@router.get("/export")
def export_account(nexus_session: str | None = Cookie(default=None)) -> JSONResponse:
    user = current_user(nexus_session)
    db_path = _auth_db()
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        profile = conn.execute("SELECT id,email,name,email_verified FROM users WHERE id=?", (user.id,)).fetchone()
        memberships = conn.execute("SELECT workspace_id,role FROM memberships WHERE user_id=?", (user.id,)).fetchall()
        workspaces = [dict(row) for row in conn.execute("SELECT id,name,purpose,created_at FROM workspaces WHERE id IN (SELECT workspace_id FROM memberships WHERE user_id=?)", (user.id,)).fetchall()]
    audit.record(user.id, user.workspace_id, "data.export")
    return JSONResponse({"user": dict(profile) if profile else None, "memberships": [dict(row) for row in memberships], "workspaces": workspaces, "audit": audit.list_for_user(user.id)})


@router.delete("/account")
def delete_account(nexus_session: str | None = Cookie(default=None)) -> dict[str, bool]:
    user = current_user(nexus_session)
    db_path = _auth_db()
    with sqlite3.connect(str(db_path)) as conn:
        workspace_rows = conn.execute("SELECT workspace_id FROM memberships WHERE user_id=?", (user.id,)).fetchall()
        workspace_ids = [row[0] for row in workspace_rows]
        conn.execute("DELETE FROM sessions WHERE user_id=?", (user.id,))
        conn.execute("DELETE FROM memberships WHERE user_id=?", (user.id,))
        conn.execute("DELETE FROM users WHERE id=?", (user.id,))
        for workspace_id in workspace_ids:
            if conn.execute("SELECT 1 FROM workspaces WHERE id=? AND owner_id=?", (workspace_id, user.id)).fetchone():
                conn.execute("DELETE FROM memberships WHERE workspace_id=?", (workspace_id,))
                conn.execute("DELETE FROM workspaces WHERE id=?", (workspace_id,))
        conn.commit()
    return {"deleted": True}


async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if request.url.scheme == "https" or os.getenv("NEXUS_FORCE_HSTS", "false").lower() == "true":
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response
