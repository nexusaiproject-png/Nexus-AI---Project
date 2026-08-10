import pytest

from app.permissions import AllowListPermissionChecker
from app.schemas import GmailListMessagesArguments
from app.tools import ToolArgumentError, ToolDefinition, ToolRegistry


@pytest.mark.asyncio
async def test_registry_validates_tool_arguments_before_handler() -> None:
    calls: list[dict[str, object]] = []

    async def handler(arguments: dict[str, object]) -> dict[str, object]:
        calls.append(arguments)
        return arguments

    registry = ToolRegistry(AllowListPermissionChecker(frozenset({"gmail.list_messages"})))
    registry.register(
        ToolDefinition(
            "gmail.list_messages",
            "List messages",
            handler,
            arguments_model=GmailListMessagesArguments,
        )
    )

    result = await registry.execute(
        "gmail.list_messages",
        {"account_id": "account-1", "max_results": 5},
        subject_id="account-1",
    )

    assert result == {"account_id": "account-1", "max_results": 5, "query": None}
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_invalid_tool_arguments_never_reach_handler() -> None:
    calls: list[dict[str, object]] = []

    async def handler(arguments: dict[str, object]) -> None:
        calls.append(arguments)

    registry = ToolRegistry(AllowListPermissionChecker(frozenset({"gmail.list_messages"})))
    registry.register(
        ToolDefinition(
            "gmail.list_messages",
            "List messages",
            handler,
            arguments_model=GmailListMessagesArguments,
        )
    )

    with pytest.raises(ToolArgumentError):
        await registry.execute(
            "gmail.list_messages",
            {"account_id": "", "max_results": 500},
            subject_id="account-1",
        )

    assert calls == []
