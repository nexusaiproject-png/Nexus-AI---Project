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


class MemoryFake:
    def __init__(self) -> None:
        self.items = []

    async def add(self, subject_id, role, content):
        self.items.append((subject_id, role, content))

    async def recent(self, subject_id, limit):
        return [
            type("Memory", (), {"role": role, "content": content})()
            for stored_subject, role, content in self.items[-limit:]
            if stored_subject == subject_id
        ]


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


def test_agent_loads_and_persists_memory():
    async def scenario():
        memory = MemoryFake()
        await memory.add("user-1", "user", "remember this")
        agent = Agent(FakeModel(), registry(), memory=memory, memory_limit=10)
        result = await agent.run("continue", "user-1")
        return result, memory

    result, memory = asyncio.run(scenario())

    assert result.messages[0] == {"role": "user", "content": "remember this"}
    assert ("user-1", "user", "continue") in memory.items
    assert ("user-1", "assistant", "done") in memory.items


def test_agent_memory_isolated_by_subject():
    async def scenario():
        memory = MemoryFake()
        await memory.add("user-1", "user", "private context")
        agent = Agent(FakeModel(), registry(), memory=memory)
        result = await agent.run("continue", "user-2")
        return result

    result = asyncio.run(scenario())

    assert {message["content"] for message in result.messages if message["role"] == "user"} == {"continue"}
