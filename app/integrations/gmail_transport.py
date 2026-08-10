from typing import Any

from app.integrations.gmail_client import GmailTransport


class UnconfiguredGmailTransport(GmailTransport):
    def __init__(self, account_id: str, access_token: str) -> None:
        self.account_id = account_id
        self.access_token = access_token

    async def list_messages(self, max_results: int, query: str | None) -> Any:
        raise NotImplementedError("Gmail API transport is not configured")

    async def get_message(self, message_id: str) -> Any:
        raise NotImplementedError("Gmail API transport is not configured")
