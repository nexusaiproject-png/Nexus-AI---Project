import pytest

from app.saas import Plan, Role, SaaSStore, TenantAccessError


def setup_workspace() -> tuple[SaaSStore, str, str, str]:
    store = SaaSStore()
    owner = store.create_user("owner@example.com")
    member = store.create_user("member@example.com")
    outsider = store.create_user("outsider@example.com")
    workspace = store.create_workspace("Acme", owner.id)
    return store, owner.id, member.id, outsider.id


def test_workspace_isolated_by_membership() -> None:
    store, owner_id, member_id, outsider_id = setup_workspace()
    workspace = next(iter(store.workspaces.values()))
    store.add_member(workspace.id, owner_id, member_id)

    assert store.membership(workspace.id, member_id).role is Role.MEMBER
    with pytest.raises(TenantAccessError):
        store.membership(workspace.id, outsider_id)


def test_owner_can_change_plan_and_entitlements_follow_plan() -> None:
    store, owner_id, _, _ = setup_workspace()
    workspace = next(iter(store.workspaces.values()))

    assert workspace.plan is Plan.FREE
    store.set_plan(workspace.id, owner_id, Plan.PRO)

    assert workspace.plan is Plan.PRO
    assert store.subscriptions[workspace.id].plan is Plan.PRO
    assert store.entitlements(workspace.id).monthly_ai_requests == 5_000


def test_non_owner_cannot_change_plan() -> None:
    store, owner_id, member_id, _ = setup_workspace()
    workspace = next(iter(store.workspaces.values()))
    store.add_member(workspace.id, owner_id, member_id)

    with pytest.raises(TenantAccessError):
        store.set_plan(workspace.id, member_id, Plan.TEAM)


def test_usage_is_enforced_per_workspace_plan() -> None:
    store, owner_id, member_id, _ = setup_workspace()
    workspace = next(iter(store.workspaces.values()))
    store.add_member(workspace.id, owner_id, member_id)

    store.record_usage(workspace.id, member_id, ai_requests=100)
    assert store.usage[workspace.id].ai_requests == 100

    with pytest.raises(ValueError, match="ai_requests usage limit exceeded"):
        store.record_usage(workspace.id, member_id, ai_requests=1)


def test_usage_cannot_cross_tenant_boundary() -> None:
    store, _, _, outsider_id = setup_workspace()
    workspace = next(iter(store.workspaces.values()))

    with pytest.raises(TenantAccessError):
        store.record_usage(workspace.id, outsider_id, ai_requests=1)


def test_member_limit_is_plan_based() -> None:
    store, owner_id, member_id, _ = setup_workspace()
    workspace = next(iter(store.workspaces.values()))

    store.add_member(workspace.id, owner_id, member_id)
    another = store.create_user("another@example.com")
    with pytest.raises(ValueError, match="member limit reached"):
        store.add_member(workspace.id, owner_id, another.id)
