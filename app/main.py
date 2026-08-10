from fastapi import FastAPI

app = FastAPI(
    title="Nexus AI Workspace",
    version="0.1.0",
    description="Backend foundation for the Nexus AI Workspace platform.",
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Nexus AI Backend is running"}


@app.get("/hello")
async def hello() -> dict[str, str]:
    return {"message": "Hello from Nexus AI"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
