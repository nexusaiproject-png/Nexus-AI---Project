import asyncio

import pytest

from app.agent_loop import AgentLoop, ToolCall
from app.tools import ToolDefinition, ToolRegistry


class FakeModel:
    async def complete(self, messages, tools):
        return type(
            "Response",
            (),
            {
                "content": None,
                "tool_calls": [
                    type("Call", (), {"call_id": "ok", "name": "ok", "arguments": {}})(),
                    type("Call", (), {"call_id": "bad", "name": "bad", "arguments": {}})(),
                ],
            },
        )()


@pytest.mark.asyncio
async def test_one_tool_failure_does_not_cancel_other_tool():
    registry = ToolRegistry()
    completed = asyncio.Event()

    async def ok(arguments):
        await asyncio.sleep(0)
        completed.set()
        return {"ok": True}

    async def bad(arguments):
        raise RuntimeError("boom")

    registry.register(ToolDefinition("ok", "ok", ok))
    registry.register(ToolDefinition("bad", "bad", bad))

    agent = AgentLoop(FakeModel(), registry)

    with pytest.raises(RuntimeError, match="boom"):
        await agent.run([], "user-1")

    assert completed.is_set()
