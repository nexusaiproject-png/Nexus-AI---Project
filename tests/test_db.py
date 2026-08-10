import asyncio

from app.db import Database


def test_database_creates_schema(tmp_path):
    async def scenario():
        database = Database(tmp_path / "nexus.db")
        database.initialize()
        with database.connect() as connection:
            row = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
            ).fetchone()
            return row is not None

    assert asyncio.run(scenario())
