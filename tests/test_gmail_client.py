import pytest

from app.integrations.gmail_client import GmailClientAdapter


class FakeTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    async def list_messages(self, max_results: int, query: str | None):
        self.calls.append(("list", (max_results, query)))
        return ["message-1"]

    async def get_message(self, message_id: str):
        self.calls.append(("get", message_id))
        return {"id": message_id}


@pytest.mark.asyncio
async def test_gmail_client_adapter_delegates_to_transport() -> None:
    transport = FakeTransport()
    client = GmailClientAdapter(transport)

    assert await client.list_messages(10, "is:unread") == ["message-1"]
    assert await client.get_message("message-1") == {"id": "message-1"}
    assert transport.calls == [
        ("list", (10, "is:unread")),
        ("get", "message-1"),
    ]
