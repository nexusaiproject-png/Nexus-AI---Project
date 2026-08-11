from __future__ import annotations

import ast
import os
import resource
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence


class SandboxError(RuntimeError):
    """Base error for fail-closed sandbox operations."""


class SandboxViolation(SandboxError):
    """Raised when a requested operation violates the sandbox policy."""


class SandboxTimeout(SandboxError):
    """Raised when execution exceeds the configured timeout."""


@dataclass(frozen=True)
class SandboxPolicy:
    timeout_seconds: float = 5.0
    max_output_bytes: int = 64 * 1024
    max_memory_bytes: int = 256 * 1024 * 1024
    max_cpu_seconds: int = 3
    max_file_bytes: int = 2 * 1024 * 1024
    max_processes: int = 1
    allowed_commands: tuple[str, ...] = ("python",)
    allowed_env: tuple[str, ...] = ()
    workspace_root: Path | None = None
    blocked_imports: tuple[str, ...] = (
        "ctypes", "multiprocessing", "os", "pathlib", "pty", "resource",
        "socket", "subprocess", "sys", "threading",
    )


@dataclass(frozen=True)
class SandboxResult:
    return_code: int
    stdout: str
    stderr: str
    timed_out: bool = False


@dataclass
class Sandbox:
    policy: SandboxPolicy = field(default_factory=SandboxPolicy)

    def _validate_source(self, source: str) -> None:
        if len(source.encode()) > self.policy.max_file_bytes:
            raise SandboxViolation("source exceeds sandbox file limit")
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            raise SandboxViolation(f"invalid source: {exc.msg}") from exc
        blocked = set(self.policy.blocked_imports)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name.split(".", 1)[0] for a in node.names]
                if any(name in blocked for name in names):
                    raise SandboxViolation("blocked import")
            elif isinstance(node, ast.ImportFrom):
                root = (node.module or "").split(".", 1)[0]
                if root in blocked:
                    raise SandboxViolation("blocked import")
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in {"eval", "exec", "compile", "__import__", "open", "input"}:
                    raise SandboxViolation(f"blocked builtin: {node.func.id}")

    def _workspace(self) -> Path:
        if self.policy.workspace_root is None:
            return Path(tempfile.mkdtemp(prefix="nexus-sandbox-"))
        root = self.policy.workspace_root.resolve()
        root.mkdir(parents=True, exist_ok=True)
        return root

    def resolve_path(self, workspace: Path, relative_path: str) -> Path:
        if not relative_path or Path(relative_path).is_absolute():
            raise SandboxViolation("absolute or empty paths are not allowed")
        candidate = (workspace / relative_path).resolve()
        root = workspace.resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise SandboxViolation("path escapes sandbox workspace") from exc
        return candidate

    def write_file(self, workspace: Path, relative_path: str, content: str) -> Path:
        encoded = content.encode()
        if len(encoded) > self.policy.max_file_bytes:
            raise SandboxViolation("file exceeds sandbox size limit")
        path = self.resolve_path(workspace, relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(encoded)
        return path

    def _preexec(self) -> None:
        resource.setrlimit(resource.RLIMIT_CPU, (self.policy.max_cpu_seconds, self.policy.max_cpu_seconds))
        resource.setrlimit(resource.RLIMIT_AS, (self.policy.max_memory_bytes, self.policy.max_memory_bytes))
        resource.setrlimit(resource.RLIMIT_FSIZE, (self.policy.max_file_bytes, self.policy.max_file_bytes))
        resource.setrlimit(resource.RLIMIT_NPROC, (self.policy.max_processes, self.policy.max_processes))
        resource.setrlimit(resource.RLIMIT_NOFILE, (32, 32))

    def run_python(self, source: str, *, argv: Sequence[str] = ()) -> SandboxResult:
        self._validate_source(source)
        workspace = self._workspace()
        script = self.write_file(workspace, "main.py", source)
        env = {key: os.environ[key] for key in self.policy.allowed_env if key in os.environ}
        env["PYTHONNOUSERSITE"] = "1"
        env["PYTHONHASHSEED"] = "0"
        command = ("python", "-I", "-S", str(script), *argv)
        if command[0] not in self.policy.allowed_commands:
            raise SandboxViolation("command is not allowed")
        try:
            completed = subprocess.run(
                command,
                cwd=workspace,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.policy.timeout_seconds,
                check=False,
                shell=False,
                preexec_fn=self._preexec,
            )
        except subprocess.TimeoutExpired as exc:
            raise SandboxTimeout("sandbox execution timed out") from exc
        stdout = completed.stdout[: self.policy.max_output_bytes]
        stderr = completed.stderr[: self.policy.max_output_bytes]
        return SandboxResult(completed.returncode, stdout, stderr, False)
