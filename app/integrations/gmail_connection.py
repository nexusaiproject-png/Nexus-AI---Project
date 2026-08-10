from typing import Protocol, Any

from app.integrations.oauth import InMemoryTokenStore


class GmailClient(Protocol):
    async def list_messages(self, max_results: int = 20, query: str | None = None) -> Any: ...
    async def get_message(self, message_id: str) -> Any: ...


class GmailConnection:
    def __init__(self, token_store: InMemoryTokenStore) -> None:
        self._token_store = token_store
        self._clients: dict[str, GmailClient] = {}

    def register_client(self, account_id: str, client: GmailClient) -> None:
        self._clients[account_id] = client

    async def client_for(self, account_id: str) -> GmailClient:
        client = self._clients.get(account_id)
        if client is None:
            token = await self._token_store.get(account_id)
            if token is None:
                raise KeyError(f"Gmail account not connected: {account_id}")
            raise NotImplementedError("Gmail API transport is not configured")
        return client
