from __future__ import annotations

from pathlib import Path
from typing import Any

from app.schemas import (
    FileCreateArguments,
    FileDeleteArguments,
    FileListArguments,
    FileReadArguments,
    FileUpdateArguments,
)
from app.tools import ToolDefinition


class FileStore:
    """Subject-scoped workspace file store backed by the local filesystem."""

    def __init__(self, root: str | Path = "./data/files") -> None:
        self._root = Path(root).resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, subject_id: str, name: str) -> Path:
        if not subject_id.strip() or not name.strip():
            raise ValueError("subject_id and file name are required")
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("invalid file path")
        subject_root = (self._root / subject_id).resolve()
        subject_root.mkdir(parents=True, exist_ok=True)
        path = (subject_root / relative).resolve()
        if not path.is_relative_to(subject_root):
            raise ValueError("invalid file path")
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def create(self, subject_id: str, name: str, content: str) -> dict[str, Any]:
        path = self._path(subject_id, name)
        if path.exists():
            raise FileExistsError(f"file already exists: {name}")
        path.write_text(content, encoding="utf-8")
        return self._metadata(subject_id, path)

    def list(self, subject_id: str) -> list[dict[str, Any]]:
        base = (self._root / subject_id).resolve()
        if not base.is_relative_to(self._root) or not base.exists():
            return []
        return [self._metadata(subject_id, path) for path in sorted(base.rglob("*")) if path.is_file() and not path.is_symlink()]

    def read(self, subject_id: str, name: str) -> dict[str, Any]:
        path = self._path(subject_id, name)
        if not path.is_file() or path.is_symlink():
            raise FileNotFoundError(f"file not found: {name}")
        return {**self._metadata(subject_id, path), "content": path.read_text(encoding="utf-8")}

    def update(self, subject_id: str, name: str, content: str) -> dict[str, Any]:
        path = self._path(subject_id, name)
        if not path.is_file() or path.is_symlink():
            raise FileNotFoundError(f"file not found: {name}")
        path.write_text(content, encoding="utf-8")
        return self._metadata(subject_id, path)

    def delete(self, subject_id: str, name: str) -> dict[str, Any]:
        path = self._path(subject_id, name)
        if not path.is_file() or path.is_symlink():
            raise FileNotFoundError(f"file not found: {name}")
        path.unlink()
        return {"deleted": True, "name": name}

    def _metadata(self, subject_id: str, path: Path) -> dict[str, Any]:
        relative = path.relative_to(self._root / subject_id).as_posix()
        return {"name": relative, "size": path.stat().st_size}


class FileToolFactory:
    def __init__(self, store: FileStore) -> None:
        self._store = store

    def definitions(self) -> tuple[ToolDefinition, ...]:
        return (
            ToolDefinition("files.create_file", "Create a workspace file.", self.create_file, FileCreateArguments, True),
            ToolDefinition("files.list_files", "List workspace files for a subject.", self.list_files, FileListArguments),
            ToolDefinition("files.read_file", "Read a workspace file.", self.read_file, FileReadArguments),
            ToolDefinition("files.update_file", "Update a workspace file.", self.update_file, FileUpdateArguments, True),
            ToolDefinition("files.delete_file", "Delete a workspace file.", self.delete_file, FileDeleteArguments, True),
        )

    async def create_file(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self._store.create(arguments["subject_id"], arguments["name"], arguments["content"])

    async def list_files(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return {"files": self._store.list(arguments["subject_id"])}

    async def read_file(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self._store.read(arguments["subject_id"], arguments["name"])

    async def update_file(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self._store.update(arguments["subject_id"], arguments["name"], arguments["content"])

    async def delete_file(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self._store.delete(arguments["subject_id"], arguments["name"],)
