from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class DeveloperAgentError(ValueError):
    pass


@dataclass(frozen=True)
class RepositoryRef:
    owner: str
    name: str


class DeveloperWorkspace(Protocol):
    async def get_repository(self, owner: str, repo: str) -> Any: ...
    async def list_branches(self, owner: str, repo: str) -> Any: ...
    async def list_commits(self, owner: str, repo: str, branch: str | None = None) -> Any: ...
    async def read_file(self, owner: str, repo: str, path: str, ref: str | None = None) -> Any: ...
    async def list_issues(self, owner: str, repo: str, state: str = "open") -> Any: ...
    async def get_issue(self, owner: str, repo: str, number: int) -> Any: ...
    async def list_pull_requests(self, owner: str, repo: str, state: str = "open") -> Any: ...
    async def get_pull_request(self, owner: str, repo: str, number: int) -> Any: ...
    async def get_pull_request_diff(self, owner: str, repo: str, number: int) -> Any: ...
    async def list_pull_request_files(self, owner: str, repo: str, number: int) -> Any: ...
    async def create_issue(self, owner: str, repo: str, title: str, body: str | None = None) -> Any: ...
    async def create_branch(self, owner: str, repo: str, branch: str, base: str) -> Any: ...
    async def update_file(self, owner: str, repo: str, path: str, content: str, sha: str, branch: str | None = None) -> Any: ...
    async def create_pull_request(self, owner: str, repo: str, title: str, head: str, base: str, body: str | None = None) -> Any: ...


class InMemoryDeveloperWorkspace:
    """Deterministic workspace adapter for tests and local development."""

    def __init__(self) -> None:
        self.repositories: dict[tuple[str, str], dict[str, Any]] = {}
        self.branches: dict[tuple[str, str], list[dict[str, Any]]] = {}
        self.commits: dict[tuple[str, str], list[dict[str, Any]]] = {}
        self.files: dict[tuple[str, str, str], dict[str, Any]] = {}
        self.issues: dict[tuple[str, str], dict[int, dict[str, Any]]] = {}
        self.pull_requests: dict[tuple[str, str], dict[int, dict[str, Any]]] = {}
        self.pull_request_files: dict[tuple[str, str, int], list[dict[str, Any]]] = {}
        self.pull_request_diffs: dict[tuple[str, str, int], Any] = {}

    def seed_repository(self, owner: str, repo: str, **metadata: Any) -> None:
        self.repositories[(owner, repo)] = {"owner": owner, "name": repo, **metadata}

    async def get_repository(self, owner: str, repo: str) -> Any:
        return self.repositories.get((owner, repo)) or {"owner": owner, "name": repo}

    async def list_branches(self, owner: str, repo: str) -> Any:
        return list(self.branches.get((owner, repo), []))

    async def list_commits(self, owner: str, repo: str, branch: str | None = None) -> Any:
        commits = self.commits.get((owner, repo), [])
        return list(commits) if branch is None else [c for c in commits if c.get("branch") == branch]

    async def read_file(self, owner: str, repo: str, path: str, ref: str | None = None) -> Any:
        validate_repo_path(path)
        item = self.files.get((owner, repo, path))
        if item is None:
            raise DeveloperAgentError(f"file not found: {path}")
        if ref is not None and item.get("branch", "main") != ref:
            raise DeveloperAgentError(f"file not found on ref: {ref}")
        return dict(item)

    async def list_issues(self, owner: str, repo: str, state: str = "open") -> Any:
        return [dict(v) for v in self.issues.get((owner, repo), {}).values() if state == "all" or v.get("state", "open") == state]

    async def get_issue(self, owner: str, repo: str, number: int) -> Any:
        item = self.issues.get((owner, repo), {}).get(number)
        if item is None:
            raise DeveloperAgentError(f"issue not found: {number}")
        return dict(item)

    async def list_pull_requests(self, owner: str, repo: str, state: str = "open") -> Any:
        return [dict(v) for v in self.pull_requests.get((owner, repo), {}).values() if state == "all" or v.get("state", "open") == state]

    async def get_pull_request(self, owner: str, repo: str, number: int) -> Any:
        item = self.pull_requests.get((owner, repo), {}).get(number)
        if item is None:
            raise DeveloperAgentError(f"pull request not found: {number}")
        return dict(item)

    async def get_pull_request_diff(self, owner: str, repo: str, number: int) -> Any:
        if number not in self.pull_requests.get((owner, repo), {}):
            raise DeveloperAgentError(f"pull request not found: {number}")
        return self.pull_request_diffs.get((owner, repo, number), "")

    async def list_pull_request_files(self, owner: str, repo: str, number: int) -> Any:
        if number not in self.pull_requests.get((owner, repo), {}):
            raise DeveloperAgentError(f"pull request not found: {number}")
        return [dict(v) for v in self.pull_request_files.get((owner, repo, number), [])]

    async def create_issue(self, owner: str, repo: str, title: str, body: str | None = None) -> Any:
        items = self.issues.setdefault((owner, repo), {})
        number = max(items, default=0) + 1
        issue = {"number": number, "title": title, "body": body, "state": "open"}
        items[number] = issue
        return dict(issue)

    async def create_branch(self, owner: str, repo: str, branch: str, base: str) -> Any:
        if not safe_branch_name(branch) or not safe_branch_name(base):
            raise DeveloperAgentError("invalid branch name")
        branches = self.branches.setdefault((owner, repo), [])
        if any(b.get("name") == branch for b in branches):
            raise DeveloperAgentError(f"branch already exists: {branch}")
        result = {"name": branch, "base": base}
        branches.append(result)
        return dict(result)

    async def update_file(self, owner: str, repo: str, path: str, content: str, sha: str, branch: str | None = None) -> Any:
        validate_repo_path(path)
        if branch is not None and not safe_branch_name(branch):
            raise DeveloperAgentError("invalid branch name")
        key = (owner, repo, path)
        item = self.files.get(key)
        if item is None:
            raise DeveloperAgentError(f"file not found: {path}")
        if item.get("sha") != sha:
            raise DeveloperAgentError("file sha mismatch")
        item = {**item, "content": content, "branch": branch or item.get("branch", "main"), "sha": f"updated-{sha}"}
        self.files[key] = item
        return dict(item)

    async def create_pull_request(self, owner: str, repo: str, title: str, head: str, base: str, body: str | None = None) -> Any:
        if not title.strip() or not safe_branch_name(head) or not safe_branch_name(base):
            raise DeveloperAgentError("invalid pull request arguments")
        items = self.pull_requests.setdefault((owner, repo), {})
        number = max(items, default=0) + 1
        pr = {"number": number, "title": title, "body": body, "head": head, "base": base, "state": "open"}
        items[number] = pr
        return dict(pr)


