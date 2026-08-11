import pytest

from app.files import FileStore, FileToolFactory
from app.tools import ToolRegistry


@pytest.mark.asyncio
async def test_file_crud_and_subject_isolation(tmp_path) -> None:
    factory = FileToolFactory(FileStore(tmp_path))
    registry = ToolRegistry()
    for tool in factory.definitions():
        registry.register(tool)

    created = await registry.execute(
        "files.create_file",
        {"subject_id": "s1", "name": "notes/plan.txt", "content": "hello"},
        confirmations=None,
        call_id="create-1",
    )
    assert created == {"name": "notes/plan.txt", "size": 5}

    assert await registry.execute("files.list_files", {"subject_id": "s1"}) == {
        "files": [{"name": "notes/plan.txt", "size": 5}]
    }
    assert await registry.execute("files.list_files", {"subject_id": "s2"}) == {"files": []}
    assert await registry.execute("files.read_file", {"subject_id": "s1", "name": "notes/plan.txt"}) == {
        "name": "notes/plan.txt",
        "size": 5,
        "content": "hello",
    }

    updated = await registry.execute(
        "files.update_file",
        {"subject_id": "s1", "name": "notes/plan.txt", "content": "updated"},
        confirmations=None,
        call_id="update-1",
    )
    assert updated == {"name": "notes/plan.txt", "size": 7}

    deleted = await registry.execute(
        "files.delete_file",
        {"subject_id": "s1", "name": "notes/plan.txt"},
        confirmations=None,
        call_id="delete-1",
    )
    assert deleted == {"deleted": True, "name": "notes/plan.txt"}


@pytest.mark.asyncio
async def test_file_mutations_require_confirmation(tmp_path) -> None:
    factory = FileToolFactory(FileStore(tmp_path))
    registry = ToolRegistry()
    for tool in factory.definitions():
        registry.register(tool)

    with pytest.raises(Exception, match="confirmation required"):
        await registry.execute(
            "files.create_file",
            {"subject_id": "s1", "name": "notes.txt", "content": "hello"},
            call_id="create-1",
        )


@pytest.mark.asyncio
async def test_file_paths_cannot_escape_subject_root(tmp_path) -> None:
    store = FileStore(tmp_path)
    with pytest.raises(ValueError, match="invalid file path"):
        store.create("s1", "../secret.txt", "nope")
