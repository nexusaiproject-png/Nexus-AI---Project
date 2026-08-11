from dataclasses import dataclass

from app.calendar_registry import build_calendar_registry
from app.calendar_tools import CalendarToolFactory
from app.gmail_registry import build_gmail_registry
from app.gmail_tools import GmailToolFactory
from app.integrations.calendar_connection import CalendarConnection
from app.integrations.gmail_connection import GmailConnection
from app.integrations.oauth import InMemoryTokenStore
from app.permissions import AllowListPermissionChecker
from app.tools import ToolDefinition, ToolRegistry


@dataclass(frozen=True)
class AppContainer:
    tools: ToolRegistry


def build_container() -> AppContainer:
    token_store = InMemoryTokenStore()
    gmail_connection = GmailConnection(token_store=token_store)
    calendar_connection = CalendarConnection(token_store=token_store)

    gmail_factory = GmailToolFactory(gmail_connection)
    calendar_factory = CalendarToolFactory(calendar_connection)

    permissions = AllowListPermissionChecker(
        frozenset(
            {
                "gmail.list_messages",
                "gmail.get_message",
                "calendar.list_events",
                "calendar.get_event",
                "calendar.create_event",
                "calendar.update_event",
                "calendar.delete_event",
            }
        )
    )

    registry = ToolRegistry(permission_checker=permissions)
    for tool in (*gmail_factory.definitions(), *calendar_factory.definitions()):
        registry.register(tool)
    return AppContainer(tools=registry)
