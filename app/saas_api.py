from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.saas import Plan, Role, SaaSStore, TenantAccessError

router = APIRouter(prefix="/saas", tags=["saas"])


class UserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320)


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    owner_id: str = Field(min_length=1)


class MemberCreate(BaseModel):
    actor_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    role: Role = Role.MEMBER


class PlanUpdate(BaseModel):
    actor_id: str = Field(min_length=1)
    plan: Plan


class UsageUpdate(BaseModel):
    user_id: str = Field(min_length=1)
    ai_requests: int = Field(default=0, ge=0)
    agent_runs: int = Field(default=0, ge=0)
    automation_runs: int = Field(default=0, ge=0)
    storage_bytes: int = Field(default=0, ge=0)


def store(request: Request) -> SaaSStore:
    return request.app.state.saas_store


@router.post("/users", status_code=201)
def create_user(payload: UserCreate, request: Request):
    return store(request).create_user(payload.email)


@router.post("/workspaces", status_code=201)
def create_workspace(payload: WorkspaceCreate, request: Request):
    try:
        return store(request).create_workspace(payload.name, payload.owner_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/workspaces/{workspace_id}/members", status_code=201)
def add_member(workspace_id: str, payload: MemberCreate, request: Request):
    try:
        return store(request).add_member(workspace_id, payload.actor_id, payload.user_id, payload.role)
    except TenantAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.patch("/workspaces/{workspace_id}/plan")
def update_plan(workspace_id: str, payload: PlanUpdate, request: Request):
    try:
        return store(request).set_plan(workspace_id, payload.actor_id, payload.plan)
    except TenantAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/workspaces/{workspace_id}/usage")
def get_usage(workspace_id: str, user_id: str, request: Request):
    try:
        store(request).membership(workspace_id, user_id)
        usage = store(request).usage[workspace_id]
        return {"usage": usage, "entitlements": store(request).entitlements(workspace_id), "subscription": store(request).subscriptions[workspace_id]}
    except TenantAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/workspaces/{workspace_id}/usage", status_code=201)
def record_usage(workspace_id: str, payload: UsageUpdate, request: Request):
    try:
        return store(request).record_usage(workspace_id, payload.user_id, ai_requests=payload.ai_requests, agent_runs=payload.agent_runs, automation_runs=payload.automation_runs, storage_bytes=payload.storage_bytes)
    except TenantAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
