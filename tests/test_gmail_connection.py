import pytest

from app.integrations.gmail_connection import GmailConnection
from app.integrations.oauth import InMemoryTokenStore, OAuthToken


class FakeClient:
    async def list_messages(self, max_results=20, query=None):
        return {"max_results": max_results, "query": query}

    async def get_message(self, message_id):
        return {"id": message_id}


@pytest.mark.asyncio
async def test_registered_gmail_client_is_reused() -> None:
    connection = GmailConnection(InMemoryTokenStore())
    client = FakeClient()
    connection.register_client("account-1", client)

    assert await connection.client_for("account-1") is client


@pytest.mark.asyncio
async def test_missing_gmail_account_is_explicit() -> None:
    connection = GmailConnection(InMemoryTokenStore())

    with pytest.raises(KeyError, match="not connected"):
        await connection.client_for("missing")


@pytest.mark.asyncio
async def test_connected_account_without_transport_is_explicit() -> None:
    store = InMemoryTokenStore()
    await store.set("account-1", OAuthToken(access_token="token"))
    connection = GmailConnection(store)

    with pytest.raises(NotImplementedError, match="transport"):
        await connection.client_for("account-1")
