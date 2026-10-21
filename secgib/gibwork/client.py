
"""Windows-compatible bridge to the official Gibwork CLI."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class GibworkResult:
    """Result of a Gibwork CLI operation."""

    ok: bool
    command: list[str]
    stdout: str = ""
    stderr: str = ""
    data: Any = None
    error: str | None = None


class GibworkClient:
    """Run safe, read-only Gibwork CLI operations without a shell."""

    def __init__(self, timeout: int = 90) -> None:
        if timeout < 1:
            raise ValueError("timeout must be at least 1 second")
        self.timeout = timeout

    @staticmethod
    def _base_command() -> list[str] | None:
        node = shutil.which("node")
        if not node:
            return None

        node_dir = Path(node).parent
        npx_cli = node_dir / "node_modules" / "npm" / "bin" / "npx-cli.js"

        if not npx_cli.is_file():
            return None

        return [
            node,
            str(npx_cli),
            "--yes",
            "@gibwork/cli",
        ]

    def version(self) -> GibworkResult:
        return self._diagnostic(["--version"])

    def mcp_doctor(self) -> GibworkResult:
        return self._diagnostic(["mcp", "doctor"])

    def available_tasks(
        self,
        page: int = 1,
        limit: int = 15,
    ) -> GibworkResult:
        """Discover available tasks using the CLI's JSON output.

        This method is read-only. It does not create tasks or submissions
        and does not approve payments.
        """
        if isinstance(page, bool) or not isinstance(page, int) or page < 1:
            return GibworkResult(
                ok=False,
                command=[],
                error="page must be a positive integer.",
            )

        if (
            isinstance(limit, bool)
            or not isinstance(limit, int)
            or not 1 <= limit <= 100
        ):
            return GibworkResult(
                ok=False,
                command=[],
                error="limit must be an integer between 1 and 100.",
            )

        base = self._base_command()
        if base is None:
            return GibworkResult(
                ok=False,
                command=[],
                error=(
                    "Node.js or npm's npx-cli.js was not found "
                    "at the expected location."
                ),
            )

        command = [
            *base,
            "--json",
            "task",
            "available",
            "--page",
            str(page),
            "--limit",
            str(limit),
        ]
        result = self._run(command)

        # Parse JSON on both success and failure. The CLI can report
        # structured credential errors in its JSON output.
        if result.stdout:
            try:
                result.data = json.loads(result.stdout)
            except json.JSONDecodeError:
                if result.ok:
                    result.ok = False
                    result.error = (
                        "Gibwork CLI succeeded but returned invalid JSON."
                    )
                return result

        if not result.ok and isinstance(result.data, dict):
            error_data = result.data.get("error")
            if isinstance(error_data, dict):
                message = error_data.get("message")
                if isinstance(message, str) and message.strip():
                    result.error = message
            elif isinstance(error_data, str) and error_data.strip():
                result.error = error_data

        return result

    def _diagnostic(self, arguments: list[str]) -> GibworkResult:
        base = self._base_command()

        if base is None:
            return GibworkResult(
                ok=False,
                command=[],
                error=(
                    "Node.js or npm's npx-cli.js was not found "
                    "at the expected location."
                ),
            )

        return self._run([*base, *arguments])

    def _run(self, command: list[str]) -> GibworkResult:
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout,
                check=False,
                shell=False,
            )
        except subprocess.TimeoutExpired:
            return GibworkResult(
                ok=False,
                command=command,
                error=f"Gibwork CLI timed out after {self.timeout} seconds.",
            )
        except OSError as exc:
            return GibworkResult(
                ok=False,
                command=command,
                error=f"Could not start Gibwork CLI: {exc}",
            )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        return GibworkResult(
            ok=result.returncode == 0,
            command=command,
            stdout=stdout,
            stderr=stderr,
            error=(
                None
                if result.returncode == 0
                else stderr
                or stdout
                or f"Gibwork CLI exited with code {result.returncode}."
            ),
        )
