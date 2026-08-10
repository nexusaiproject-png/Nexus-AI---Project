from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ToolExecutionError:
    call_id: str
    name: str
    error_type: str
    message: str

    def as_message(self) -> dict[str, Any]:
        return {
            "role": "tool",
            "tool_call_id": self.call_id,
            "name": self.name,
            "content": {
                "error": self.error_type,
                "message": self.message,
            },
        }
