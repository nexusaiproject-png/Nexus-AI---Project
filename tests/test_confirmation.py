from app.confirmation import ConfirmationRequiredError, ConfirmationSet, confirmation_id


def test_confirmation_set_allows_only_explicit_approval() -> None:
    confirmations = ConfirmationSet(frozenset({"send_email:call-1"}))
    assert confirmations.allows("send_email:call-1")
    assert not confirmations.allows("send_email:call-2")


def test_confirmation_id_prefers_call_id() -> None:
    assert confirmation_id("send_email", "call-7") == "call-7"
    assert confirmation_id("send_email") == "send_email"


def test_confirmation_error_exposes_actionable_identifier() -> None:
    error = ConfirmationRequiredError("send_email", "call-9")
    assert error.tool_name == "send_email"
    assert error.confirmation_id == "call-9"
