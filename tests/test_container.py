from app.container import build_container


def test_container_builds_single_tool_registry() -> None:
    container = build_container()

    assert container.tools.names() == (
        "calendar.create_event",
        "calendar.delete_event",
        "calendar.get_event",
        "calendar.list_events",
        "calendar.update_event",
        "gmail.get_message",
        "gmail.list_messages",
    )
