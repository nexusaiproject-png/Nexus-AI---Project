from datetime import datetime, timezone

import pytest

from app.meetings import (
    Meeting,
    MeetingConnection,
    MeetingError,
    MeetingNotFoundError,
    MeetingStore,
    make_meeting,
    normalize_provider,
)


def test_provider_aliases_are_normalized() -> None:
    assert normalize_provider("meet") == "google_meet"
    assert normalize_provider("teams") == "microsoft_teams"
    assert normalize_provider("zoom") == "zoom"


def test_meeting_store_is_subject_scoped_and_supports_crud() -> None:
    store = MeetingStore()
    start = datetime(2026, 8, 11, 10, tzinfo=timezone.utc)
    meeting = make_meeting("s1", "meet", "Sprint", start, join_url="https://meet.example/sprint")
    other = make_meeting("s2", "zoom", "Other", start)
    store.create(meeting)
    store.create(other)

    assert store.get(meeting.id, "s1") == meeting
    assert store.list("s1") == (meeting,)
    assert store.list("s1", "google_meet") == (meeting,)
    with pytest.raises(MeetingNotFoundError):
        store.get(other.id, "s1")

    updated = store.update(meeting.id, "s1", title="Sprint planning", transcript="Decisions")
    assert updated.title == "Sprint planning"
    assert updated.transcript == "Decisions"
    store.delete(meeting.id, "s1")
    with pytest.raises(MeetingNotFoundError):
        store.get(meeting.id, "s1")


def test_meeting_store_validates_provider_and_time_range() -> None:
    store = MeetingStore()
    start = datetime(2026, 8, 11, 10, tzinfo=timezone.utc)
    with pytest.raises(MeetingError, match="unsupported meeting provider"):
        store.create(make_meeting("s1", "webex", "Bad", start))
    with pytest.raises(MeetingError, match="ends_at"):
        store.create(make_meeting("s1", "zoom", "Bad", start, ends_at=datetime(2026, 8, 11, 9, tzinfo=timezone.utc)))


def test_connections_are_subject_scoped() -> None:
    store = MeetingStore()
    connection = store.connect("s1", MeetingConnection("teams", "acct-1"))
    assert connection.provider == "microsoft_teams"
    assert store.connections("s1") == (connection,)
    assert store.connections("s2") == ()
