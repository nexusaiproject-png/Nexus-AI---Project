from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


SUPPORTED_PROVIDERS = {"zoom", "google_meet", "microsoft_teams"}


class MeetingError(ValueError):
    pass


class MeetingNotFoundError(MeetingError):
    pass


@dataclass(frozen=True)
class Meeting:
    id: str
    subject_id: str
    provider: str
    title: str
    starts_at: datetime
    ends_at: datetime | None = None
    join_url: str | None = None
    transcript: str | None = None
    recording_url: str | None = None


@dataclass(frozen=True)
class MeetingConnection:
    provider: str
    account_id: str
    connected: bool = True


class MeetingStore:
    def __init__(self) -> None:
        self._items: dict[str, Meeting] = {}
        self._connections: dict[tuple[str, str], MeetingConnection] = {}

    def connect(self, subject_id: str, connection: MeetingConnection) -> MeetingConnection:
        if not subject_id.strip():
            raise MeetingError("subject_id is required")
        provider = normalize_provider(connection.provider)
        if provider not in SUPPORTED_PROVIDERS:
            raise MeetingError(f"unsupported meeting provider: {provider}")
        normalized = replace(connection, provider=provider)
        self._connections[(subject_id, provider)] = normalized
        return normalized

    def connections(self, subject_id: str) -> tuple[MeetingConnection, ...]:
        return tuple(c for (sid, _), c in self._connections.items() if sid == subject_id)

    def create(self, meeting: Meeting) -> Meeting:
        if meeting.id in self._items:
            raise MeetingError(f"meeting already exists: {meeting.id}")
        if not meeting.subject_id.strip():
            raise MeetingError("subject_id is required")
        provider = normalize_provider(meeting.provider)
        if provider not in SUPPORTED_PROVIDERS:
            raise MeetingError(f"unsupported meeting provider: {provider}")
        if not meeting.title.strip():
            raise MeetingError("meeting title is required")
        if meeting.ends_at is not None and meeting.ends_at < meeting.starts_at:
            raise MeetingError("ends_at must not precede starts_at")
        normalized = replace(meeting, provider=provider)
        self._items[meeting.id] = normalized
        return normalized

    def get(self, meeting_id: str, subject_id: str) -> Meeting:
        meeting = self._items.get(meeting_id)
        if meeting is None or meeting.subject_id != subject_id:
            raise MeetingNotFoundError(f"meeting not found: {meeting_id}")
        return meeting

    def list(self, subject_id: str, provider: str | None = None) -> tuple[Meeting, ...]:
        provider = normalize_provider(provider) if provider else None
        return tuple(
            m for m in self._items.values()
            if m.subject_id == subject_id and (provider is None or m.provider == provider)
        )

    def update(self, meeting_id: str, subject_id: str, **changes: Any) -> Meeting:
        current = self.get(meeting_id, subject_id)
        allowed = {"title", "starts_at", "ends_at", "join_url", "transcript", "recording_url"}
        unknown = set(changes) - allowed
        if unknown:
            raise MeetingError(f"unsupported meeting fields: {sorted(unknown)}")
        updated = replace(current, **changes)
        if updated.ends_at is not None and updated.ends_at < updated.starts_at:
            raise MeetingError("ends_at must not precede starts_at")
        self._items[meeting_id] = updated
        return updated

    def delete(self, meeting_id: str, subject_id: str) -> None:
        self.get(meeting_id, subject_id)
        del self._items[meeting_id]


def make_meeting(subject_id: str, provider: str, title: str, starts_at: datetime, **kwargs: Any) -> Meeting:
    return Meeting(str(uuid4()), subject_id, normalize_provider(provider), title, starts_at, **kwargs)


def normalize_provider(provider: str) -> str:
    aliases = {
        "meet": "google_meet",
        "google-meet": "google_meet",
        "teams": "microsoft_teams",
        "msteams": "microsoft_teams",
    }
    return aliases.get(provider.strip().lower(), provider.strip().lower())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
