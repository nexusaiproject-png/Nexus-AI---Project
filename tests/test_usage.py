from app.usage import LIMITS, UsageLimitExceeded, UsageStore


def test_usage_consumption_is_workspace_scoped():
    store = UsageStore()
    store.consume("ws-a", "free", "ai", 3)
    store.consume("ws-b", "free", "ai", 2)
    assert store.snapshot("ws-a").ai == 3
    assert store.snapshot("ws-b").ai == 2


def test_usage_limit_is_enforced():
    store = UsageStore()
    limit = LIMITS["free"].ai
    store.consume("ws", "free", "ai", limit)
    try:
        store.consume("ws", "free", "ai", 1)
    except UsageLimitExceeded as exc:
        assert exc.metric == "ai"
        assert exc.limit == limit
    else:
        raise AssertionError("usage limit was not enforced")


def test_storage_limit_is_enforced():
    store = UsageStore()
    limit = LIMITS["free"].storage_bytes
    store.consume("ws", "free", "storage_bytes", limit)
    try:
        store.consume("ws", "free", "storage_bytes", 1)
    except UsageLimitExceeded as exc:
        assert exc.metric == "storage_bytes"
    else:
        raise AssertionError("storage limit was not enforced")


def test_rate_limit_blocks_after_plan_threshold():
    store = UsageStore()
    limit = LIMITS["free"].requests_per_minute
    assert all(store.allow_request("ws", "free") for _ in range(limit))
    assert store.allow_request("ws", "free") is False
