from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ToolSchema:
    name: str
    required: tuple[str, ...]

    def validate(self, arguments: dict[str, Any]) -> None:
        missing = [key for key in self.required if key not in arguments]
        if missing:
            raise ValueError(f"missing required arguments: {', '.join(missing)}")


GMAIL_LIST_MESSAGES_SCHEMA = ToolSchema(
    "gmail.list_messages", ("account_id",)
)
GMAIL_GET_MESSAGE_SCHEMA = ToolSchema(
    "gmail.get_message", ("account_id", "message_id")
)
