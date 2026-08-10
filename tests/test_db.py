import asyncio

from sqlalchemy import text

from app.db import engine, init_db


def test_database_creates_schema():
    async def scenario():
        await init_db()
        async with engine.connect() as connection:
            result = await connection.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'")
            )
            return result.scalar_one_or_none()

    assert asyncio.run(scenario()) == "schema_version"
