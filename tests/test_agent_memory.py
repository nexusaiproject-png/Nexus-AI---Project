import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.agent import Agent, ModelResponse
from app.db_models import Base
from app.memory import MemoryStore
from app.permissions import AllowListPermissionChecker
from app.tools import ToolRegistry


class FakeModel:
    async def complete(self, messages, tools):
        assert messages[-1] == {"role": "user", "content": "continue"}
        return ModelResponse(content="done")


def test_agent_persists_user_and_assistant_messages():
    async def scenario():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        sessions = async_sessionmaker(engine, expire_on_commit=False)
        async with sessions() as session:
            memory = MemoryStore(session)
            agent = Agent(
                FakeModel(),
                ToolRegistry(permission_checker=AllowListPermissionChecker(frozenset())),
                memory=memory,
            )
            result = await agent.run("continue", "user-1")
            await session.commit()
            entries = await memory.recent("user-1", 10)

        await engine.dispose()
        return result, entries

    result, entries = asyncio.run(scenario())

    assert result.messages[-1] == {"role": "assistant", "content": "done"}
    assert [(item.role, item.content) for item in entries] == [
        ("user", "continue"),
        ("assistant", "done"),
    ]


def test_agent_memory_isolated_by_subject():
    async def scenario():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        sessions = async_sessionmaker(engine, expire_on_commit=False)
        async with sessions() as session:
            memory = MemoryStore(session)
            agent = Agent(
                FakeModel(),
                ToolRegistry(permission_checker=AllowListPermissionChecker(frozenset())),
                memory=memory,
            )
            await memory.add("user-1", "user", "private context")
            result = await agent.run("continue", "user-2")

        await engine.dispose()
        return result

    result = asyncio.run(scenario())
    assert [m["content"] for m in result.messages if m["role"] == "user"] == ["continue"]
