from dataclasses import dataclass

from app.automation import AutomationRunner, AutomationStore
from app.calendar_tools import CalendarToolFactory
from app.developer_agent import DeveloperAgent, InMemoryDeveloperWorkspace
from app.developer_tools import DeveloperToolFactory
from app.files import FileStore, FileToolFactory
from app.gmail_tools import GmailToolFactory
from app.integrations.calendar_connection import CalendarConnection
from app.integrations.gmail_connection import GmailConnection
from app.integrations.oauth import InMemoryTokenStore
from app.meetings import MeetingStore
from app.meeting_tools import MeetingToolFactory
from app.permissions import AllowListPermissionChecker
from app.tasks import TaskStore, TaskToolFactory
from app.tools import ToolRegistry


@dataclass(frozen=True)
class AppContainer:
    tools: ToolRegistry
    automations: AutomationStore | None = None
    automation_runner: AutomationRunner | None = None
    meetings: MeetingStore | None = None
    developer_agent: DeveloperAgent | None = None


def build_container() -> AppContainer:
    token_store = InMemoryTokenStore()
    gmail_connection = GmailConnection(token_store=token_store)
    calendar_connection = CalendarConnection(token_store=token_store)

    gmail_factory = GmailToolFactory(gmail_connection)
    calendar_factory = CalendarToolFactory(calendar_connection)
    task_factory = TaskToolFactory(TaskStore())
    file_factory = FileToolFactory(FileStore())
    meeting_store = MeetingStore()
    meeting_factory = MeetingToolFactory(meeting_store)
    developer_workspace = InMemoryDeveloperWorkspace()
    developer_agent = DeveloperAgent(developer_workspace)
    developer_factory = DeveloperToolFactory(developer_workspace)

    permissions = AllowListPermissionChecker(
        frozenset(
            {
                "gmail.list_messages", "gmail.get_message",
                "calendar.list_events", "calendar.get_event", "calendar.create_event", "calendar.update_event", "calendar.delete_event",
                "tasks.create_task", "tasks.list_tasks", "tasks.get_task", "tasks.update_task", "tasks.delete_task",
                "files.create_file", "files.list_files", "files.read_file", "files.update_file", "files.delete_file",
                "meetings.connect", "meetings.create", "meetings.list", "meetings.get", "meetings.update", "meetings.delete",
                "developer.get_repository", "developer.list_branches", "developer.list_commits", "developer.read_file",
                "developer.list_issues", "developer.get_issue", "developer.list_pull_requests", "developer.get_pull_request",
                "developer.get_pull_request_diff", "developer.list_pull_request_files",
                "developer.create_issue", "developer.create_branch", "developer.update_file", "developer.create_pull_request",
            }
        )
    )

    registry = ToolRegistry(permission_checker=permissions)
    for tool in (
        *gmail_factory.definitions(),
        *calendar_factory.definitions(),
        *task_factory.definitions(),
        *file_factory.definitions(),
        *meeting_factory.definitions(),
        *developer_factory.definitions(),
    ):
        registry.register(tool)

    automations = AutomationStore()
    return AppContainer(
        tools=registry,
        automations=automations,
        automation_runner=AutomationRunner(automations, registry),
        meetings=meeting_store,
        developer_agent=developer_agent,
    )
