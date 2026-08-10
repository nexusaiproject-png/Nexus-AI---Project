from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import router as tools_router
from app.container import build_container
from app.errors import permission_denied_handler
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
app.add_exception_handler(PermissionDeniedError, permission_denied_handler)
app.include_router(tools_router)


@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    return {"message": "Nexus AI Backend is running"}


@app.get("/hello", tags=["system"])
async def hello() -> dict[str, str]:
    return {"message": "Hello from Nexus AI"}


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "nexus-backend"}
