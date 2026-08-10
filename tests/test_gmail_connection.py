import pytest

from app.integrations.gmail_connection import GmailConnection
from app.integrations.gmail_factory import GmailClientFactory
from app.integrations.oauth import InMemoryTokenStore, OAuthToken


class FakeClient:
    async def list_messages(self, max_results=20, query=None):
        return {"max_results": max_results, "query": query}

    async def get_message(self, message_id):
        return {"id": message_id}


class FakeTransport:
    async def list_messages(self, max_results, query):
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
async def test_connected_account_builds_client_from_token() -> None:
    store = InMemoryTokenStore()
    await store.set("account-1", OAuthToken(access_token="token"))
    factory = GmailClientFactory(lambda account_id, access_token: FakeTransport())
    connection = GmailConnection(store, client_factory=factory)

    client = await connection.client_for("account-1")
    assert await client.get_message("message-1") == {"id": "message-1"}
    assert await connection.client_for("account-1") is client
