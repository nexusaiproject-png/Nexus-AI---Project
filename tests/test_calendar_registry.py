from app.calendar_registry import CALENDAR_TOOL_NAMES, build_calendar_registry
from app.calendar_tools import CalendarToolFactory
from app.permissions import AllowListPermissionChecker


class DummyConnection:
    async def client_for(self, account_id):
        raise AssertionError("not called")


def test_calendar_registry_registers_all_tools():
    registry = build_calendar_registry(
        CalendarToolFactory(DummyConnection()),
        AllowListPermissionChecker(frozenset(CALENDAR_TOOL_NAMES)),
    )
    assert frozenset(registry.names()) == CALENDAR_TOOL_NAMES
