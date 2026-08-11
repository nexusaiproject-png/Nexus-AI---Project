from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard() -> HTMLResponse:
    page = Path(__file__).resolve().parents[1] / "web" / "dashboard.html"
    return HTMLResponse(page.read_text(encoding="utf-8"))
