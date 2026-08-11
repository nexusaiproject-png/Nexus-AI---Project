import pytest

from app.confirmation import ConfirmationRequiredError, ConfirmationSet
from app.developer_agent import DeveloperAgent, DeveloperAgentError, InMemoryDeveloperWorkspace
from app.developer_tools import DeveloperToolFactory
from app.tools import ToolRegistry


@pytest.fixture
def workspace() -> InMemoryDeveloperWorkspace:
    ws = InMemoryDeveloperWorkspace()
    ws.seed_repository("acme", "app", description="demo")
    ws.branches[("acme", "app")] = [{"name": "main"}, {"name": "feature/x"}]
    ws.commits[("acme", "app")] = [{"sha": "c1", "branch": "main"}, {"sha": "c2", "branch": "feature/x"}]
    ws.files[("acme", "app", "README.md")] = {"path": "README.md", "content": "hello", "sha": "sha1", "branch": "main"}
    ws.issues[("acme", "app")] = {1: {"number": 1, "title": "bug", "state": "open"}}
    ws.pull_requests[("acme", "app")] = {2: {"number": 2, "title": "feature", "state": "open"}}
    ws.pull_request_diffs[("acme", "app", 2)] = "diff --git a/README.md b/README.md"
    ws.pull_request_files[("acme", "app", 2)] = [{"filename": "README.md", "status": "modified"}]
    return ws


def registry(workspace: InMemoryDeveloperWorkspace) -> ToolRegistry:
    tools = ToolRegistry()
    for tool in DeveloperToolFactory(workspace).definitions():
        tools.register(tool)
    return tools


@pytest.mark.asyncio
async def test_developer_agent_inspects_repository(workspace: InMemoryDeveloperWorkspace) -> None:
    result = await DeveloperAgent(workspace).inspect("acme/app")
    assert result["repository"]["name"] == "app"
    assert len(result["branches"]) == 2
    assert len(result["open_issues"]) == 1
    assert len(result["open_pull_requests"]) == 1


@pytest.mark.asyncio
async def test_developer_agent_reviews_pull_request(workspace: InMemoryDeveloperWorkspace) -> None:
    result = await DeveloperAgent(workspace).review_pull_request("acme/app", 2)
    assert result["pull_request"]["title"] == "feature"
    assert result["files"] == [{"filename": "README.md", "status": "modified"}]
    assert "diff --git" in result["diff"]


@pytest.mark.asyncio
async def test_developer_tools_read_and_write(workspace: InMemoryDeveloperWorkspace) -> None:
    tools = registry(workspace)
    result = await tools.execute("developer.read_file", {"subject_id": "s1", "repository": "acme/app", "path": "README.md"})
    assert result["content"] == "hello"

    with pytest.raises(ConfirmationRequiredError):
        await tools.execute("developer.create_issue", {"subject_id": "s1", "repository": "acme/app", "title": "new issue"}, call_id="issue-1")

    result = await tools.execute(
        "developer.create_issue",
        {"subject_id": "s1", "repository": "acme/app", "title": "new issue"},
        confirmations=ConfirmationSet(frozenset({"issue-1"})),
        call_id="issue-1",
    )
    assert result["number"] == 2

    updated = await tools.execute(
        "developer.update_file",
        {"subject_id": "s1", "repository": "acme/app", "path": "README.md", "content": "updated", "sha": "sha1"},
        confirmations=ConfirmationSet(frozenset({"file-update"})),
        call_id="file-update",
    )
    assert updated["content"] == "updated"


@pytest.mark.asyncio
async def test_developer_pull_request_inspection_tools(workspace: InMemoryDeveloperWorkspace) -> None:
    tools = registry(workspace)
    assert await tools.execute("developer.get_pull_request_diff", {"subject_id": "s1", "repository": "acme/app", "number": 2}) == "diff --git a/README.md b/README.md"
    assert await tools.execute("developer.list_pull_request_files", {"subject_id": "s1", "repository": "acme/app", "number": 2}) == [{"filename": "README.md", "status": "modified"}]

    with pytest.raises(ConfirmationRequiredError):
        await tools.execute("developer.create_pull_request", {"subject_id": "s1", "repository": "acme/app", "title": "Ship", "head": "feature/x", "base": "main"}, call_id="pr-1")

    created = await tools.execute(
        "developer.create_pull_request",
        {"subject_id": "s1", "repository": "acme/app", "title": "Ship", "head": "feature/x", "base": "main"},
        confirmations=ConfirmationSet(frozenset({"pr-1"})),
        call_id="pr-1",
    )
    assert created["head"] == "feature/x"
    assert created["base"] == "main"


@pytest.mark.asyncio
async def test_developer_tools_reject_unsafe_paths_and_branches(workspace: InMemoryDeveloperWorkspace) -> None:
    tools = registry(workspace)
    with pytest.raises(DeveloperAgentError, match="traversal"):
        await tools.execute("developer.read_file", {"subject_id": "s1", "repository": "acme/app", "path": "../secret"})

    with pytest.raises(DeveloperAgentError, match="invalid branch"):
        await tools.execute(
            "developer.create_branch",
            {"subject_id": "s1", "repository": "acme/app", "branch": "../evil", "base": "main"},
            confirmations=ConfirmationSet(frozenset({"branch-1"})),
            call_id="branch-1",
        )


@pytest.mark.asyncio
async def test_developer_tools_validate_repository_format(workspace: InMemoryDeveloperWorkspace) -> None:
    tools = registry(workspace)
    with pytest.raises(DeveloperAgentError, match="owner/repo"):
        await tools.execute("developer.get_repository", {"subject_id": "s1", "repository": "invalid"})
