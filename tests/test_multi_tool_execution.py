from app.permissions import AllowListPermissionChecker
from app.tools import ToolDefinition, ToolRegistry


async def first_tool(arguments):
    return {"tool": "first", "value": arguments["value"]}


async def second_tool(arguments):
    return {"tool": "second", "value": arguments["value"]}


def build_registry():
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
