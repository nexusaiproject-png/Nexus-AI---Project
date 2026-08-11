import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import router
from app.container import AppContainer
from app.permissions import AllowListPermissionChecker
from app.calendar_tools import CalendarToolFactory
from app.integrations.calendar_client import CalendarClientAdapter
from app.tools import ToolRegistry


class FakeTransport:
    async def list_events(self, calendar_id, max_results, time_min, time_max):
        return []
    async def get_event(self, calendar_id, event_id):
        return {"event_id": event_id}
    async def create_event(self, calendar_id, event):
        return {"created": True, "event": event}
    async def update_event(self, calendar_id, event_id, event):
        return {"updated": True, "event_id": event_id, "event": event}
    async def delete_event(self, calendar_id, event_id):
        return {"deleted": True, "event_id": event_id}


class FakeConnection:
    async def client_for(self, account_id):
        return CalendarClientAdapter(FakeTransport())


def test_calendar_write_requires_confirmation_at_http_boundary():
    factory = CalendarToolFactory(FakeConnection())
    registry = ToolRegistry(permission_checker=AllowListPermissionChecker(
        frozenset({"calendar.create_event"})
    ))
    registry.register(next(t for t in factory.definitions() if t.name == "calendar.create_event"))

    app = FastAPI()
    app.state.container = AppContainer(tools=registry)
    app.include_router(router)

    with TestClient(app) as client:
        pending = client.post(
            "/tools/calendar.create_event/execute",
            json={"subject_id": "account-1", "confirmation_id": "call-1", "arguments": {
                "account_id": "account-1", "calendar_id": "primary", "event": {"summary": "Demo"}
            }},
        )
        confirmed = client.post(
            "/tools/calendar.create_event/execute",
            json={"subject_id": "account-1", "confirmation_id": "call-1", "confirmed": True, "arguments": {
                "account_id": "account-1", "calendar_id": "primary", "event": {"summary": "Demo"}
            }},
        )

    assert pending.status_code == 409
    assert confirmed.status_code == 200
    assert confirmed.json()["result"]["created"] is True
