from __future__ import annotations

import secrets
from dataclasses import dataclass
from threading import RLock
from typing import Literal

from fastapi import APIRouter, Cookie, HTTPException
from pydantic import BaseModel, Field

from app.auth_api import current_user

Provider = Literal["gmail", "calendar", "files", "meetings", "developer"]


@dataclass
class Connection:
    id: str
    workspace_id: str
    provider: Provider
    access_token: str
    refresh_token: str | None
    status: str = "connected"
    scopes: tuple[str, ...] = ()


class IntegrationStore:
    def __init__(self) -> None:
        self._items: dict[str, Connection] = {}
        self._lock = RLock()

    def connect(self, workspace_id: str, provider: Provider, access_token: str, refresh_token: str | None, scopes: list[str]) -> Connection:
        if not access_token:
            raise ValueError("access_token is required")
        with self._lock:
            connection = Connection(secrets.token_urlsafe(18), workspace_id, provider, access_token, refresh_token, scopes=tuple(scopes))
            self._items[connection.id] = connection
            return connection

    def list(self, workspace_id: str) -> list[Connection]:
        with self._lock:
            return [item for item in self._items.values() if item.workspace_id == workspace_id and item.status != "revoked"]

    def disconnect(self, workspace_id: str, connection_id: str) -> None:
        with self._lock:
            item = self._items.get(connection_id)
            if item is None or item.workspace_id != workspace_id:
                raise KeyError(connection_id)
            item.status = "revoked"
            item.access_token = ""
            item.refresh_token = None

    def refresh(self, workspace_id: str, connection_id: str, access_token: str) -> Connection:
        with self._lock:
            item = self._items.get(connection_id)
            if item is None or item.workspace_id != workspace_id:
                raise KeyError(connection_id)
            item.access_token = access_token
            item.status = "connected"
            return item


store = IntegrationStore()
router = APIRouter(prefix="/integrations", tags=["integrations"])


class ConnectRequest(BaseModel):
    provider: Provider
    access_token: str = Field(min_length=1)
    refresh_token: str | None = None
    scopes: list[str] = []


class RefreshRequest(BaseModel):
    access_token: str = Field(min_length=1)


def _workspace(session: str | None) -> str:
    user = current_user(session)
    if not user.workspace_id:
        raise HTTPException(status_code=400, detail="workspace required")
    return user.workspace_id


def _public(item: Connection) -> dict:
    return {"id": item.id, "workspace_id": item.workspace_id, "provider": item.provider, "status": item.status, "scopes": list(item.scopes)}


@router.get("")
def list_connections(nexus_session: str | None = Cookie(default=None)) -> dict:
    workspace_id = _workspace(nexus_session)
    return {"connections": [_public(item) for item in store.list(workspace_id)]}


@router.post("")
def connect(payload: ConnectRequest, nexus_session: str | None = Cookie(default=None)) -> dict:
    workspace_id = _workspace(nexus_session)
    return _public(store.connect(workspace_id, payload.provider, payload.access_token, payload.refresh_token, payload.scopes))


@router.post("/{connection_id}/refresh")
def refresh(connection_id: str, payload: RefreshRequest, nexus_session: str | None = Cookie(default=None)) -> dict:
    workspace_id = _workspace(nexus_session)
    try:
        return _public(store.refresh(workspace_id, connection_id, payload.access_token))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="connection not found") from exc


@router.delete("/{connection_id}")
def disconnect(connection_id: str, nexus_session: str | None = Cookie(default=None)) -> dict:
    workspace_id = _workspace(nexus_session)
    try:
        store.disconnect(workspace_id, connection_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="connection not found") from exc
    return {"ok": True}
