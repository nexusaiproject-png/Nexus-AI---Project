import pytest

from app.tools.registry import ToolRegistry


class DummyTool:
    name = "dummy"
    description = "A dummy tool"

    def schema(self):
        return {
            "type": "object",
            "properties": {"value": {"type": "string"}},
            "required": ["value"],
            "additionalProperties": False,
        }

    async def execute(self, arguments, context):
        return arguments["value"]


def test_registry_describe_returns_provider_ready_schema():
    registry = ToolRegistry()
    registry.register(DummyTool())

    assert registry.describe() == [
        {
            "name": "dummy",
            "description": "A dummy tool",
            "parameters": {
                "type": "object",
                "properties": {"value": {"type": "string"}},
                "required": ["value"],
                "additionalProperties": False,
            },
        }
    ]


def test_registry_rejects_duplicate_tools():
    registry = ToolRegistry()
    registry.register(DummyTool())

    with pytest.raises(ValueError, match="Tool already registered: dummy"):
        registry.register(DummyTool())
