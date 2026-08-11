from typing import Any

from app.meetings import Meeting, MeetingConnection, MeetingStore, make_meeting, normalize_provider
from app.schemas import (
    MeetingConnectArguments,
    MeetingCreateArguments,
    MeetingDeleteArguments,
    MeetingGetArguments,
    MeetingListArguments,
    MeetingUpdateArguments,
)
from app.tools import ToolDefinition


class MeetingToolFactory:
    def __init__(self, store: MeetingStore) -> None:
        self._store = store

    def definitions(self) -> tuple[ToolDefinition, ...]:
        return (
            ToolDefinition("meetings.connect", "Connect a Zoom, Google Meet, or Microsoft Teams account.", self.connect, MeetingConnectArguments, True),
            ToolDefinition("meetings.create", "Create a meeting record for a connected meeting provider.", self.create, MeetingCreateArguments, True),
            ToolDefinition("meetings.list", "List meetings for the current subject.", self.list, MeetingListArguments),
            ToolDefinition("meetings.get", "Get one meeting for the current subject.", self.get, MeetingGetArguments),
            ToolDefinition("meetings.update", "Update meeting metadata, transcript, or recording URL.", self.update, MeetingUpdateArguments, True),
            ToolDefinition("meetings.delete", "Delete a meeting record.", self.delete, MeetingDeleteArguments, True),
        )

    async def connect(self, a: dict[str, Any]) -> Any:
        return self._store.connect(a["subject_id"], MeetingConnection(normalize_provider(a["provider"]), a["account_id"]))

    async def create(self, a: dict[str, Any]) -> Any:
        meeting = make_meeting(a["subject_id"], a["provider"], a["title"], a["starts_at"], ends_at=a.get("ends_at"), join_url=a.get("join_url"), transcript=a.get("transcript"), recording_url=a.get("recording_url"))
        return self._store.create(meeting)

    async def list(self, a: dict[str, Any]) -> Any:
        return self._store.list(a["subject_id"], a.get("provider"))

    async def get(self, a: dict[str, Any]) -> Any:
        return self._store.get(a["meeting_id"], a["subject_id"])

    async def update(self, a: dict[str, Any]) -> Any:
        changes = {k: v for k, v in a.items() if k not in {"subject_id", "meeting_id"} and v is not None}
        return self._store.update(a["meeting_id"], a["subject_id"], **changes)

    async def delete(self, a: dict[str, Any]) -> Any:
        self._store.delete(a["meeting_id"], a["subject_id"])
        return {"deleted": True}
