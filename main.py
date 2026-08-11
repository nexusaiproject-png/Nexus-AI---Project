from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import router as tools_router
from app.automation_api import router as automation_router
from app.container import build_container
from app.errors import (
    permission_denied_handler,
    tool_argument_error_handler,
    tool_not_found_handler,
)
from app.permissions import PermissionDeniedError
from app.saas import SaaSStore
from app.saas_api import router as saas_router
from app.tools import ToolArgumentError
from app.web import router as web_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.container = build_container()
    app.state.saas_store = SaaSStore()
    yield
    app.state.container = None
    app.state.saas_store = None


app = FastAPI(
    title="Nexus AI Workspace",
    version="0.1.0",
    description="Backend foundation for the Nexus AI Workspace platform.",
    lifespan=lifespan,
)
app.add_exception_handler(PermissionDeniedError, permission_denied_handler)
app.add_exception_handler(KeyError, tool_not_found_handler)
app.add_exception_handler(ToolArgumentError, tool_argument_error_handler)
app.include_router(tools_router)
app.include_router(automation_router)
app.include_router(saas_router)
app.include_router(web_router)


@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    return {"message": "Nexus AI Backend is running"}


@app.get("/hello", tags=["system"])
async def hello() -> dict[str, str]:
    return {"message": "Hello from Nexus AI"}


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "nexus-backend"}
