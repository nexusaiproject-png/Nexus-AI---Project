from app.container import build_container


def test_container_builds_single_tool_registry() -> None:
    container = build_container()

    assert container.tools.names() == (
        "calendar.create_event",
        "calendar.delete_event",
        "calendar.get_event",
        "calendar.list_events",
        "calendar.update_event",
        "files.create_file",
        "files.delete_file",
        "files.list_files",
        "files.read_file",
        "files.update_file",
        "gmail.get_message",
        "gmail.list_messages",
        "tasks.create_task",
        "tasks.delete_task",
        "tasks.get_task",
        "tasks.list_tasks",
        "tasks.update_task",
    )
