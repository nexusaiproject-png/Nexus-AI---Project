import pytest

from app.gmail_tools import GmailToolFactory


class FakeClient:
    async def list_messages(self, max_results: int = 20, query: str | None = None):
        return {"max_results": max_results, "query": query}

    async def get_message(self, message_id: str):
        return {"message_id": message_id}


class FakeConnection:
    async def client_for(self, account_id: str):
        assert account_id == "account-1"
        return FakeClient()


@pytest.mark.asyncio
async def test_gmail_tool_definitions_have_expected_names() -> None:
    factory = GmailToolFactory(FakeConnection())

    assert tuple(tool.name for tool in factory.definitions()) == (
        "gmail.list_messages",
        "gmail.get_message",
    )


@pytest.mark.asyncio
async def test_list_messages_maps_tool_arguments() -> None:
    factory = GmailToolFactory(FakeConnection())

    result = await factory.list_messages(
        {"account_id": "account-1", "max_results": 5, "query": "is:unread"}
    )

    assert result == {"max_results": 5, "query": "is:unread"}


@pytest.mark.asyncio
async def test_get_message_maps_tool_arguments() -> None:
    factory = GmailToolFactory(FakeConnection())

    result = await factory.get_message(
        {"account_id": "account-1", "message_id": "msg-123"}
    )

    assert result == {"message_id": "msg-123"}
