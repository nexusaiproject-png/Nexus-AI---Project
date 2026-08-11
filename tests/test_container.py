from app.container import build_container


def test_container_builds_single_tool_registry() -> None:
    container = build_container()

    assert container.tools.names() == (
        "calendar.create_event",
        "calendar.delete_event",
        "calendar.get_event",
        "calendar.list_events",
        "calendar.update_event",
        "developer.create_branch",
        "developer.create_issue",
        "developer.get_issue",
        "developer.get_pull_request",
        "developer.get_repository",
        "developer.list_branches",
        "developer.list_commits",
        "developer.list_issues",
        "developer.list_pull_requests",
        "developer.read_file",
        "developer.update_file",
        "files.create_file",
        "files.delete_file",
        "files.list_files",
        "files.read_file",
        "files.update_file",
        "gmail.get_message",
        "gmail.list_messages",
        "meetings.connect",
        "meetings.create",
        "meetings.delete",
        "meetings.get",
        "meetings.list",
        "meetings.update",
        "tasks.create_task",
        "tasks.delete_task",
        "tasks.get_task",
        "tasks.list_tasks",
        "tasks.update_task",
    )
    assert container.meetings is not None
    assert container.developer_agent is not None
