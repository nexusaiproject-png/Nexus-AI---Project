from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Awaitable, Callable


class AIExperienceError(RuntimeError):
    pass


@dataclass
class MemoryEntry:
    role: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class WorkspaceMemory:
    def __init__(self) -> None:
        self._items: dict[str, list[MemoryEntry]] = {}

    def add(self, workspace_id: str, role: str, content: str, **metadata: Any) -> MemoryEntry:
        if not workspace_id or not content.strip():
            raise ValueError("workspace_id and content are required")
        entry = MemoryEntry(role=role, content=content, metadata=metadata)
        self._items.setdefault(workspace_id, []).append(entry)
        return entry

    def recent(self, workspace_id: str, limit: int = 20) -> list[MemoryEntry]:
        if limit <= 0:
            return []
        return list(self._items.get(workspace_id, []))[-limit:]


memory = WorkspaceMemory()


@dataclass(frozen=True)
class Confirmation:
    id: str
    tool: str
    arguments: dict[str, Any]
    reason: str


class ConfirmationStore:
    def __init__(self) -> None:
        self._pending: dict[str, Confirmation] = {}

    def request(self, confirmation: Confirmation) -> Confirmation:
        self._pending[confirmation.id] = confirmation
        return confirmation

    def get(self, confirmation_id: str) -> Confirmation | None:
        return self._pending.get(confirmation_id)

    def resolve(self, confirmation_id: str) -> Confirmation:
        item = self._pending.pop(confirmation_id, None)
        if item is None:
            raise AIExperienceError("confirmation not found or already resolved")
        return item


confirmations = ConfirmationStore()


async def stream_text(text: str, chunk_size: int = 32) -> AsyncIterator[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    for start in range(0, len(text), chunk_size):
        await asyncio.sleep(0)
        yield text[start:start + chunk_size]


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, Any]
    requires_confirmation: bool = False
    reason: str = ""


@dataclass
class AgentResult:
    response: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


ToolExecutor = Callable[[str, dict[str, Any]], Awaitable[Any]]


class AIProductAgent:
    def __init__(self, executor: ToolExecutor) -> None:
        self.executor = executor

    async def execute(
        self,
        workspace_id: str,
        user_message: str,
        *,
        context_limit: int = 20,
        tool_calls: list[ToolCall] | None = None,
        approved_confirmation_ids: set[str] | None = None,
    ) -> AgentResult:
        if not workspace_id or not user_message.strip():
            raise ValueError("workspace_id and user_message are required")
        history = memory.recent(workspace_id, context_limit)
        memory.add(workspace_id, "user", user_message)
        result = AgentResult(response=f"Received: {user_message}")
        approved = approved_confirmation_ids or set()
        for call in tool_calls or []:
            if call.requires_confirmation:
                confirmation_id = f"{workspace_id}:{len(history)}:{call.name}"
                if confirmation_id not in approved:
                    confirmations.request(Confirmation(confirmation_id, call.name, call.arguments, call.reason or "confirmation required"))
                    result.tool_calls.append(call)
                    continue
                confirmations.resolve(confirmation_id)
            try:
                await self.executor(call.name, call.arguments)
                result.tool_calls.append(call)
            except Exception as exc:
                result.errors.append(f"tool {call.name} failed: {exc}")
        memory.add(workspace_id, "assistant", result.response, context_size=len(history) + 1)
        return result
