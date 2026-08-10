from dataclasses import dataclass
from typing import Protocol


class PermissionChecker(Protocol):
    async def allowed(self, tool_name: str, subject_id: str) -> bool: ...


@dataclass(frozen=True)
class AllowListPermissionChecker:
    allowed_tools: frozenset[str]

    async def allowed(self, tool_name: str, subject_id: str) -> bool:
        return bool(subject_id.strip()) and tool_name in self.allowed_tools


class PermissionDeniedError(PermissionError):
    pass
