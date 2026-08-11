from fastapi import APIRouter, HTTPException, Request

from app.confirmation import ConfirmationRequiredError
from app.models import ToolExecutionRequest, ToolExecutionResponse
from app.permissions import PermissionDeniedError
from app.tools import ToolArgumentError

router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("")
async def list_tools(request: Request) -> dict[str, list[str]]:
    return {"tools": list(request.app.state.container.tools.names())}


@router.post("/{tool_name:path}/execute", response_model=ToolExecutionResponse)
async def execute_tool(
    tool_name: str,
    payload: ToolExecutionRequest,
    request: Request,
) -> ToolExecutionResponse:
    try:
        result = await request.app.state.container.tools.execute(
            tool_name,
            payload.arguments,
            subject_id=payload.subject_id,
            confirmed=payload.confirmed,
            call_id=payload.confirmation_id,
        )
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ConfirmationRequiredError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ToolArgumentError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"tool execution failed: {exc}") from exc
    return ToolExecutionResponse(result=result)
