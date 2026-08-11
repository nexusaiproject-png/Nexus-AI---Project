from pathlib import Path

import pytest

from app.sandbox import Sandbox, SandboxPolicy, SandboxTimeout, SandboxViolation


def test_path_resolution_cannot_escape_workspace(tmp_path: Path) -> None:
    sandbox = Sandbox(SandboxPolicy(workspace_root=tmp_path))
    with pytest.raises(SandboxViolation, match="escapes"):
        sandbox.resolve_path(tmp_path, "../outside.txt")
    with pytest.raises(SandboxViolation, match="absolute"):
        sandbox.resolve_path(tmp_path, "/etc/passwd")


def test_file_size_limit(tmp_path: Path) -> None:
    sandbox = Sandbox(SandboxPolicy(workspace_root=tmp_path, max_file_bytes=8))
    with pytest.raises(SandboxViolation, match="size limit"):
        sandbox.write_file(tmp_path, "data.txt", "123456789")


def test_blocked_imports_and_builtins_are_rejected(tmp_path: Path) -> None:
    sandbox = Sandbox(SandboxPolicy(workspace_root=tmp_path))
    with pytest.raises(SandboxViolation, match="blocked import"):
        sandbox.run_python("import socket\nprint('no')")
    with pytest.raises(SandboxViolation, match="blocked builtin"):
        sandbox.run_python("open('secret', 'w').write('x')")


def test_python_runs_with_isolated_environment(tmp_path: Path) -> None:
    sandbox = Sandbox(SandboxPolicy(workspace_root=tmp_path))
    result = sandbox.run_python("print('sandbox-ok')")
    assert result.return_code == 0
    assert result.stdout.strip() == "sandbox-ok"


def test_python_timeout_is_enforced(tmp_path: Path) -> None:
    sandbox = Sandbox(SandboxPolicy(workspace_root=tmp_path, timeout_seconds=0.05, max_cpu_seconds=1))
    with pytest.raises(SandboxTimeout):
        sandbox.run_python("while True:\n    pass")
