import asyncio

from app.agent import Agent, ModelResponse, ToolCall
from app.tools import ToolDefinition, ToolRegistry


def test_model_can_recover_after_tool_failure_without_pytest_asyncio():
    async def scenario():
        registry = ToolRegistry()

        async def bad(arguments):
            raise RuntimeError("temporary failure")

        async def ok(arguments):
            return {"ok": True}

        registry.register(ToolDefinition("bad", "bad", bad))
        registry.register(ToolDefinition("ok", "ok", ok))

        class RecoveryModel:
            def __init__(self):
                self.calls = 0

            async def complete(self, messages, tools):
                self.calls += 1
                if self.calls == 1:
                    return ModelResponse(tool_calls=(
                        ToolCall("bad", {}, "bad-1"),
                        ToolCall("ok", {}, "ok-1"),
                    ))
                return ModelResponse(content="recovered")

        model = RecoveryModel()
        state = await Agent(model, registry, max_steps=2).run("test", "user-1")
        return state

    state = asyncio.run(scenario())
    assert state.messages[-1] == {"role": "assistant", "content": "recovered"}
    assert any(result.call_id == "bad-1" and result.error is not None for result in state.tool_results)
    assert any(result.call_id == "ok-1" and result.error is None for result in state.tool_results)
