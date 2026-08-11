from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4


class Role(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class Plan(StrEnum):
    FREE = "free"
    PRO = "pro"
    TEAM = "team"


@dataclass(frozen=True)
class Entitlements:
    max_members: int
    monthly_ai_requests: int
    monthly_agent_runs: int
    monthly_automation_runs: int
    storage_bytes: int


PLAN_ENTITLEMENTS: dict[Plan, Entitlements] = {
    Plan.FREE: Entitlements(1, 100, 20, 20, 100 * 1024 * 1024),
    Plan.PRO: Entitlements(5, 5_000, 1_000, 500, 10 * 1024 * 1024 * 1024),
    Plan.TEAM: Entitlements(25, 25_000, 5_000, 2_500, 100 * 1024 * 1024 * 1024),
}


@dataclass
class User:
    id: str
    email: str


@dataclass
class Workspace:
    id: str
    name: str
    owner_id: str
    plan: Plan = Plan.FREE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Membership:
    workspace_id: str
    user_id: str
    role: Role


@dataclass
class Subscription:
    workspace_id: str
    plan: Plan
    status: str = "active"
    external_id: str | None = None


@dataclass
class Usage:
    workspace_id: str
    ai_requests: int = 0
    agent_runs: int = 0
    automation_runs: int = 0
    storage_bytes: int = 0


class TenantAccessError(PermissionError):
    pass


class SaaSStore:
    """In-memory SaaS domain store used by the current application architecture."""

    def __init__(self) -> None:
        self.users: dict[str, User] = {}
        self.workspaces: dict[str, Workspace] = {}
        self.memberships: dict[tuple[str, str], Membership] = {}
        self.subscriptions: dict[str, Subscription] = {}
        self.usage: dict[str, Usage] = {}

    def create_user(self, email: str) -> User:
        user = User(id=str(uuid4()), email=email.strip().lower())
        if not user.email:
            raise ValueError("email is required")
        self.users[user.id] = user
        return user

    def create_workspace(self, name: str, owner_id: str) -> Workspace:
        if owner_id not in self.users:
            raise KeyError("user not found")
        workspace = Workspace(id=str(uuid4()), name=name.strip(), owner_id=owner_id)
        if not workspace.name:
            raise ValueError("workspace name is required")
        self.workspaces[workspace.id] = workspace
        self.memberships[(workspace.id, owner_id)] = Membership(workspace.id, owner_id, Role.OWNER)
        self.subscriptions[workspace.id] = Subscription(workspace.id, Plan.FREE)
        self.usage[workspace.id] = Usage(workspace.id)
        return workspace

    def membership(self, workspace_id: str, user_id: str) -> Membership:
        try:
            return self.memberships[(workspace_id, user_id)]
        except KeyError as exc:
            raise TenantAccessError("user is not a member of workspace") from exc

    def add_member(self, workspace_id: str, actor_id: str, user_id: str, role: Role = Role.MEMBER) -> Membership:
        actor = self.membership(workspace_id, actor_id)
        if actor.role not in {Role.OWNER, Role.ADMIN}:
            raise TenantAccessError("only owners and admins can add members")
        if user_id not in self.users:
            raise KeyError("user not found")
        entitlements = self.entitlements(workspace_id)
        member_count = sum(1 for m in self.memberships.values() if m.workspace_id == workspace_id)
        if member_count >= entitlements.max_members:
            raise ValueError("workspace member limit reached")
        membership = Membership(workspace_id, user_id, role)
        self.memberships[(workspace_id, user_id)] = membership
        return membership

    def entitlements(self, workspace_id: str) -> Entitlements:
        workspace = self.workspaces.get(workspace_id)
        if workspace is None:
            raise KeyError("workspace not found")
        return PLAN_ENTITLEMENTS[workspace.plan]

    def set_plan(self, workspace_id: str, actor_id: str, plan: Plan) -> Subscription:
        actor = self.membership(workspace_id, actor_id)
        if actor.role is not Role.OWNER:
            raise TenantAccessError("only the workspace owner can change the plan")
        workspace = self.workspaces[workspace_id]
        workspace.plan = plan
        subscription = Subscription(workspace_id, plan)
        self.subscriptions[workspace_id] = subscription
        return subscription

    def record_usage(self, workspace_id: str, user_id: str, *, ai_requests: int = 0, agent_runs: int = 0, automation_runs: int = 0, storage_bytes: int = 0) -> Usage:
        self.membership(workspace_id, user_id)
        usage = self.usage[workspace_id]
        next_values = {
            "ai_requests": usage.ai_requests + ai_requests,
            "agent_runs": usage.agent_runs + agent_runs,
            "automation_runs": usage.automation_runs + automation_runs,
            "storage_bytes": usage.storage_bytes + storage_bytes,
        }
        limits = self.entitlements(workspace_id)
        limits_map = {"ai_requests": limits.monthly_ai_requests, "agent_runs": limits.monthly_agent_runs, "automation_runs": limits.monthly_automation_runs, "storage_bytes": limits.storage_bytes}
        for key, value in next_values.items():
            if value < 0 or value > limits_map[key]:
                raise ValueError(f"{key} usage limit exceeded")
        usage.ai_requests = next_values["ai_requests"]
        usage.agent_runs = next_values["agent_runs"]
        usage.automation_runs = next_values["automation_runs"]
        usage.storage_bytes = next_values["storage_bytes"]
        return usage
