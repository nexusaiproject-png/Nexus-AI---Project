from typing import Any

from pydantic import BaseModel, Field


class ToolExecutionRequest(BaseModel):
    subject_id: str = Field(min_length=1)
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolExecutionResponse(BaseModel):
    result: Any
