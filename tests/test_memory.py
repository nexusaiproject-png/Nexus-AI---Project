import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db_models import Base
from app.memory import MemoryStore


def test_memory_round_trip_and_subject_isolation():
    async def scenario():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        sessions = async_sessionmaker(engine, expire_on_commit=False)
        async with sessions() as session:
            store = MemoryStore(session)
            await store.add("user-1", "user", "hello")
            await store.add("user-1", "assistant", "hi there")
            await store.add("user-2", "user", "other")
            await session.commit()

            memories = await store.recent("user-1", limit=10)
            assert [(item.role, item.content) for item in memories] == [
                ("user", "hello"),
                ("assistant", "hi there"),
            ]
            assert all(item.subject_id == "user-1" for item in memories)

        await engine.dispose()

    asyncio.run(scenario())


def test_memory_validates_inputs():
    async def scenario():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        sessions = async_sessionmaker(engine, expire_on_commit=False)
        async with sessions() as session:
            store = MemoryStore(session)
            for args in [("", "user", "x"), ("u", "", "x"), ("u", "user", "")]:
                try:
                    await store.add(*args)
                except ValueError:
                    pass
                else:
                    raise AssertionError("invalid memory input was accepted")
            try:
                await store.recent("u", 0)
            except ValueError:
                pass
            else:
                raise AssertionError("invalid memory limit was accepted")
        await engine.dispose()

    asyncio.run(scenario())
