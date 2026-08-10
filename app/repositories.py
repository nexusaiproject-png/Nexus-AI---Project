from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_models import SchemaVersion


class SchemaVersionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_current(self) -> SchemaVersion | None:
        result = await self.session.execute(
            select(SchemaVersion).order_by(SchemaVersion.version.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def record(self, version: int) -> SchemaVersion:
        row = SchemaVersion(version=version)
        self.session.add(row)
        await self.session.flush()
        return row
