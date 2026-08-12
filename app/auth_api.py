from __future__ import annotations

import os

from fastapi import APIRouter, Cookie, HTTPException, Response
from pydantic import BaseModel

from app.auth import AuthError, AuthStore
from app.email_service import EmailDeliveryError, send_password_reset_email, send_verification_email

router = APIRouter(prefix="/auth", tags=["auth"])
store = AuthStore()


class SignupRequest(BaseModel):
    email: str
    name: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenRequest(BaseModel):
    token: str


class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetConfirm(BaseModel):
    token: str
    password: str


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


def _valid_email(email: str) -> bool:
    local, sep, domain = email.strip().partition("@")
    return bool(local and sep and "." in domain)


@router.post("/signup", status_code=201)
def signup(payload: SignupRequest) -> dict:
    if not _valid_email(payload.email):
        raise HTTPException(status_code=400, detail="valid email is required")
    try:
        user, token = store.create_user(payload.email, payload.name, payload.password)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        send_verification_email(user.email, user.name, token)
    except EmailDeliveryError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    result = {"user_id": user.id, "email": user.email, "verification_required": True}
    if os.getenv("NEXUS_EXPOSE_DEV_TOKENS", "false").lower() == "true":
        result["verification_token"] = token
    return result


@router.post("/verify-email")
def verify_email(payload: TokenRequest) -> dict:
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
    secure = os.getenv("NEXUS_COOKIE_SECURE", "false").lower() == "true"
    response.set_cookie("nexus_session", token, httponly=True, secure=secure, samesite="lax", max_age=86_400)
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


@router.post("/password-reset/request")
def password_reset_request(payload: PasswordResetRequest) -> dict:
    user = store.get_user_by_email(payload.email)
    if user:
        token = store.request_password_reset(payload.email)
        try:
            send_password_reset_email(user.email, user.name, token)
        except EmailDeliveryError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        result = {"accepted": True}
        if os.getenv("NEXUS_EXPOSE_DEV_TOKENS", "false").lower() == "true":
            result["reset_token"] = token
        return result
    return {"accepted": True}


@router.post("/password-reset/confirm")
def password_reset_confirm(payload: PasswordResetConfirm) -> dict:
    try:
        store.reset_password(payload.token, payload.password)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"password_reset": True}


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
