from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_models import SchemaVersion

CURRENT_SCHEMA_VERSION = 2


async def migrate(session: AsyncSession) -> None:
    result = await session.execute(select(SchemaVersion.version).order_by(SchemaVersion.version.desc()).limit(1))
    current = result.scalar_one_or_none() or 0

    if current < CURRENT_SCHEMA_VERSION:
        session.add(SchemaVersion(version=CURRENT_SCHEMA_VERSION))
        await session.commit()
