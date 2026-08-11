from typing import Any

from app.developer_agent import DeveloperWorkspace, parse_repo, validate_repo_path
from app.schemas import (
    DeveloperBranchArguments,
    DeveloperCreateIssueArguments,
    DeveloperCreatePullRequestArguments,
    DeveloperGetIssueArguments,
    DeveloperGetPullRequestArguments,
    DeveloperListBranchesArguments,
    DeveloperListCommitsArguments,
    DeveloperListIssuesArguments,
    DeveloperListPullRequestFilesArguments,
    DeveloperListPullRequestsArguments,
    DeveloperReadFileArguments,
    DeveloperRepositoryArguments,
    DeveloperUpdateFileArguments,
)
from app.tools import ToolDefinition


class DeveloperToolFactory:
    def __init__(self, workspace: DeveloperWorkspace) -> None:
        self._workspace = workspace

    def definitions(self) -> tuple[ToolDefinition, ...]:
        return (
            ToolDefinition("developer.get_repository", "Inspect repository metadata.", self.get_repository, DeveloperRepositoryArguments),
            ToolDefinition("developer.list_branches", "List repository branches.", self.list_branches, DeveloperListBranchesArguments),
            ToolDefinition("developer.list_commits", "List repository commits, optionally filtered by branch.", self.list_commits, DeveloperListCommitsArguments),
            ToolDefinition("developer.read_file", "Read a repository file at a branch or ref.", self.read_file, DeveloperReadFileArguments),
            ToolDefinition("developer.list_issues", "List repository issues by state.", self.list_issues, DeveloperListIssuesArguments),
            ToolDefinition("developer.get_issue", "Get a repository issue.", self.get_issue, DeveloperGetIssueArguments),
            ToolDefinition("developer.list_pull_requests", "List repository pull requests by state.", self.list_pull_requests, DeveloperListPullRequestsArguments),
            ToolDefinition("developer.get_pull_request", "Get a repository pull request.", self.get_pull_request, DeveloperGetPullRequestArguments),
            ToolDefinition("developer.get_pull_request_diff", "Inspect a pull request diff.", self.get_pull_request_diff, DeveloperGetPullRequestArguments),
            ToolDefinition("developer.list_pull_request_files", "List files changed by a pull request.", self.list_pull_request_files, DeveloperListPullRequestFilesArguments),
            ToolDefinition("developer.create_issue", "Create a repository issue.", self.create_issue, DeveloperCreateIssueArguments, True),
            ToolDefinition("developer.create_branch", "Create a repository branch from a base ref.", self.create_branch, DeveloperBranchArguments, True),
            ToolDefinition("developer.update_file", "Update repository file contents using the current blob SHA.", self.update_file, DeveloperUpdateFileArguments, True),
            ToolDefinition("developer.create_pull_request", "Create a pull request from a branch to a base branch.", self.create_pull_request, DeveloperCreatePullRequestArguments, True),
        )

    @staticmethod
    def _repo(a: dict[str, Any]):
        return parse_repo(a["repository"])

    async def get_repository(self, a: dict[str, Any]) -> Any:
        r = self._repo(a)
        return await self._workspace.get_repository(r.owner, r.name)

    async def list_branches(self, a: dict[str, Any]) -> Any:
        r = self._repo(a)
        return await self._workspace.list_branches(r.owner, r.name)

    async def list_commits(self, a: dict[str, Any]) -> Any:
        r = self._repo(a)
        return await self._workspace.list_commits(r.owner, r.name, a.get("branch"))

    async def read_file(self, a: dict[str, Any]) -> Any:
        r = self._repo(a)
        return await self._workspace.read_file(r.owner, r.name, validate_repo_path(a["path"]), a.get("ref"))

    async def list_issues(self, a: dict[str, Any]) -> Any:
        r = self._repo(a)
        return await self._workspace.list_issues(r.owner, r.name, a["state"])

    async def get_issue(self, a: dict[str, Any]) -> Any:
        r = self._repo(a)
        return await self._workspace.get_issue(r.owner, r.name, a["number"])

    async def list_pull_requests(self, a: dict[str, Any]) -> Any:
        r = self._repo(a)
        return await self._workspace.list_pull_requests(r.owner, r.name, a["state"])

    async def get_pull_request(self, a: dict[str, Any]) -> Any:
        r = self._repo(a)
        return await self._workspace.get_pull_request(r.owner, r.name, a["number"])

    async def get_pull_request_diff(self, a: dict[str, Any]) -> Any:
        r = self._repo(a)
        return await self._workspace.get_pull_request_diff(r.owner, r.name, a["number"])

    async def list_pull_request_files(self, a: dict[str, Any]) -> Any:
        r = self._repo(a)
        return await self._workspace.list_pull_request_files(r.owner, r.name, a["number"])

    async def create_issue(self, a: dict[str, Any]) -> Any:
        r = self._repo(a)
        return await self._workspace.create_issue(r.owner, r.name, a["title"], a.get("body"))

    async def create_branch(self, a: dict[str, Any]) -> Any:
        r = self._repo
        return await self._workspace.create_branch(r.owner, r.name, a["branch"], a["base"])

    async def update_file(self, a: dict[str, Any]) -> Any:
        r = self._repo(a)
        return await self._workspace.update_file(r.owner, r.name, validate_repo_path(a["path"]), a["content"], a["sha"], a.get("branch"))

    async def create_pull_request(self, a: dict[str, Any]) -> Any:
        r = self._repo(a)
        return await self._workspace.create_pull_request(r.owner, r.name, a["title"], a["head"], a["base"], a.get("body"))
