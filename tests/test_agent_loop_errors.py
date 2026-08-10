import asyncio

from app.agent import Agent, ModelResponse, ToolCall
from app.tools import ToolDefinition, ToolRegistry


class FakeModel:
    async def complete(self, messages, tools):
        return ModelResponse(
            tool_calls=(
                ToolCall(name="ok", arguments={}, call_id="ok"),
                ToolCall(name="bad", arguments={}, call_id="bad"),
            )
        )


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

        agent = Agent(FakeModel(), registry, max_steps=1)
        state = await agent.run("test", "user-1")
        return state, completed.is_set()

    state, completed = asyncio.run(scenario())
    assert completed
    assert any(result.call_id == "bad" and result.error is not None for result in state.tool_results)
    assert any(result.call_id == "ok" and result.error is None for result in state.tool_results)
