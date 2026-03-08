"""Shell command execution tool."""

import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Dict, List

from .base import Tool

# Maximum combined stdout+stderr before truncation (~10K tokens).
# Matches Gemini CLI's default threshold of 40,000 characters.
_MAX_OUTPUT_CHARS = 40_000

# Number of bytes to sniff for binary detection.
_BINARY_SNIFF_BYTES = 8_192


def _is_binary(data: bytes) -> bool:
    """Return True if data looks like binary (null bytes present)."""
    return b"\x00" in data[:_BINARY_SNIFF_BYTES]


def _decode(raw: bytes) -> str:
    """Decode bytes to str, flagging binary content."""
    if not raw:
        return ""
    if _is_binary(raw):
        return f"[binary output — {len(raw):,} bytes not shown]"
    return raw.decode("utf-8", errors="replace")


def _truncate_tail(text: str, max_chars: int) -> str:
    """Keep the tail of text (most recent output), noting how much was omitted."""
    if len(text) <= max_chars:
        return text
    omitted = len(text) - max_chars
    return f"[... {omitted:,} chars omitted (showing last {max_chars:,}) ...]\n" + text[-max_chars:]


class ShellTool(Tool):
    """Tool for executing shell commands."""

    @property
    def name(self) -> str:
        return "run_shell_command"

    @property
    def description(self) -> str:
        return (
            "Execute a shell command and return its output. "
            "Each call runs in a fresh stateless bash session; there is no shared state between calls. "
            "The timeout is inactivity-based: it resets whenever the command produces output, "
            "so a command that prints steadily can run longer than the timeout value. "
            "For fire-and-forget tasks (servers, watchers), set is_background=true to detach "
            "the process and return its PID immediately."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to execute.",
                },
                "working_directory": {
                    "type": "string",
                    "description": (
                        "Working directory for the command. "
                        "Must be an existing directory. "
                        "Defaults to the current working directory."
                    ),
                },
                "timeout": {
                    "type": "number",
                    "description": (
                        "Inactivity timeout in seconds (default: 120). "
                        "Resets whenever the command produces output. "
                        "Use is_background=true for commands that should run indefinitely."
                    ),
                    "default": 120,
                },
                "is_background": {
                    "type": "boolean",
                    "description": (
                        "If true, start the command detached from the terminal and return its PID "
                        "immediately without waiting for it to finish. stdout/stderr are discarded. "
                        "Useful for long-running servers or file watchers."
                    ),
                    "default": False,
                },
            },
            "required": ["command"],
        }

    @property
    def requires_confirmation(self) -> bool:
        return True

    def execute(
        self,
        command: str,
        working_directory: str = ".",
        timeout: float = 120,
        is_background: bool = False,
    ) -> str:
        """Execute shell command."""
        # Resolve and validate working directory
        try:
            cwd = Path(working_directory).expanduser().resolve()
            if not cwd.is_dir():
                return (
                    f"Error: working_directory '{working_directory}' does not exist "
                    "or is not a directory."
                )
        except Exception as e:
            return f"Error resolving working_directory: {e}"

        if is_background:
            return self._run_background(command, cwd)
        return self._run_foreground(command, cwd, timeout)

    # ------------------------------------------------------------------
    # Background execution
    # ------------------------------------------------------------------

    def _run_background(self, command: str, cwd: Path) -> str:
        """Start command detached; return PID immediately."""
        try:
            proc = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,  # detach from parent process group
            )
            return (
                f"Background process started.\n"
                f"PID: {proc.pid}\n"
                f"Command: {command}\n"
                f"Working directory: {cwd}"
            )
        except Exception as e:
            return f"Error starting background command: {e}"

    # ------------------------------------------------------------------
    # Foreground execution with inactivity timeout
    # ------------------------------------------------------------------

    def _run_foreground(self, command: str, cwd: Path, timeout: float) -> str:
        """Run command, killing it after `timeout` seconds without any output."""
        try:
            proc = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except Exception as e:
            return f"Error starting command: {e}"

        stdout_chunks: List[bytes] = []
        stderr_chunks: List[bytes] = []
        last_activity = [time.monotonic()]
        timed_out = [False]

        def _read(stream, chunks: List[bytes]) -> None:
            for chunk in iter(lambda: stream.read(4096), b""):
                chunks.append(chunk)
                last_activity[0] = time.monotonic()

        t_out = threading.Thread(target=_read, args=(proc.stdout, stdout_chunks), daemon=True)
        t_err = threading.Thread(target=_read, args=(proc.stderr, stderr_chunks), daemon=True)
        t_out.start()
        t_err.start()

        # Poll for inactivity timeout
        while proc.poll() is None:
            if time.monotonic() - last_activity[0] > timeout:
                timed_out[0] = True
                proc.kill()
                break
            time.sleep(0.05)

        t_out.join(timeout=2)
        t_err.join(timeout=2)

        stdout_raw = b"".join(stdout_chunks)
        stderr_raw = b"".join(stderr_chunks)

        if timed_out[0]:
            partial = _decode(stdout_raw + stderr_raw)
            msg = f"Command timed out after {timeout:.0f}s of inactivity.\nCommand: {command}"
            if partial:
                msg += f"\n\nPartial output before timeout:\n{partial}"
            return msg

        return self._format_result(proc.returncode, stdout_raw, stderr_raw)

    # ------------------------------------------------------------------
    # Output formatting
    # ------------------------------------------------------------------

    def _format_result(
        self, returncode: int, stdout_raw: bytes, stderr_raw: bytes
    ) -> str:
        stdout_str = _decode(stdout_raw)
        stderr_str = _decode(stderr_raw)

        # Truncate: keep tail of each stream proportionally
        total = len(stdout_str) + len(stderr_str)
        if total > _MAX_OUTPUT_CHARS:
            # Allocate budget proportionally; give at least 1 char if non-empty
            if stdout_str and stderr_str:
                ratio = len(stdout_str) / total
                stdout_budget = max(1, int(_MAX_OUTPUT_CHARS * ratio))
                stderr_budget = max(1, _MAX_OUTPUT_CHARS - stdout_budget)
            elif stdout_str:
                stdout_budget, stderr_budget = _MAX_OUTPUT_CHARS, 0
            else:
                stdout_budget, stderr_budget = 0, _MAX_OUTPUT_CHARS

            stdout_str = _truncate_tail(stdout_str, stdout_budget)
            stderr_str = _truncate_tail(stderr_str, stderr_budget)

        parts = []
        if stdout_str:
            parts.append(f"STDOUT:\n{stdout_str}")
        if stderr_str:
            parts.append(f"STDERR:\n{stderr_str}")

        if returncode < 0:
            parts.append(f"Exit: killed by signal {-returncode}")
        else:
            parts.append(f"Exit code: {returncode}")

        return "\n\n".join(parts) if parts else f"Command completed with no output.\n\nExit code: {returncode}"
