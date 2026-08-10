import pytest

from app.permissions import AllowListPermissionChecker


@pytest.mark.asyncio
async def test_allow_list_requires_subject_and_registered_tool() -> None:
    checker = AllowListPermissionChecker(frozenset({"gmail.list_messages"}))

    assert await checker.allowed("gmail.list_messages", "account-1") is True
    assert await checker.allowed("gmail.get_message", "account-1") is False
    assert await checker.allowed("gmail.list_messages", "") is False
