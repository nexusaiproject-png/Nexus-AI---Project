from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request

from app.container import AppContainer, build_container
from app.models import ToolExecutionRequest, ToolExecutionResponse
from app.permissions import PermissionDeniedError


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.container = build_container()
    yield
    app.state.container = None


app = FastAPI(
    title="Nexus AI Workspace",
    version="0.1.0",
    description="Backend foundation for the Nexus AI Workspace platform.",
    lifespan=lifespan,
)


def get_container(request: Request) -> AppContainer:
    return request.app.state.container


@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    return {"message": "Nexus AI Backend is running"}


@app.get("/hello", tags=["system"])
async def hello() -> dict[str, str]:
    return {"message": "Hello from Nexus AI"}


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "nexus-backend"}


@app.get("/tools", tags=["tools"])
async def tools(request: Request) -> dict[str, list[str]]:
    container = get_container(request)
    return {"tools": list(container.tools.names())}


@app.post("/tools/{tool_name:path}/execute", response_model=ToolExecutionResponse, tags=["tools"])
async def execute_tool(
    tool_name: str,
    payload: ToolExecutionRequest,
    request: Request,
) -> ToolExecutionResponse:
    container = get_container(request)
    try:
        result = await container.tools.execute(
            tool_name,
            payload.arguments,
            subject_id=payload.subject_id,
        )
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ToolExecutionResponse(result=result)
