import pytest

from app.ai_experience import AIProductAgent, Confirmation, confirmations, memory, stream_text


@pytest.mark.asyncio
async def test_streaming_and_workspace_memory():
    chunks = [chunk async for chunk in stream_text("hello world", chunk_size=5)]
    assert "".join(chunks) == "hello world"
    memory.add("w1", "user", "remember this")
    memory.add("w2", "user", "private")
    assert [item.content for item in memory.recent("w1")] == ["remember this"]
    assert memory.recent("w2")[0].content == "private"


@pytest.mark.asyncio
async def test_agent_tool_execution_and_error_recovery():
    calls = []

    async def execute(name, arguments):
        calls.append((name, arguments))
        if name == "broken":
            raise RuntimeError("boom")

    agent = AIProductAgent(execute)
    result = await agent.execute("w1", "do work", tool_calls=[
        __import__("app.ai_experience", fromlist=["ToolCall"]).ToolCall("ok", {"x": 1}),
        __import__("app.ai_experience", fromlist=["ToolCall"]).ToolCall("broken", {}),
    ])
    assert calls == [("ok", {"x": 1}), ("broken", {})]
    assert result.errors == ["tool broken failed: boom"]


@pytest.mark.asyncio
async def test_confirmation_is_required_before_sensitive_tool():
    async def execute(name, arguments):
        return {"ok": True}

    agent = AIProductAgent(execute)
    from app.ai_experience import ToolCall
    call = ToolCall("delete_file", {"path": "x"}, requires_confirmation=True, reason="destructive action")
    first = await agent.execute("w-confirm", "delete x", tool_calls=[call])
    assert first.tool_calls == [call]
    assert confirmations.get("w-confirm:0:delete_file") is not None
