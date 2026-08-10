import asyncio

import pytest

from app.agent_loop import AgentLoop, ToolCall
from app.tools import ToolDefinition, ToolRegistry


class FakeResponse:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls or []


class FakeModel:
    def __init__(self, responses):
        self.responses = iter(responses)

    async def complete(self, messages, tools):
        return next(self.responses)


@pytest.mark.asyncio
async def test_agent_loop_executes_multiple_calls_and_preserves_order():
    registry = ToolRegistry()

    async def first(args):
        await asyncio.sleep(0.01)
        return {"value": "first"}

    async def second(args):
        return {"value": "second"}

    registry.register(ToolDefinition("first", "first tool", first))
    registry.register(ToolDefinition("second", "second tool", second))

    model = FakeModel([
        FakeResponse(tool_calls=[
            ToolCall("call-1", "first", {}),
            ToolCall("call-2", "second", {}),
        ]),
        FakeResponse(content="done"),
    ])

    content, history = await AgentLoop(model, registry).run([], "user-1")

    assert content == "done"
    assert history[0]["tool_calls"][0]["id"] == "call-1"
    assert history[0]["tool_calls"][1]["id"] == "call-2"
    assert [item["tool_call_id"] for item in history[1:3]] == ["call-1", "call-2"]


@pytest.mark.asyncio
async def test_agent_loop_does_not_hide_tool_failure():
    registry = ToolRegistry()

    async def failing(args):
        raise RuntimeError("boom")

    registry.register(ToolDefinition("failing", "fails", failing))

    model = FakeModel([
        FakeResponse(tool_calls=[ToolCall("call-1", "failing", {})]),
    ])

    with pytest.raises(RuntimeError, match="boom"):
        await AgentLoop(model, registry).run([], "user-1")
