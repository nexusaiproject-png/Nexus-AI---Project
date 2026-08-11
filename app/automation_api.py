from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.automation import (
    Automation,
    AutomationAction,
    AutomationCondition,
    AutomationNotFoundError,
    AutomationTrigger,
    new_automation_id,
)
from app.confirmation import ConfirmationSet


router = APIRouter(prefix="/automations", tags=["automations"])


class TriggerPayload(BaseModel):
    kind: str = Field(min_length=1)
    config: dict[str, Any] = Field(default_factory=dict)


class ConditionPayload(BaseModel):
    field: str = Field(min_length=1)
    operator: str = Field(min_length=1)
    value: Any


class ActionPayload(BaseModel):
    tool_name: str = Field(min_length=1)
    arguments: dict[str, Any] = Field(default_factory=dict)
    call_id: str | None = None


class AutomationPayload(BaseModel):
    subject_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    trigger: TriggerPayload
    conditions: list[ConditionPayload] = Field(default_factory=list)
    actions: list[ActionPayload] = Field(default_factory=list)
    enabled: bool = True


class AutomationUpdatePayload(BaseModel):
    subject_id: str = Field(min_length=1)
    name: str | None = None
    trigger: TriggerPayload | None = None
    conditions: list[ConditionPayload] | None = None
    actions: list[ActionPayload] | None = None
    enabled: bool | None = None


def _to_dict(item: Automation) -> dict[str, Any]:
    return {
        "id": item.id,
        "subject_id": item.subject_id,
        "name": item.name,
        "trigger": {"kind": item.trigger.kind, "config": item.trigger.config},
        "conditions": [c.__dict__ for c in item.conditions],
        "actions": [a.__dict__ for a in item.actions],
        "enabled": item.enabled,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }


def _build(payload: AutomationPayload) -> Automation:
    return Automation(
        id=new_automation_id(),
        subject_id=payload.subject_id,
        name=payload.name,
        trigger=AutomationTrigger(payload.trigger.kind, payload.trigger.config),
        conditions=tuple(AutomationCondition(c.field, c.operator, c.value) for c in payload.conditions),
        actions=tuple(AutomationAction(a.tool_name, a.arguments, a.call_id) for a in payload.actions),
        enabled=payload.enabled,
    )


@router.post("")
async def create_automation(payload: AutomationPayload, request: Request) -> dict[str, Any]:
    item = _build(payload)
    request.app.state.container.automations.create(item)
    return _to_dict(item)


@router.get("")
async def list_automations(subject_id: str, request: Request) -> dict[str, list[dict[str, Any]]]:
    return {"automations": [_to_dict(x) for x in request.app.state.container.automations.list(subject_id)]}


@router.get("/{automation_id}")
async def get_automation(automation_id: str, subject_id: str, request: Request) -> dict[str, Any]:
    try:
        return _to_dict(request.app.state.container.automations.get(automation_id, subject_id))
    except AutomationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{automation_id}")
async def update_automation(automation_id: str, payload: AutomationUpdatePayload, request: Request) -> dict[str, Any]:
    changes: dict[str, Any] = {}
    if payload.name is not None:
        changes["name"] = payload.name
    if payload.trigger is not None:
        changes["trigger"] = AutomationTrigger(payload.trigger.kind, payload.trigger.config)
    if payload.conditions is not None:
        changes["conditions"] = tuple(AutomationCondition(c.field, c.operator, c.value) for c in payload.conditions)
    if payload.actions is not None:
        changes["actions"] = tuple(AutomationAction(a.tool_name, a.arguments, a.call_id) for a in payload.actions)
    if payload.enabled is not None:
        changes["enabled"] = payload.enabled
    try:
        return _to_dict(request.app.state.container.automations.update(automation_id, payload.subject_id, **changes))
    except AutomationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{automation_id}")
async def delete_automation(automation_id: str, subject_id: str, request: Request) -> dict[str, bool]:
    try:
        request.app.state.container.automations.delete(automation_id, subject_id)
    except AutomationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"deleted": True}


class RunPayload(BaseModel):
    subject_id: str = Field(min_length=1)
    event: dict[str, Any] = Field(default_factory=dict)
    confirmation_ids: list[str] = Field(default_factory=list)


@router.post("/{automation_id}/run")
async def run_automation(automation_id: str, payload: RunPayload, request: Request) -> dict[str, Any]:
    try:
        result = await request.app.state.container.automation_runner.run(
            automation_id,
            payload.subject_id,
            payload.event,
            ConfirmationSet(frozenset(payload.confirmation_ids)),
        )
        return {"results": result}
    except AutomationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"automation execution failed: {exc}") from exc
