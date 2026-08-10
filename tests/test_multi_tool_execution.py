import asyncio

import pytest

from app.permissions import AllowListPermissionChecker, PermissionDeniedError
from app.tools import ToolDefinition, ToolRegistry


async def first_tool(arguments):
    return {"tool": "first", "value": arguments["value"]}


async def second_tool(arguments):
    return {"tool": "second", "value": arguments["value"]}


def build_registry() -> ToolRegistry:
    permissions = AllowListPermissionChecker(
        frozenset({"test.first", "test.second"})
    )
    registry = ToolRegistry(permission_checker=permissions)
    registry.register(
        ToolDefinition(
            name="test.first",
            description="first test tool",
            handler=first_tool,
            arguments_model=None,
        )
    )
    registry.register(
        ToolDefinition(
            name="test.second",
            description="second test tool",
            handler=second_tool,
            arguments_model=None,
        )
    )
    return registry


@pytest.mark.asyncio
async def test_registry_executes_multiple_independent_tool_calls() -> None:
    registry = build_registry()

    first, second = await asyncio.gather(
        registry.execute("test.first", {"value": 1}, subject_id="user-1"),
        registry.execute("test.second", {"value": 2}, subject_id="user-1"),
    )

    assert first == {"tool": "first", "value": 1}
    assert second == {"tool": "second", "value": 2}


@pytest.mark.asyncio
async def test_registry_does_not_allow_unapproved_tool_call() -> None:
    registry = build_registry()

    with pytest.raises(PermissionDeniedError, match="permission denied: test.unknown"):
        await registry.execute("test.unknown", {}, subject_id="user-1")
