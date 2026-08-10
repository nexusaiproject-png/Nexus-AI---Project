from fastapi import APIRouter, Request

from app.models import ToolExecutionRequest, ToolExecutionResponse

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
    result = await request.app.state.container.tools.execute(
        tool_name,
        payload.arguments,
        subject_id=payload.subject_id,
    )
    return ToolExecutionResponse(result=result)
