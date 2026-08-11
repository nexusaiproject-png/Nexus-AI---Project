from typing import Any, Protocol


class CalendarTransport(Protocol):
    async def list_events(self, calendar_id: str, max_results: int, time_min: str | None, time_max: str | None) -> Any: ...
    async def get_event(self, calendar_id: str, event_id: str) -> Any: ...
    async def create_event(self, calendar_id: str, event: dict[str, Any]) -> Any: ...
    async def update_event(self, calendar_id: str, event_id: str, event: dict[str, Any]) -> Any: ...
    async def delete_event(self, calendar_id: str, event_id: str) -> Any: ...


class CalendarClientAdapter:
    def __init__(self, transport: CalendarTransport) -> None:
        self._transport = transport

    async def list_events(self, calendar_id: str = "primary", max_results: int = 20, time_min: str | None = None, time_max: str | None = None) -> Any:
        return await self._transport.list_events(calendar_id, max_results, time_min, time_max)

    async def get_event(self, calendar_id: str, event_id: str) -> Any:
        return await self._transport.get_event(calendar_id, event_id)

    async def create_event(self, calendar_id: str, event: dict[str, Any]) -> Any:
        return await self._transport.create_event(calendar_id, event)

    async def update_event(self, calendar_id: str, event_id: str, event: dict[str, Any]) -> Any:
        return await self._transport.update_event(calendar_id, event_id, event)

    async def delete_event(self, calendar_id: str, event_id: str) -> Any:
        return await self._transport.delete_event(calendar_id, event_id)
