from app.gmail_tools import GmailToolFactory
from app.permissions import PermissionChecker
from app.tools import ToolRegistry


GMAIL_TOOL_NAMES = frozenset({"gmail.list_messages", "gmail.get_message"})


def build_gmail_registry(
    factory: GmailToolFactory,
    permission_checker: PermissionChecker,
) -> ToolRegistry:
    registry = ToolRegistry(permission_checker=permission_checker)
    for tool in factory.definitions():
        registry.register(tool)
    return registry
