from datetime import datetime, timezone

import pytest

from app.automation import (
    Automation,
    AutomationAction,
    AutomationCondition,
    AutomationError,
    AutomationNotFoundError,
    AutomationRunner,
    AutomationStore,
    AutomationTrigger,
    ConditionEvaluator,
)
from app.confirmation import ConfirmationRequiredError, ConfirmationSet
from app.tools import ToolDefinition, ToolRegistry


def make_registry(calls: list[dict]) -> ToolRegistry:
    registry = ToolRegistry()

    async def handler(arguments: dict):
        calls.append(arguments)
        return {"ok": True, "arguments": arguments}

    registry.register(ToolDefinition("echo", "echo", handler))
    registry.register(ToolDefinition("sensitive", "sensitive", handler, requires_confirmation=True))
    return registry


def test_condition_evaluator_supports_basic_operators() -> None:
    evaluator = ConditionEvaluator()
    assert evaluator.matches({"status": "ready", "count": 3, "tags": ["urgent"]}, (
        AutomationCondition("status", "eq", "ready"),
        AutomationCondition("count", "gte", 2),
        AutomationCondition("tags", "contains", "urgent"),
    ))
    assert not evaluator.matches({"status": "pending"}, (AutomationCondition("status", "eq", "ready"),))


def test_store_is_subject_scoped() -> None:
    store = AutomationStore()
    action = AutomationAction("echo", {"value": "ok"})
    first = Automation("a1", "s1", "one", AutomationTrigger("event"), actions=(action,))
    second = Automation("a2", "s2", "two", AutomationTrigger("event"), actions=(action,))
    store.create(first)
    store.create(second)

    assert store.list("s1") == (first,)
    with pytest.raises(AutomationNotFoundError):
        store.get("a2", "s1")


@pytest.mark.asyncio
async def test_runner_dispatches_matching_automation() -> None:
    calls: list[dict] = []
    tools = make_registry(calls)
    store = AutomationStore()
    automation = Automation(
        "a1",
        "s1",
        "when ready",
        AutomationTrigger("event", {"name": "task.updated"}),
        (AutomationCondition("status", "eq", "ready"),),
        (AutomationAction("echo", {"value": "done"}),),
    )
    store.create(automation)
    runner = AutomationRunner(store, tools)

    result = await runner.dispatch("s1", AutomationTrigger("event", {"name": "task.updated"}), {"status": "ready"})
    assert result["a1"][0]["ok"] is True
    assert calls == [{"value": "done"}]


@pytest.mark.asyncio
async def test_runner_skips_disabled_or_non_matching_automation() -> None:
    calls: list[dict] = []
    tools = make_registry(calls)
    store = AutomationStore()
    noop = (AutomationAction("echo", {"value": "noop"}),)
    store.create(Automation("disabled", "s1", "disabled", AutomationTrigger("event"), actions=noop, enabled=False))
    store.create(Automation("wrong", "s1", "wrong", AutomationTrigger("event", {"name": "other.event"}), actions=noop))
    runner = AutomationRunner(store, tools)

    assert await runner.dispatch("s1", AutomationTrigger("event", {"name": "task.updated"}), {}) == {}
    assert calls == []


def test_store_rejects_unsupported_trigger_kind() -> None:
    store = AutomationStore()
    action = AutomationAction("echo", {"value": "noop"})
    with pytest.raises(AutomationError, match="unsupported trigger kind"):
        store.create(Automation("invalid", "s1", "invalid", AutomationTrigger("other"), actions=(action,)))


@pytest.mark.asyncio
async def test_sensitive_automation_requires_confirmation() -> None:
    tools = make_registry([])
    store = AutomationStore()
    store.create(Automation(
        "a1",
        "s1",
        "sensitive",
        AutomationTrigger("event"),
        actions=(AutomationAction("sensitive", {}, "auto-call"),),
    ))
    runner = AutomationRunner(store, tools)

    with pytest.raises(ConfirmationRequiredError):
        await runner.run("a1", "s1", {})

    result = await runner.run("a1", "s1", {}, ConfirmationSet(frozenset({"auto-call"})))
    assert result[0]["ok"] is True


def test_schedule_trigger_can_be_evaluated_from_iso_timestamp() -> None:
    now = datetime.now(timezone.utc).isoformat()
    trigger = AutomationTrigger("schedule", {"at": now})
    assert trigger.kind == "schedule"
    assert datetime.fromisoformat(trigger.config["at"]).tzinfo is not None
