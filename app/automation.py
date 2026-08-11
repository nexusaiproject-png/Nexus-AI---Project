from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.confirmation import ConfirmationSet
from app.tools import ToolRegistry


class AutomationError(ValueError):
    pass


class AutomationNotFoundError(AutomationError):
    pass


@dataclass(frozen=True)
class AutomationTrigger:
    kind: str
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AutomationCondition:
    field: str
    operator: str
    value: Any


@dataclass(frozen=True)
class AutomationAction:
    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    call_id: str | None = None


@dataclass
class Automation:
    id: str
    subject_id: str
    name: str
    trigger: AutomationTrigger
    conditions: tuple[AutomationCondition, ...] = ()
    actions: tuple[AutomationAction, ...] = ()
    enabled: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AutomationStore:
    def __init__(self) -> None:
        self._items: dict[str, Automation] = {}

    def create(self, automation: Automation) -> Automation:
        if automation.id in self._items:
            raise AutomationError(f"automation already exists: {automation.id}")
        self._items[automation.id] = automation
        return automation

    def get(self, automation_id: str, subject_id: str) -> Automation:
        item = self._items.get(automation_id)
        if item is None or item.subject_id != subject_id:
            raise AutomationNotFoundError(f"automation not found: {automation_id}")
        return item

    def list(self, subject_id: str) -> tuple[Automation, ...]:
        return tuple(sorted((x for x in self._items.values() if x.subject_id == subject_id), key=lambda x: x.id))

    def update(self, automation_id: str, subject_id: str, **changes: Any) -> Automation:
        item = self.get(automation_id, subject_id)
        for key, value in changes.items():
            if value is not None and hasattr(item, key):
                setattr(item, key, value)
        item.updated_at = datetime.now(timezone.utc)
        return item

    def delete(self, automation_id: str, subject_id: str) -> None:
        self.get(automation_id, subject_id)
        del self._items[automation_id]


class ConditionEvaluator:
    SUPPORTED = {"eq", "neq", "contains", "gt", "gte", "lt", "lte"}

    def matches(self, payload: dict[str, Any], conditions: tuple[AutomationCondition, ...]) -> bool:
        for condition in conditions:
            if condition.operator not in self.SUPPORTED:
                raise AutomationError(f"unsupported condition operator: {condition.operator}")
            actual = payload.get(condition.field)
            expected = condition.value
            if condition.operator == "eq" and actual != expected:
                return False
            if condition.operator == "neq" and actual == expected:
                return False
            if condition.operator == "contains" and (not isinstance(actual, (str, list, tuple, set)) or expected not in actual):
                return False
            if condition.operator == "gt" and not actual > expected:
                return False
            if condition.operator == "gte" and not actual >= expected:
                return False
            if condition.operator == "lt" and not actual < expected:
                return False
            if condition.operator == "lte" and not actual <= expected:
                return False
        return True


class AutomationRunner:
    def __init__(self, store: AutomationStore, tools: ToolRegistry) -> None:
        self.store = store
        self.tools = tools
        self.conditions = ConditionEvaluator()

    async def run(self, automation_id: str, subject_id: str, event: dict[str, Any], confirmations: ConfirmationSet | None = None) -> list[Any]:
        automation = self.store.get(automation_id, subject_id)
        if not automation.enabled or not self.conditions.matches(event, automation.conditions):
            return []
        results: list[Any] = []
        for action in automation.actions:
            results.append(
                await self.tools.execute(
                    action.tool_name,
                    dict(action.arguments),
                    subject_id=subject_id,
                    confirmations=confirmations,
                    call_id=action.call_id or f"automation:{automation.id}:{action.tool_name}",
                )
            )
        return results

    async def dispatch(self, subject_id: str, trigger: AutomationTrigger, event: dict[str, Any], confirmations: ConfirmationSet | None = None) -> dict[str, list[Any]]:
        results: dict[str, list[Any]] = {}
        for automation in self.store.list(subject_id):
            if automation.trigger.kind == trigger.kind and automation.trigger.config == trigger.config:
                results[automation.id] = await self.run(automation.id, subject_id, event, confirmations)
        return results


def new_automation_id() -> str:
    return str(uuid4())
