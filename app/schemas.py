from pydantic import BaseModel, Field


class GmailListMessagesArguments(BaseModel):
    account_id: str = Field(min_length=1)
    max_results: int = Field(default=20, ge=1, le=100)
    query: str | None = None


class GmailGetMessageArguments(BaseModel):
    account_id: str = Field(min_length=1)
    message_id: str = Field(min_length=1)
