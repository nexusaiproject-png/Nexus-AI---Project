import pytest

from app.integrations.gmail_auth import GmailAccount, GmailAuthService
from app.integrations.oauth import InMemoryTokenStore


@pytest.mark.asyncio
async def test_gmail_auth_connect_and_disconnect() -> None:
    service = GmailAuthService(InMemoryTokenStore())
    account = GmailAccount("account-1", "user@example.com")

    assert await service.is_connected(account.account_id) is False

    await service.connect(account, "token-1")
    assert await service.is_connected(account.account_id) is True

    await service.disconnect(account.account_id)
    assert await service.is_connected(account.account_id) is False
