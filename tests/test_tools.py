import pytest

from app.confirmation import ConfirmationRequiredError
from app.permissions import AllowListPermissionChecker, PermissionDeniedError
from app.tools import ToolArgumentError, ToolDefinition, ToolRegistry
from pydantic import BaseModel, Field


class EchoArguments(BaseModel):
    value: str = Field(min_length=1)


@pytest.mark.asyncio
async def test_registry_registers_lists_and_executes_tool() -> None:
    registry = ToolRegistry()

    async def handler(arguments: dict[str, object]) -> dict[str, object]:
        return {"echo": arguments["value"]}

    registry.register(ToolDefinition("echo", "Echo a value", handler))

    assert registry.names() == ("echo",)
    assert await registry.execute("echo", {"value": "hello"}) == {"echo": "hello"}


@pytest.mark.asyncio
async def test_registry_validates_typed_arguments_before_handler() -> None:
    calls: list[dict[str, object]] = []

    async def handler(arguments: dict[str, object]) -> dict[str, object]:
        calls.append(arguments)
        return {"echo": arguments["value"]}

    registry = ToolRegistry()
    registry.register(ToolDefinition("echo", "Echo", handler, EchoArguments))

    assert await registry.execute("echo", {"value": "hello"}) == {"echo": "hello"}

    with pytest.raises(ToolArgumentError, match="value"):
        await registry.execute("echo", {"value": ""})

    assert calls == [{"value": "hello"}]


@pytest.mark.asyncio
async def test_registry_enforces_permissions_before_handler() -> None:
    calls: list[dict[str, object]] = []

    async def handler(arguments: dict[str, object]) -> dict[str, object]:
        calls.append(arguments)
        return {"ok": True}

    permissions = AllowListPermissionChecker(frozenset({"echo"}))
    registry = ToolRegistry(permission_checker=permissions)
    registry.register(ToolDefinition("echo", "Echo", handler))

    assert await registry.execute("echo", {"value": "hello"}, subject_id="account-1") == {"ok": True}
    assert calls == [{"value": "hello"}]

    denied = ToolRegistry(permission_checker=AllowListPermissionChecker(frozenset()))
    denied.register(ToolDefinition("echo", "Echo", handler))

    with pytest.raises(PermissionDeniedError, match="permission denied"):
        await denied.execute("echo", {"value": "secret"}, subject_id="account-1")
    assert calls == [{"value": "hello"}]


@pytest.mark.asyncio
async def test_registry_requires_subject_when_permission_checker_is_configured() -> None:
    async def handler(_: dict[str, object]) -> None:
        return None

    registry = ToolRegistry(
        permission_checker=AllowListPermissionChecker(frozenset({"echo"}))
    )
    registry.register(ToolDefinition("echo", "Echo", handler))

    with pytest.raises(PermissionDeniedError, match="subject_id is required"):
        await registry.execute("echo", {})


@pytest.mark.asyncio
async def test_registry_requires_confirmation_for_sensitive_tool() -> None:
    calls: list[dict[str, object]] = []

    async def handler(arguments: dict[str, object]) -> dict[str, object]:
        calls.append(arguments)
        return {"ok": True}

    registry = ToolRegistry()
    registry.register(ToolDefinition("delete", "Delete data", handler, requires_confirmation=True))

    with pytest.raises(ConfirmationRequiredError, match="confirmation required: delete \(call-1\)"):
        await registry.execute("delete", {"id": "123"}, call_id="call-1")
    assert calls == []

    assert await registry.execute(
        "delete", {"id": "123"}, confirmed=True, call_id="call-1"
    ) == {"ok": True}
    assert calls == [{"id": "123"}]


@pytest.mark.asyncio
async def test_permission_is_checked_before_confirmation() -> None:
    async def handler(_: dict[str, object]) -> None:
        raise AssertionError("handler must not run")

    registry = ToolRegistry(
        permission_checker=AllowListPermissionChecker(frozenset())
    )
    registry.register(ToolDefinition("delete", "Delete", handler, requires_confirmation=True))

    with pytest.raises(PermissionDeniedError, match="permission denied"):
        await registry.execute("delete", {}, subject_id="account-1")


def test_registry_rejects_duplicate_and_blank_names() -> None:
    registry = ToolRegistry()

    async def handler(_: dict[str, object]) -> None:
        return None

    registry.register(ToolDefinition("echo", "Echo", handler))

    with pytest.raises(ValueError, match="tool already registered"):
        registry.register(ToolDefinition("echo", "Duplicate", handler))

    with pytest.raises(ValueError, match="tool name is required"):
        registry.register(ToolDefinition(" ", "Blank", handler))


def test_registry_reports_missing_tool() -> None:
    registry = ToolRegistry()

    with pytest.raises(KeyError, match="tool not found"):
        registry.get("missing")
