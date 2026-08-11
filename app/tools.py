from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from pydantic import BaseModel, ValidationError

from app.confirmation import ConfirmationRequiredError, confirmation_id
from app.permissions import PermissionChecker, PermissionDeniedError


ToolHandler = Callable[[dict[str, Any]], Awaitable[Any]]


class ToolArgumentError(ValueError):
    pass


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    handler: ToolHandler
    arguments_model: type[BaseModel] | None = None
    requires_confirmation: bool = False


class ToolRegistry:
    def __init__(self, permission_checker: PermissionChecker | None = None) -> None:
        self._tools: dict[str, ToolDefinition] = {}
        self._permission_checker = permission_checker

    def register(self, tool: ToolDefinition) -> None:
        if not tool.name.strip():
            raise ValueError("tool name is required")
        if tool.name in self._tools:
            raise ValueError(f"tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"tool not found: {name}") from exc

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._tools))

    async def execute(
        self,
        name: str,
        arguments: dict[str, Any],
        subject_id: str | None = None,
        *,
        confirmed: bool = False,
        call_id: str | None = None,
    ) -> Any:
        if self._permission_checker is not None:
            if subject_id is None:
                raise PermissionDeniedError("subject_id is required for permission checks")
            if not await self._permission_checker.allowed(name, subject_id):
                raise PermissionDeniedError(f"permission denied: {name}")

        tool = self.get(name)
        if tool.requires_confirmation and not confirmed:
            raise ConfirmationRequiredError(name, confirmation_id(name, call_id))

        if tool.arguments_model is not None:
            try:
                arguments = tool.arguments_model.model_validate(arguments).model_dump()
            except ValidationError as exc:
                raise ToolArgumentError(str(exc)) from exc

        return await tool.handler(arguments)
