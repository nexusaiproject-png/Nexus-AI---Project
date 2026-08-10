import pytest

from app.tools import ToolDefinition, ToolRegistry


def test_registry_rejects_duplicate_tools():
    registry = ToolRegistry()

    async def handler(arguments):
        return arguments

    registry.register(ToolDefinition("dummy", "A dummy tool", handler))
    with pytest.raises(ValueError, match="tool already registered"):
        registry.register(ToolDefinition("dummy", "Duplicate", handler))


def test_registry_rejects_blank_names():
    registry = ToolRegistry()

    async def handler(arguments):
        return arguments

    with pytest.raises(ValueError, match="tool name is required"):
        registry.register(ToolDefinition(" ", "Blank", handler))
