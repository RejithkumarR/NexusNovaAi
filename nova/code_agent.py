from dataclasses import dataclass
import subprocess
import tempfile
from pathlib import Path

from .config import get_settings


@dataclass(frozen=True)
class CodeExecutionResult:
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool


class DockerCodeSandbox:
    """Run generated/user-supplied Python in a disposable, networkless container."""

    def __init__(self, image: str | None = None):
        settings = get_settings()
        self.image = image or settings.code_sandbox_image
        self.timeout = settings.code_timeout_seconds
        self.memory_mb = settings.code_memory_mb
        self.cpu_limit = settings.code_cpu_limit

    def run_python(self, source: str) -> CodeExecutionResult:
        if not source.strip():
            raise ValueError("source code cannot be empty")

        with tempfile.TemporaryDirectory(prefix="nova-code-") as tmp:
            source_path = Path(tmp) / "main.py"
            source_path.write_text(source, encoding="utf-8")

            command = [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges",
                "--pids-limit",
                "128",
                "--memory",
                f"{self.memory_mb}m",
                "--cpus",
                str(self.cpu_limit),
                "--read-only",
                "--tmpfs",
                "/tmp:rw,noexec,nosuid,size=64m",
                "-v",
                f"{source_path}:/workspace/main.py:ro",
                self.image,
                "python",
                "/workspace/main.py",
            ]

            try:
                completed = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                return CodeExecutionResult(
                    stdout=exc.stdout or "",
                    stderr=exc.stderr or "execution timed out",
                    exit_code=-1,
                    timed_out=True,
                )
            except FileNotFoundError as exc:
                raise RuntimeError("Docker is required for NOVA code execution") from exc

            return CodeExecutionResult(
                stdout=completed.stdout,
                stderr=completed.stderr,
                exit_code=completed.returncode,
                timed_out=False,
            )
