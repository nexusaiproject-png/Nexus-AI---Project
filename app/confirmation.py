from __future__ import annotations

from typing import FrozenSet


class ConfirmationRequiredError(PermissionError):
    """Raised when a sensitive tool call has not been explicitly confirmed."""

    def __init__(self, tool_name: str, confirmation_id: str) -> None:
        self.tool_name = tool_name
        self.confirmation_id = confirmation_id
        super().__init__(
            f"confirmation required: {tool_name} ({confirmation_id})"
        )


def confirmation_id(tool_name: str, call_id: str | None = None) -> str:
    """Return a stable caller-visible identifier for a tool confirmation."""
    return call_id or tool_name


class ConfirmationSet:
    """Immutable set of explicitly approved confirmation ids for one agent run."""

    def __init__(self, approved: FrozenSet[str] | None = None) -> None:
        self._approved = approved or frozenset()

    def allows(self, confirmation_key: str) -> bool:
        return confirmation_key in self._approved
