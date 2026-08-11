import pytest
from pydantic import ValidationError

from app.schemas import (
    CalendarCreateEventArguments,
    CalendarDeleteEventArguments,
    CalendarGetEventArguments,
    CalendarListEventsArguments,
    CalendarUpdateEventArguments,
)


def test_calendar_list_defaults():
    value = CalendarListEventsArguments(account_id="a")
    assert value.calendar_id == "primary"
    assert value.max_results == 20


def test_calendar_write_schemas_require_event_identity():
    with pytest.raises(ValidationError):
        CalendarGetEventArguments(account_id="a", event_id="")
    with pytest.raises(ValidationError):
        CalendarCreateEventArguments(account_id="a", event={})
    with pytest.raises(ValidationError):
        CalendarUpdateEventArguments(account_id="a", event_id="e", event={})
    with pytest.raises(ValidationError):
        CalendarDeleteEventArguments(account_id="a", event_id="")
