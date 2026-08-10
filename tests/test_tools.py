import pytest

from app.tools import ToolDefinition, ToolRegistry


@pytest.mark.asyncio
async def test_registry_registers_lists_and_executes_tool() -> None:
    registry = ToolRegistry()

    async def handler(arguments: dict[str, object]) -> dict[str, object]:
        return {"echo": arguments["value"]}

    registry.register(ToolDefinition("echo", "Echo a value", handler))

    assert registry.names() == ("echo",)
    assert await registry.execute("echo", {"value": "hello"}) == {"echo": "hello"}


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
