import pytest

from app.confirmation import ConfirmationSet
from app.tasks import TaskStore, TaskToolFactory
from app.tools import ToolRegistry


@pytest.mark.asyncio
async def test_task_crud_and_subject_isolation() -> None:
    factory = TaskToolFactory(TaskStore())
    registry = ToolRegistry()
    for tool in factory.definitions():
        registry.register(tool)

    confirmations = ConfirmationSet(
        frozenset({"create-1", "update-1", "delete-1"})
    )

    created = await registry.execute(
        "tasks.create_task",
        {"subject_id": "s1", "title": "Ship feature", "description": "finish it"},
        confirmations=confirmations,
        call_id="create-1",
    )
    assert created["title"] == "Ship feature"
    task_id = created["task_id"]

    assert (await registry.execute("tasks.list_tasks", {"subject_id": "s1"}))['tasks'][0]["task_id"] == task_id
    assert await registry.execute("tasks.list_tasks", {"subject_id": "s2"}) == {"tasks": []}

    updated = await registry.execute(
        "tasks.update_task",
        {"subject_id": "s1", "task_id": task_id, "completed": True},
        confirmations=confirmations,
        call_id="update-1",
    )
    assert updated["completed"] is True

    assert await registry.execute("tasks.get_task", {"subject_id": "s1", "task_id": task_id}) == updated
    assert await registry.execute(
        "tasks.delete_task",
        {"subject_id": "s1", "task_id": task_id},
        confirmations=confirmations,
        call_id="delete-1",
    ) == {"deleted": True, "task_id": task_id}


@pytest.mark.asyncio
async def test_task_mutations_require_confirmation() -> None:
    factory = TaskToolFactory(TaskStore())
    registry = ToolRegistry()
    for tool in factory.definitions():
        registry.register(tool)

    with pytest.raises(Exception, match="confirmation required"):
        await registry.execute("tasks.create_task", {"subject_id": "s1", "title": "Ship"}, call_id="create-1")
