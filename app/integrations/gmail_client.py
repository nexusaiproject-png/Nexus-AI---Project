from typing import Any, Protocol


class GmailTransport(Protocol):
    async def list_messages(self, max_results: int, query: str | None) -> Any: ...
    async def get_message(self, message_id: str) -> Any: ...


class GmailClientAdapter:
    def __init__(self, transport: GmailTransport) -> None:
        self._transport = transport

    async def list_messages(self, max_results: int = 20, query: str | None = None) -> Any:
        return await self._transport.list_messages(max_results, query)

    async def get_message(self, message_id: str) -> Any:
        return await self._transport.get_message(message_id)
