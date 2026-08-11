from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from app.schemas import (
    TaskCreateArguments,
    TaskDeleteArguments,
    TaskGetArguments,
    TaskListArguments,
    TaskUpdateArguments,
)
from app.tools import ToolDefinition


@dataclass
class Task:
    task_id: str
    subject_id: str
    title: str
    description: str | None = None
    completed: bool = False
    due_at: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "subject_id": self.subject_id,
            "title": self.title,
            "description": self.description,
            "completed": self.completed,
            "due_at": self.due_at,
        }


class TaskStore:
    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}

    def create(self, subject_id: str, title: str, description: str | None, due_at: str | None) -> dict[str, Any]:
        task = Task(str(uuid4()), subject_id, title, description, False, due_at)
        self._tasks[task.task_id] = task
        return task.as_dict()

    def list(self, subject_id: str, completed: bool | None = None) -> list[dict[str, Any]]:
        tasks = [task.as_dict() for task in self._tasks.values() if task.subject_id == subject_id]
        if completed is not None:
            tasks = [task for task in tasks if task["completed"] is completed]
        return tasks

    def get(self, subject_id: str, task_id: str) -> dict[str, Any]:
        task = self._tasks.get(task_id)
        if task is None or task.subject_id != subject_id:
            raise KeyError(f"task not found: {task_id}")
        return task.as_dict()

    def update(
        self,
        subject_id: str,
        task_id: str,
        title: str | None,
        description: str | None,
        completed: bool | None,
        due_at: str | None,
    ) -> dict[str, Any]:
        task = self._tasks.get(task_id)
        if task is None or task.subject_id != subject_id:
            raise KeyError(f"task not found: {task_id}")
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if completed is not None:
            task.completed = completed
        if due_at is not None:
            task.due_at = due_at
        return task.as_dict()

    def delete(self, subject_id: str, task_id: str) -> dict[str, Any]:
        task = self._tasks.get(task_id)
        if task is None or task.subject_id != subject_id:
            raise KeyError(f"task not found: {task_id}")
        del self._tasks[task_id]
        return {"deleted": True, "task_id": task_id}


class TaskToolFactory:
    def __init__(self, store: TaskStore) -> None:
        self._store = store

    def definitions(self) -> tuple[ToolDefinition, ...]:
        return (
            ToolDefinition("tasks.create_task", "Create a task.", self.create_task, TaskCreateArguments, True),
            ToolDefinition("tasks.list_tasks", "List tasks for a subject.", self.list_tasks, TaskListArguments),
            ToolDefinition("tasks.get_task", "Get one task.", self.get_task, TaskGetArguments),
            ToolDefinition("tasks.update_task", "Update a task.", self.update_task, TaskUpdateArguments, True),
            ToolDefinition("tasks.delete_task", "Delete a task.", self.delete_task, TaskDeleteArguments, True),
        )

    async def create_task(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self._store.create(arguments["subject_id"], arguments["title"], arguments.get("description"), arguments.get("due_at"))

    async def list_tasks(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return {"tasks": self._store.list(arguments["subject_id"], arguments.get("completed"))}

    async def get_task(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self._store.get(arguments["subject_id"], arguments["task_id"])

    async def update_task(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self._store.update(
            arguments["subject_id"], arguments["task_id"], arguments.get("title"),
            arguments.get("description"), arguments.get("completed"), arguments.get("due_at"),
        )

    async def delete_task(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self._store.delete(arguments["subject_id"], arguments["task_id"])
