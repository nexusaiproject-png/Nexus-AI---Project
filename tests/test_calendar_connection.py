import pytest

from app.integrations.calendar_client import CalendarClientAdapter
from app.integrations.calendar_connection import CalendarConnection
from app.integrations.oauth import InMemoryTokenStore, OAuthToken


class FakeTransport:
    async def list_events(self, calendar_id, max_results, time_min, time_max):
        return []
    async def get_event(self, calendar_id, event_id):
        return {}
    async def create_event(self, calendar_id, event):
        return event
    async def update_event(self, calendar_id, event_id, event):
        return event
    async def delete_event(self, calendar_id, event_id):
        return None


class FakeFactory:
    def create(self, account_id, access_token):
        assert account_id == "account-1"
        assert access_token == "token"
        return CalendarClientAdapter(FakeTransport())


@pytest.mark.asyncio
async def test_calendar_connection_uses_token_store():
    store = InMemoryTokenStore()
    await store.set("account-1", OAuthToken("token"))
    connection = CalendarConnection(store, FakeFactory())
    client = await connection.client_for("account-1")
    assert isinstance(client, CalendarClientAdapter)


@pytest.mark.asyncio
async def test_calendar_connection_rejects_unknown_account():
    connection = CalendarConnection(InMemoryTokenStore(), FakeFactory())
    with pytest.raises(KeyError, match="Calendar account not connected"):
        await connection.client_for("missing")
