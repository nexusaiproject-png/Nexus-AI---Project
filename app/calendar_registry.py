from app.calendar_tools import CalendarToolFactory
from app.permissions import PermissionChecker
from app.tools import ToolRegistry


CALENDAR_TOOL_NAMES = frozenset(
    {
        "calendar.list_events",
        "calendar.get_event",
        "calendar.create_event",
        "calendar.update_event",
        "calendar.delete_event",
    }
)


def build_calendar_registry(
    factory: CalendarToolFactory,
    permission_checker: PermissionChecker,
) -> ToolRegistry:
    registry = ToolRegistry(permission_checker=permission_checker)
    for tool in factory.definitions():
        registry.register(tool)
    return registry
