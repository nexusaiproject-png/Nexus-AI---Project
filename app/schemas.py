from typing import Any

from pydantic import BaseModel, Field


class GmailListMessagesArguments(BaseModel):
    account_id: str = Field(min_length=1)
    max_results: int = Field(default=20, ge=1, le=100)
    query: str | None = None


class GmailGetMessageArguments(BaseModel):
    account_id: str = Field(min_length=1)
    message_id: str = Field(min_length=1)


class CalendarListEventsArguments(BaseModel):
    account_id: str = Field(min_length=1)
    calendar_id: str = Field(default="primary", min_length=1)
    max_results: int = Field(default=20, ge=1, le=250)
    time_min: str | None = None
    time_max: str | None = None


class CalendarGetEventArguments(BaseModel):
    account_id: str = Field(min_length=1)
    calendar_id: str = Field(default="primary", min_length=1)
    event_id: str = Field(min_length=1)


class CalendarCreateEventArguments(BaseModel):
    account_id: str = Field(min_length=1)
    calendar_id: str = Field(default="primary", min_length=1)
    event: dict[str, Any] = Field(min_length=1)


class CalendarUpdateEventArguments(BaseModel):
    account_id: str = Field(min_length=1)
    calendar_id: str = Field(default="primary", min_length=1)
    event_id: str = Field(min_length=1)
    event: dict[str, Any] = Field(min_length=1)


class CalendarDeleteEventArguments(BaseModel):
    account_id: str = Field(default="primary", min_length=1)
    calendar_id: str = Field(default="primary", min_length=1)
    event_id: str = Field(min_length=1)


class TaskCreateArguments(BaseModel):
    subject_id: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    due_at: str | None = None


class TaskListArguments(BaseModel):
    subject_id: str = Field(min_length=1)
    completed: bool | None = None


class TaskGetArguments(BaseModel):
    subject_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)


class TaskUpdateArguments(BaseModel):
    subject_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    completed: bool | None = None
    due_at: str | None = None


class TaskDeleteArguments(BaseModel):
    subject_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
