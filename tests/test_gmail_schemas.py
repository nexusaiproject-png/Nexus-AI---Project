import pytest
from pydantic import ValidationError

from app.schemas import GmailGetMessageArguments, GmailListMessagesArguments


def test_list_messages_defaults_are_safe() -> None:
    args = GmailListMessagesArguments(account_id="account-1")
    assert args.max_results == 20
    assert args.query is None


def test_list_messages_rejects_invalid_page_size() -> None:
    with pytest.raises(ValidationError):
        GmailListMessagesArguments(account_id="account-1", max_results=101)


def test_get_message_requires_message_id() -> None:
    with pytest.raises(ValidationError):
        GmailGetMessageArguments(account_id="account-1", message_id="")
