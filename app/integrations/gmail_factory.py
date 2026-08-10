from typing import Any, Callable

from app.integrations.gmail_client import GmailClientAdapter, GmailTransport


class GmailClientFactory:
    def __init__(self, transport_factory: Callable[[str, str], GmailTransport]) -> None:
        self._transport_factory = transport_factory

    def create(self, account_id: str, access_token: str) -> GmailClientAdapter:
        transport = self._transport_factory(account_id, access_token)
        return GmailClientAdapter(transport)
