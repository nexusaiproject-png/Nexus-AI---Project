from app.container import build_container


def test_container_builds_single_tool_registry() -> None:
    container = build_container()

    assert container.tools.names() == (
        "gmail.get_message",
        "gmail.list_messages",
    )
