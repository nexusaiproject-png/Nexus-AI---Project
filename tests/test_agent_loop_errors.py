import asyncio

from app.agent_loop import AgentLoop
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


def test_one_tool_failure_does_not_cancel_other_tool():
    async def scenario():
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
        content, history = await agent.run([], "user-1")
        return content, history, completed.is_set()

    content, history, completed = asyncio.run(scenario())
    assert completed
    assert any(message.get("tool_call_id") == "bad" for message in history)
    assert any(message.get("tool_call_id") == "ok" for message in history)
