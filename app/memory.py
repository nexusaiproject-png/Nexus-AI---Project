from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, String, Text, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.db_models import Base


class MemoryEntry(Base):
    __tablename__ = "memory_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )


@dataclass(frozen=True)
class Memory:
    id: int
    subject_id: str
    role: str
    content: str
    created_at: datetime


class MemoryStore:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, subject_id: str, role: str, content: str) -> Memory:
        if not subject_id.strip():
            raise ValueError("subject_id is required")
        if not role.strip() or not content.strip():
            raise ValueError("role and content are required")

        entry = MemoryEntry(subject_id=subject_id, role=role, content=content)
        self.session.add(entry)
        await self.session.flush()
        await self.session.refresh(entry)
        return self._to_memory(entry)

    async def recent(self, subject_id: str, limit: int = 20) -> list[Memory]:
        if not subject_id.strip():
            raise ValueError("subject_id is required")
        if limit < 1:
            raise ValueError("limit must be positive")

        result = await self.session.execute(
            select(MemoryEntry)
            .where(MemoryEntry.subject_id == subject_id)
            .order_by(MemoryEntry.created_at.desc(), MemoryEntry.id.desc())
            .limit(limit)
        )
        entries = list(result.scalars())
        entries.reverse()
        return [self._to_memory(entry) for entry in entries]

    @staticmethod
    def _to_memory(entry: MemoryEntry) -> Memory:
        return Memory(
            id=entry.id,
            subject_id=entry.subject_id,
            role=entry.role,
            content=entry.content,
            created_at=entry.created_at,
        )
