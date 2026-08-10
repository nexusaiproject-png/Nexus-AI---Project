import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db_models import Base, SchemaVersion, ToolPermission
from app.migrations import CURRENT_SCHEMA_VERSION, migrate
from app.permission_repository import ToolPermissionRepository


def test_database_migration_and_permission_persistence():
    async def scenario():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        sessions = async_sessionmaker(engine, expire_on_commit=False)

        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with sessions() as session:
            await migrate(session)
            version = await session.scalar(select(SchemaVersion.version))
            assert version == CURRENT_SCHEMA_VERSION

            permissions = ToolPermissionRepository(session)
            assert not await permissions.is_allowed("user-1", "tool.read")

            await permissions.set_permission("user-1", "tool.read", True)
            await session.commit()
            assert await permissions.is_allowed("user-1", "tool.read")

            await permissions.set_permission("user-1", "tool.read", False)
            await session.commit()
            assert not await permissions.is_allowed("user-1", "tool.read")

        await engine.dispose()

    asyncio.run(scenario())
