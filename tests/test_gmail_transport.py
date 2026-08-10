import pytest

from app.integrations.gmail_transport import UnconfiguredGmailTransport


@pytest.mark.asyncio
async def test_unconfigured_transport_fails_explicitly() -> None:
    transport = UnconfiguredGmailTransport("account-1", "token-1")

    with pytest.raises(NotImplementedError, match="not configured"):
        await transport.list_messages(20, None)

    with pytest.raises(NotImplementedError, match="not configured"):
        await transport.get_message("message-1")
