import asyncio

from app.agent import Agent, ModelResponse, ToolCall
from app.tools import ToolDefinition, ToolRegistry


class FakeModel:
    async def complete(self, messages, tools):
        return ModelResponse(
            tool_calls=(
                ToolCall(name="first", arguments={}, call_id="call-1"),
                ToolCall(name="second", arguments={}, call_id="call-2"),
            )
        )


def test_agent_executes_multiple_calls_and_preserves_order():
    async def scenario():
        registry = ToolRegistry()

        async def first(arguments):
            await asyncio.sleep(0.01)
            return {"value": "first"}

        async def second(arguments):
            return {"value": "second"}

        registry.register(ToolDefinition("first", "first tool", first))
        registry.register(ToolDefinition("second", "second tool", second))
        return await Agent(FakeModel(), registry, max_steps=1).run("test", "user-1")

    state = asyncio.run(scenario())
    assert [result.call_id for result in state.tool_results] == ["call-1", "call-2"]
    assert state.tool_results[0].result == {"value": "first"}
    assert state.tool_results[1].result == {"value": "second"}


def test_agent_returns_tool_failure_as_structured_result():
    async def scenario():
        registry = ToolRegistry()

        async def failing(arguments):
            raise RuntimeError("boom")

        registry.register(ToolDefinition("failing", "fails", failing))
        return await Agent(
            ModelResponseModel(), registry, max_steps=1
        ).run("test", "user-1")

    state = asyncio.run(scenario())
    assert state.tool_results[0].error is not None
    assert state.tool_results[0].error.error_type == "RuntimeError"


class ModelResponseModel:
    async def complete(self, messages, tools):
        return ModelResponse(
            tool_calls=(ToolCall(name="failing", arguments={}, call_id="call-1"),)
        )
