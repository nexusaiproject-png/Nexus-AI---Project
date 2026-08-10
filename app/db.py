from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.db_models import Base
from app.migrations import migrate

settings = get_settings()

# SQLite does not create missing parent directories for a database file.
# Ensure the local database directory exists before SQLAlchemy opens the engine.
if settings.database_url.startswith("sqlite+aiosqlite:///./"):
    Path(settings.database_url.removeprefix("sqlite+aiosqlite:///./")).parent.mkdir(
        parents=True,
        exist_ok=True,
    )

engine = create_async_engine(settings.database_url, future=True)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        await migrate(session)


async def close_db() -> None:
    await engine.dispose()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
