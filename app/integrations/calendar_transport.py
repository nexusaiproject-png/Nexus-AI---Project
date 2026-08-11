from typing import Any

from app.integrations.calendar_client import CalendarTransport


class UnconfiguredCalendarTransport(CalendarTransport):
    def __init__(self, account_id: str, access_token: str) -> None:
        self.account_id = account_id
        self.access_token = access_token

    async def list_events(self, calendar_id: str, max_results: int, time_min: str | None, time_max: str | None) -> Any:
        raise NotImplementedError("Google Calendar API transport is not configured")

    async def get_event(self, calendar_id: str, event_id: str) -> Any:
        raise NotImplementedError("Google Calendar API transport is not configured")

    async def create_event(self, calendar_id: str, event: dict[str, Any]) -> Any:
        raise NotImplementedError("Google Calendar API transport is not configured")

    async def update_event(self, calendar_id: str, event_id: str, event: dict[str, Any]) -> Any:
        raise NotImplementedError("Google Calendar API transport is not configured")

    async def delete_event(self, calendar_id: str, event_id: str) -> Any:
        raise NotImplementedError("Google Calendar API transport is not configured")
