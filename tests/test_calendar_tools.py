import pytest

from app.calendar_tools import CalendarToolFactory
from app.integrations.calendar_client import CalendarClientAdapter


class FakeCalendarTransport:
    async def list_events(self, calendar_id, max_results, time_min, time_max):
        return {"calendar_id": calendar_id, "max_results": max_results, "time_min": time_min, "time_max": time_max}

    async def get_event(self, calendar_id, event_id):
        return {"calendar_id": calendar_id, "event_id": event_id}

    async def create_event(self, calendar_id, event):
        return {"created": True, "calendar_id": calendar_id, "event": event}

    async def update_event(self, calendar_id, event_id, event):
        return {"updated": True, "calendar_id": calendar_id, "event_id": event_id, "event": event}

    async def delete_event(self, calendar_id, event_id):
        return {"deleted": True, "calendar_id": calendar_id, "event_id": event_id}


class FakeConnection:
    def __init__(self):
        self.client = CalendarClientAdapter(FakeCalendarTransport())

    async def client_for(self, account_id):
        assert account_id == "account-1"
        return self.client


@pytest.mark.asyncio
async def test_calendar_tools_cover_read_and_write_operations():
    factory = CalendarToolFactory(FakeConnection())
    tools = {tool.name: tool for tool in factory.definitions()}

    listed = await tools["calendar.list_events"].handler({"account_id": "account-1", "max_results": 10, "query": None, "calendar_id": "primary", "time_min": None, "time_max": None})
    fetched = await tools["calendar.get_event"].handler({"account_id": "account-1", "calendar_id": "primary", "event_id": "event-1"})
    created = await tools["calendar.create_event"].handler({"account_id": "account-1", "calendar_id": "primary", "event": {"summary": "Demo"}})
    updated = await tools["calendar.update_event"].handler({"account_id": "account-1", "calendar_id": "primary", "event_id": "event-1", "event": {"summary": "Updated"}})
    deleted = await tools["calendar.delete_event"].handler({"account_id": "account-1", "calendar_id": "primary", "event_id": "event-1"})

    assert listed["max_results"] == 10
    assert fetched["event_id"] == "event-1"
    assert created["created"] is True
    assert updated["updated"] is True
    assert deleted["deleted"] is True
    assert tools["calendar.list_events"].requires_confirmation is False
    assert tools["calendar.get_event"].requires_confirmation is False
    assert tools["calendar.create_event"].requires_confirmation is True
    assert tools["calendar.update_event"].requires_confirmation is True
    assert tools["calendar.delete_event"].requires_confirmation is True
