from typing import Any
from datetime import datetime

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

class FileCreateArguments(BaseModel):
    subject_id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=500)
    content: str = ""

class FileListArguments(BaseModel):
    subject_id: str = Field(min_length=1)

class FileReadArguments(BaseModel):
    subject_id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=500)

class FileUpdateArguments(BaseModel):
    subject_id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=500)
    content: str = ""

class FileDeleteArguments(BaseModel):
    subject_id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=500)

class MeetingConnectArguments(BaseModel):
    subject_id: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    account_id: str = Field(min_length=1)

class MeetingCreateArguments(BaseModel):
    subject_id: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=300)
    starts_at: datetime
    ends_at: datetime | None = None
    join_url: str | None = None
    transcript: str | None = None
    recording_url: str | None = None

class MeetingListArguments(BaseModel):
    subject_id: str = Field(min_length=1)
    provider: str | None = None

class MeetingGetArguments(BaseModel):
    subject_id: str = Field(min_length=1)
    meeting_id: str = Field(min_length=1)

class MeetingUpdateArguments(BaseModel):
    subject_id: str = Field(min_length=1)
    meeting_id: str = Field(min_length=1)
    title: str | None = Field(default=None, min_length=1, max_length=300)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    join_url: str | None = None
    transcript: str | None = None
    recording_url: str | None = None

class MeetingDeleteArguments(BaseModel):
    subject_id: str = Field(min_length=1)
    meeting_id: str = Field(min_length=1)

class DeveloperRepositoryArguments(BaseModel):
    subject_id: str = Field(min_length=1)
    repository: str = Field(min_length=3)

class DeveloperListBranchesArguments(DeveloperRepositoryArguments):
    pass

class DeveloperListCommitsArguments(DeveloperRepositoryArguments):
    branch: str | None = None

class DeveloperReadFileArguments(DeveloperRepositoryArguments):
    path: str = Field(min_length=1, max_length=1000)
    ref: str | None = None

class DeveloperListIssuesArguments(DeveloperRepositoryArguments):
    state: str = Field(default="open", pattern="^(open|closed|all)$")

class DeveloperGetIssueArguments(DeveloperRepositoryArguments):
    number: int = Field(ge=1)

class DeveloperListPullRequestsArguments(DeveloperRepositoryArguments):
    state: str = Field(default="open", pattern="^(open|closed|all)$")

class DeveloperGetPullRequestArguments(DeveloperRepositoryArguments):
    number: int = Field(ge=1)

class DeveloperListPullRequestFilesArguments(DeveloperGetPullRequestArguments):
    pass

class DeveloperCreateIssueArguments(DeveloperRepositoryArguments):
    title: str = Field(min_length=1, max_length=300)
    body: str | None = Field(default=None, max_length=10000)

class DeveloperBranchArguments(DeveloperRepositoryArguments):
    branch: str = Field(min_length=1, max_length=200)
    base: str = Field(min_length=1, max_length=200)

class DeveloperCreatePullRequestArguments(DeveloperRepositoryArguments):
    title: str = Field(min_length=1, max_length=300)
    head: str = Field(min_length=1, max_length=200)
    base: str = Field(min_length=1, max_length=200)
    body: str | None = Field(default=None, max_length=10000)

class DeveloperUpdateFileArguments(DeveloperRepositoryArguments):
    path: str = Field(min_length=1, max_length=1000)
    content: str = ""
    sha: str = Field(min_length=1)
    branch: str | None = None
