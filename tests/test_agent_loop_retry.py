import pytest

from app.agent_loop import AgentLoop
from app.tools import ToolDefinition, ToolRegistry


class RecoveryModel:
    def __init__(self):
        self.calls = 0

    async def complete(self, messages, tools):
        self.calls += 1
        if self.calls == 1:
            return type("Response", (), {
                "content": None,
                "tool_calls": [
                    type("Call", (), {"call_id": "bad-1", "name": "bad", "arguments": {}})(),
                    type("Call", (), {"call_id": "ok-1", "name": "ok", "arguments": {}})(),
                ],
            })()
        assert any(
            message.get("tool_call_id") == "bad-1"
            and message.get("content", {}).get("error") == "RuntimeError"
            for message in messages
            if message.get("role") == "tool"
        )
        return type("Response", (), {"content": "recovered", "tool_calls": []})()


@pytest.mark.asyncio
async def test_model_can_recover_after_tool_failure():
    registry = ToolRegistry()

    async def bad(arguments):
        raise RuntimeError("temporary failure")

    async def ok(arguments):
        return {"ok": True}

    registry.register(ToolDefinition("bad", "bad", bad))
    registry.register(ToolDefinition("ok", "ok", ok))

    model = RecoveryModel()
    agent = AgentLoop(model, registry, max_steps=2)

    content, history = await agent.run([], "user-1")

    assert content == "recovered"
    assert model.calls == 2
    assert any(message.get("tool_call_id") == "bad-1" for message in history)
    assert any(message.get("tool_call_id") == "ok-1" for message in history)
