from dataclasses import dataclass

from app.gmail_registry import build_gmail_registry
from app.gmail_tools import GmailToolFactory
from app.integrations.gmail_connection import GmailConnection
from app.integrations.oauth import InMemoryTokenStore
from app.permissions import AllowListPermissionChecker
from app.tools import ToolRegistry


@dataclass(frozen=True)
class AppContainer:
    tools: ToolRegistry


def build_container() -> AppContainer:
    token_store = InMemoryTokenStore()
    gmail_connection = GmailConnection(token_store=token_store)
    gmail_factory = GmailToolFactory(gmail_connection)
    permissions = AllowListPermissionChecker(
        frozenset({"gmail.list_messages", "gmail.get_message"})
    )
    return AppContainer(tools=build_gmail_registry(gmail_factory, permissions))
