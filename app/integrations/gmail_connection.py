from typing import Any

from app.integrations.gmail_client import GmailClientAdapter
from app.integrations.gmail_factory import GmailClientFactory
from app.integrations.gmail_transport import UnconfiguredGmailTransport
from app.integrations.oauth import InMemoryTokenStore


class GmailConnection:
    def __init__(
        self,
        token_store: InMemoryTokenStore,
        client_factory: GmailClientFactory | None = None,
    ) -> None:
        self._token_store = token_store
        self._client_factory = client_factory or GmailClientFactory(
            lambda account_id, access_token: UnconfiguredGmailTransport(
                account_id, access_token
            )
        )
        self._clients: dict[str, Any] = {}

    def register_client(self, account_id: str, client: GmailClientAdapter) -> None:
        self._clients[account_id] = client

    async def client_for(self, account_id: str) -> Any:
        client = self._clients.get(account_id)
        if client is not None:
            return client

        token = await self._token_store.get(account_id)
        if token is None:
            raise KeyError(f"Gmail account not connected: {account_id}")

        client = self._client_factory.create(account_id, token.access_token)
        self._clients[account_id] = client
        return client
