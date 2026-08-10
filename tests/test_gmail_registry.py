import pytest

from app.gmail_registry import GMAIL_TOOL_NAMES, build_gmail_registry
from app.gmail_tools import GmailToolFactory
from app.permissions import AllowListPermissionChecker, PermissionDeniedError


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
async def test_gmail_registry_registers_expected_tools() -> None:
    factory = GmailToolFactory(FakeConnection())
    permissions = AllowListPermissionChecker(GMAIL_TOOL_NAMES)
    registry = build_gmail_registry(factory, permissions)

    assert registry.names() == tuple(sorted(GMAIL_TOOL_NAMES))


@pytest.mark.asyncio
async def test_gmail_registry_enforces_tool_specific_permission() -> None:
    factory = GmailToolFactory(FakeConnection())
    permissions = AllowListPermissionChecker(frozenset({"gmail.list_messages"}))
    registry = build_gmail_registry(factory, permissions)

    assert await registry.execute(
        "gmail.list_messages",
        {"account_id": "account-1", "max_results": 3},
        subject_id="account-1",
    ) == {"max_results": 3, "query": None}

    with pytest.raises(PermissionDeniedError, match="gmail.get_message"):
        await registry.execute(
            "gmail.get_message",
            {"account_id": "account-1", "message_id": "msg-1"},
            subject_id="account-1",
        )
