import pytest

from app.integrations.oauth import InMemoryTokenStore, OAuthToken


@pytest.mark.asyncio
async def test_token_store_round_trip_and_delete() -> None:
    store = InMemoryTokenStore()
    token = OAuthToken(access_token="access", refresh_token="refresh")

    assert await store.get("account-1") is None
    await store.set("account-1", token)
    assert await store.get("account-1") == token

    await store.delete("account-1")
    assert await store.get("account-1") is None
