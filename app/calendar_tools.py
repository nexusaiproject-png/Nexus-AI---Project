from typing import Any

from app.integrations.calendar_connection import CalendarConnection
from app.schemas import (
    CalendarCreateEventArguments,
    CalendarDeleteEventArguments,
    CalendarGetEventArguments,
    CalendarListEventsArguments,
    CalendarUpdateEventArguments,
)
from app.tools import ToolDefinition


class CalendarToolFactory:
    def __init__(self, connection: CalendarConnection) -> None:
        self._connection = connection

    def definitions(self) -> tuple[ToolDefinition, ...]:
        return (
            ToolDefinition(
                name="calendar.list_events",
                description="List calendar events for a connected Google account.",
                handler=self.list_events,
                arguments_model=CalendarListEventsArguments,
            ),
            ToolDefinition(
                name="calendar.get_event",
                description="Get one calendar event for a connected Google account.",
                handler=self.get_event,
                arguments_model=CalendarGetEventArguments,
            ),
            ToolDefinition(
                name="calendar.create_event",
                description="Create a calendar event for a connected Google account.",
                handler=self.create_event,
                arguments_model=CalendarCreateEventArguments,
                requires_confirmation=True,
            ),
            ToolDefinition(
                name="calendar.update_event",
                description="Update a calendar event for a connected Google account.",
                handler=self.update_event,
                arguments_model=CalendarUpdateEventArguments,
                requires_confirmation=True,
            ),
            ToolDefinition(
                name="calendar.delete_event",
                description="Delete a calendar event for a connected Google account.",
                handler=self.delete_event,
                arguments_model=CalendarDeleteEventArguments,
                requires_confirmation=True,
            ),
        )

    async def list_events(self, arguments: dict[str, Any]) -> Any:
        client = await self._connection.client_for(arguments["account_id"])
        return await client.list_events(
            calendar_id=arguments["calendar_id"],
            max_results=arguments["max_results"],
            time_min=arguments["time_min"],
            time_max=arguments["time_max"],
        )

    async def get_event(self, arguments: dict[str, Any]) -> Any:
        client = await self._connection.client_for(arguments["account_id"])
        return await client.get_event(arguments["calendar_id"], arguments["event_id"])

    async def create_event(self, arguments: dict[str, Any]) -> Any:
        client = await self._connection.client_for(arguments["account_id"])
        return await client.create_event(
            calendar_id=arguments["calendar_id"],
            event=arguments["event"],
        )

    async def update_event(self, arguments: dict[str, Any]) -> Any:
        client = await self._connection.client_for(arguments["account_id"])
        return await client.update_event(
            calendar_id=arguments["calendar_id"],
            event_id=arguments["event_id"],
            event=arguments["event"],
        )

    async def delete_event(self, arguments: dict[str, Any]) -> Any:
        client = await self._connection.client_for(arguments["account_id"])
        return await client.delete_event(arguments["calendar_id"], arguments["event_id"])