def parse_repo(repository: str) -> RepositoryRef:
    parts = [p for p in repository.strip().split("/") if p]
    if len(parts) != 2 or any(p in {".", ".."} for p in parts):
        raise DeveloperAgentError("repository must be in owner/repo form")
    return RepositoryRef(parts[0], parts[1])


def validate_repo_path(path: str) -> str:
    normalized = path.replace("\\", "/").strip()
    if not normalized or normalized.startswith("/") or "\x00" in normalized:
        raise DeveloperAgentError("invalid repository path")
    parts = [p for p in normalized.split("/") if p]
    if any(p in {".", ".."} for p in parts):
        raise DeveloperAgentError("path traversal is not allowed")
    return normalized


def safe_branch_name(branch: str) -> bool:
    value = branch.strip()
    return bool(value) and not value.startswith("/") and ".." not in value and "\\" not in value and "\x00" not in value


class DeveloperAgent:
    """Safe orchestration boundary for developer-focused repository tools."""

    def __init__(self, workspace: DeveloperWorkspace) -> None:
        self.workspace = workspace

    async def inspect(self, repository: str) -> dict[str, Any]:
        ref = parse_repo(repository)
        return {
            "repository": await self.workspace.get_repository(ref.owner, ref.name),
            "branches": await self.workspace.list_branches(ref.owner, ref.name),
            "open_issues": await self.workspace.list_issues(ref.owner, ref.name, "open"),
            "open_pull_requests": await self.workspace.list_pull_requests(ref.owner, ref.name, "open"),
        }

    async def review_pull_request(self, repository: str, number: int) -> dict[str, Any]:
        ref = parse_repo(repository)
        return {
            "pull_request": await self.workspace.get_pull_request(ref.owner, ref.name, number),
            "files": await self.workspace.list_pull_request_files(ref.owner, ref.name, number),
            "diff": await self.workspace.get_pull_request_diff(ref.owner, ref.name, number),
        }
