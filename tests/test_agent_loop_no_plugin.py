import asyncio

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
        return type("Response", (), {"content": "recovered", "tool_calls": []})()


def test_model_can_recover_after_tool_failure_without_pytest_asyncio():
    async def scenario():
        registry = ToolRegistry()

        async def bad(arguments):
            raise RuntimeError("temporary failure")

        async def ok(arguments):
            return {"ok": True}

        registry.register(ToolDefinition("bad", "bad", bad))
        registry.register(ToolDefinition("ok", "ok", ok))

        model = RecoveryModel()
        agent = AgentLoop(model, registry, max_steps=2)
        return await agent.run([], "user-1")

    content, history = asyncio.run(scenario())

    assert content == "recovered"
    assert any(message.get("tool_call_id") == "bad-1" for message in history)
    assert any(message.get("tool_call_id") == "ok-1" for message in history)
