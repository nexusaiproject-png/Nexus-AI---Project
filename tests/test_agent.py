import asyncio

from app.agent import Agent, ModelResponse, ToolCall
from app.permissions import AllowListPermissionChecker
from app.tools import ToolDefinition, ToolRegistry


class FakeModel:
    def __init__(self) -> None:
        self.calls = 0

    async def complete(self, messages, tools):
        self.calls += 1
        if self.calls == 1:
            return ModelResponse(
                tool_calls=(
                    ToolCall("test.first", {"value": 1}, "call-1"),
                    ToolCall("test.second", {"value": 2}, "call-2"),
                )
            )
        return ModelResponse(content="done")


async def first(arguments):
    return {"value": arguments["value"], "name": "first"}


async def second(arguments):
    return {"value": arguments["value"], "name": "second"}


def registry() -> ToolRegistry:
    checker = AllowListPermissionChecker(frozenset({"test.first", "test.second"}))
    tools = ToolRegistry(permission_checker=checker)
    tools.register(ToolDefinition("test.first", "first", first))
    tools.register(ToolDefinition("test.second", "second", second))
    return tools


def test_agent_executes_all_tool_calls_from_one_model_response():
    async def scenario():
        return await Agent(FakeModel(), registry()).run("do both", "user-1")

    result = asyncio.run(scenario())

    assert [item.name for item in result.tool_results] == ["test.first", "test.second"]
    assert result.tool_results[0].result == {"value": 1, "name": "first"}
    assert result.tool_results[1].result == {"value": 2, "name": "second"}
    assert result.messages[-1] == {"role": "assistant", "content": "done"}
