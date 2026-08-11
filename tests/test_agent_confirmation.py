import pytest

from app.agent import Agent, ModelResponse, ToolCall
from app.confirmation import ConfirmationRequiredError
from app.permissions import AllowListPermissionChecker
from app.tools import ToolDefinition, ToolRegistry


class OneToolModel:
    def __init__(self) -> None:
        self.calls = 0

    async def complete(self, messages, tools):
        self.calls += 1
        if self.calls == 1:
            return ModelResponse(tool_calls=(ToolCall("delete", {"id": "123"}, "call-1"),))
        return ModelResponse(content="done")


@pytest.mark.asyncio
async def test_agent_does_not_execute_sensitive_tool_without_confirmation() -> None:
    executed: list[dict[str, object]] = []

    async def delete(arguments: dict[str, object]) -> dict[str, object]:
        executed.append(arguments)
        return {"deleted": True}

    registry = ToolRegistry(
        permission_checker=AllowListPermissionChecker(frozenset({"delete"}))
    )
    registry.register(ToolDefinition("delete", "Delete data", delete, requires_confirmation=True))

    state = await Agent(OneToolModel(), registry, max_steps=2).run(
        "delete item 123",
        "account-1",
    )

    assert executed == []
    assert len(state.tool_results) == 1
    assert isinstance(state.tool_results[0].error, Exception)
    assert "confirmation required" in str(state.tool_results[0].error)


@pytest.mark.asyncio
async def test_agent_executes_sensitive_tool_after_explicit_confirmation() -> None:
    executed: list[dict[str, object]] = []

    async def delete(arguments: dict[str, object]) -> dict[str, object]:
        executed.append(arguments)
        return {"deleted": True}

    registry = ToolRegistry(
        permission_checker=AllowListPermissionChecker(frozenset({"delete"}))
    )
    registry.register(ToolDefinition("delete", "Delete data", delete, requires_confirmation=True))

    state = await Agent(OneToolModel(), registry, max_steps=2).run(
        "delete item 123",
        "account-1",
        confirmed_tool_calls=frozenset({"call-1"}),
    )

    assert executed == [{"id": "123"}]
    assert state.tool_results[0].result == {"deleted": True}
