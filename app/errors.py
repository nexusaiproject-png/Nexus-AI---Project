from fastapi import Request
from fastapi.responses import JSONResponse

from app.permissions import PermissionDeniedError


async def permission_denied_handler(
    request: Request, exc: PermissionDeniedError
) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": str(exc)})


async def tool_not_found_handler(
    request: Request, exc: KeyError
) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})
