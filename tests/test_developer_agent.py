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
    return ws


@pytest.mark.asyncio
async def test_developer_agent_inspect_and_subject_safe_tools(workspace: InMemoryDeveloperWorkspace) -> None:
    agent = DeveloperAgent(workspace)
    result = await agent.inspect("acme/app")
    assert result["repository"]["name"] == "app"
    assert len(result["branches"]) == 2
    assert len(result["open_issues"]) == 1


@pytest.mark.asyncio
async def test_developer_tools_read_and_write(workspace: InMemoryDeveloperWorkspace) -> None:
    registry = ToolRegistry()
    for tool in DeveloperToolFactory(workspace).definitions():
        registry.register(tool)

    result = await registry.execute("developer.read_file", {"subject_id": "s1", "repository": "acme/app", "path": "README.md"})
    assert result["content"] == "hello"

    with pytest.raises(ConfirmationRequiredError):
        await registry.execute(
            "developer.create_issue",
            {"subject_id": "s1", "repository": "acme/app", "title": "new issue"},
            call_id="issue-1",
        )

    result = await registry.execute(
        "developer.create_issue",
        {"subject_id": "s1", "repository": "acme/app", "title": "new issue"},
        confirmations=ConfirmationSet(frozenset({"issue-1"})),
        call_id="issue-1",
    )
    assert result["number"] == 2

    updated = await registry.execute(
        "developer.update_file",
        {"subject_id": "s1", "repository": "acme/app", "path": "README.md", "content": "updated", "sha": "sha1"},
        confirmations=ConfirmationSet(frozenset({"file-update"})),
        call_id="file-update",
    )
    assert updated["content"] == "updated"


@pytest.mark.asyncio
async def test_developer_tools_validate_repository_format(workspace: InMemoryDeveloperWorkspace) -> None:
    registry = ToolRegistry()
    for tool in DeveloperToolFactory(workspace).definitions():
        registry.register(tool)
    with pytest.raises(DeveloperAgentError, match="owner/repo"):
        await registry.execute("developer.get_repository", {"subject_id": "s1", "repository": "invalid"})
