from __future__ import annotations

from fastapi import APIRouter, Cookie, HTTPException, Response
from pydantic import BaseModel, EmailStr

from app.auth import AuthError, AuthStore

router = APIRouter(prefix="/auth", tags=["auth"])
store = AuthStore()


class SignupRequest(BaseModel):
    email: EmailStr
    name: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class VerifyRequest(BaseModel):
    token: str


class WorkspaceRequest(BaseModel):
    name: str
    purpose: str | None = None


class OnboardingRequest(BaseModel):
    purpose: str | None = None


def current_user(session: str | None):
    user = store.get_user_by_session(session) if session else None
    if not user:
        raise HTTPException(status_code=401, detail="authentication required")
    return user


@router.post("/signup", status_code=201)
def signup(payload: SignupRequest) -> dict:
    try:
        user, token = store.create_user(payload.email, payload.name, payload.password)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    # Until an email delivery integration exists, the token is returned so deployments
    # can hand it to their configured mail layer without exposing passwords or sessions.
    return {"user_id": user.id, "email": user.email, "verification_required": True, "verification_token": token}


@router.post("/verify-email")
def verify_email(payload: VerifyRequest) -> dict:
    try:
        user = store.verify_email(payload.token)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"user_id": user.id, "email": user.email, "verified": True}


@router.post("/login")
def login(payload: LoginRequest, response: Response) -> dict:
    try:
        user = store.authenticate(payload.email, payload.password)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    token = store.create_session(user.id)
    response.set_cookie("nexus_session", token, httponly=True, secure=False, samesite="lax", max_age=86_400)
    return {"user_id": user.id, "email": user.email, "workspace_id": user.workspace_id}


@router.post("/logout")
def logout(response: Response, nexus_session: str | None = Cookie(default=None)) -> dict:
    if nexus_session:
        store.delete_session(nexus_session)
    response.delete_cookie("nexus_session")
    return {"logged_out": True}


@router.get("/me")
def me(nexus_session: str | None = Cookie(default=None)) -> dict:
    user = current_user(nexus_session)
    return {"id": user.id, "email": user.email, "name": user.name, "email_verified": user.email_verified, "workspace_id": user.workspace_id}


@router.post("/workspace", status_code=201)
def create_workspace(payload: WorkspaceRequest, nexus_session: str | None = Cookie(default=None)) -> dict:
    user = current_user(nexus_session)
    try:
        workspace_id = store.create_workspace(user.id, payload.name, payload.purpose)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"workspace_id": workspace_id, "name": payload.name.strip(), "purpose": payload.purpose, "role": "owner"}


@router.post("/onboarding")
def onboarding(payload: OnboardingRequest, nexus_session: str | None = Cookie(default=None)) -> dict:
    user = current_user(nexus_session)
    if user.workspace_id is None:
        raise HTTPException(status_code=400, detail="workspace must be created first")
    try:
        store.update_onboarding(user.id, user.workspace_id, payload.purpose)
    except AuthError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return {"onboarding_complete": True, "workspace_id": user.workspace_id}
