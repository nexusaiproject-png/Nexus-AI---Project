from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_models import ToolPermission


class ToolPermissionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def is_allowed(self, subject_id: str, tool_name: str) -> bool:
        result = await self.session.execute(
            select(ToolPermission.allowed).where(
                ToolPermission.subject_id == subject_id,
                ToolPermission.tool_name == tool_name,
            )
        )
        allowed = result.scalar_one_or_none()
        return bool(allowed) if allowed is not None else False

    async def set_permission(self, subject_id: str, tool_name: str, allowed: bool) -> ToolPermission:
        result = await self.session.execute(
            select(ToolPermission).where(
                ToolPermission.subject_id == subject_id,
                ToolPermission.tool_name == tool_name,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = ToolPermission(subject_id=subject_id, tool_name=tool_name, allowed=allowed)
            self.session.add(row)
        else:
            row.allowed = allowed
        await self.session.flush()
        return row
