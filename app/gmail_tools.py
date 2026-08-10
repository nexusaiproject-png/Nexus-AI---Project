from typing import Any

from app.integrations.gmail_connection import GmailConnection
from app.tools import ToolDefinition


class GmailToolFactory:
    def __init__(self, connection: GmailConnection) -> None:
        self._connection = connection

    def definitions(self) -> tuple[ToolDefinition, ...]:
        return (
            ToolDefinition(
                name="gmail.list_messages",
                description="List messages for a connected Google account.",
                handler=self.list_messages,
            ),
            ToolDefinition(
                name="gmail.get_message",
                description="Get one message for a connected Google account.",
                handler=self.get_message,
            ),
        )

    async def list_messages(self, arguments: dict[str, Any]) -> Any:
        client = await self._connection.client_for(str(arguments["account_id"]))
        return await client.list_messages(
            max_results=int(arguments.get("max_results", 20)),
            query=arguments.get("query"),
        )

    async def get_message(self, arguments: dict[str, Any]) -> Any:
        client = await self._connection.client_for(str(arguments["account_id"]))
        return await client.get_message(str(arguments["message_id"]))
