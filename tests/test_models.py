import pytest
from pydantic import ValidationError

from app.models import ToolExecutionRequest, ToolExecutionResponse


def test_tool_execution_request_defaults_arguments() -> None:
    request = ToolExecutionRequest(subject_id="account-1")
    assert request.arguments == {}


def test_tool_execution_request_requires_subject_id() -> None:
    with pytest.raises(ValidationError):
        ToolExecutionRequest(subject_id="")


def test_tool_execution_response_accepts_any_result() -> None:
    response = ToolExecutionResponse(result={"ok": True})
    assert response.result == {"ok": True}
