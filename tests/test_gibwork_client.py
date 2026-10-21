
import json
import subprocess
from unittest.mock import Mock, patch

from secgib.gibwork.client import GibworkClient, GibworkResult


def test_version_runs_expected_cli_command():
    expected = GibworkResult(
        ok=True,
        command=["node", "npx-cli.js", "--yes", "@gibwork/cli", "--version"],
        stdout="0.2.4",
    )

    with (
        patch.object(
            GibworkClient,
            "_base_command",
            return_value=["node", "npx-cli.js", "--yes", "@gibwork/cli"],
        ),
        patch.object(GibworkClient, "_run", return_value=expected) as run,
    ):
        result = GibworkClient().version()

    assert result.ok is True
    assert result.stdout == "0.2.4"
    run.assert_called_once_with(
        ["node", "npx-cli.js", "--yes", "@gibwork/cli", "--version"]
    )


def test_mcp_doctor_uses_expected_arguments():
    expected = GibworkResult(ok=True, command=["gibwork", "mcp", "doctor"])

    with (
        patch.object(
            GibworkClient,
            "_base_command",
            return_value=["gibwork"],
        ),
        patch.object(GibworkClient, "_run", return_value=expected) as run,
    ):
        result = GibworkClient().mcp_doctor()

    assert result.ok is True
    run.assert_called_once_with(["gibwork", "mcp", "doctor"])


def test_missing_cli_returns_clear_error():
    with patch.object(GibworkClient, "_base_command", return_value=None):
        result = GibworkClient().version()

    assert result.ok is False
    assert result.command == []
    assert "Node.js" in result.error


def test_run_passes_command_captures_output_and_disables_shell():
    completed = Mock(returncode=0, stdout="  0.2.4\n", stderr="  ")

    with patch(
        "secgib.gibwork.client.subprocess.run",
        return_value=completed,
    ) as run:
        result = GibworkClient()._run(["node", "--version"])

    assert result.ok is True
    assert result.stdout == "0.2.4"
    assert result.stderr == ""
    assert result.error is None
    assert run.call_args.args == (["node", "--version"],)
    assert run.call_args.kwargs["capture_output"] is True
    assert run.call_args.kwargs["shell"] is False


def test_run_reports_cli_failure():
    completed = Mock(returncode=2, stdout="", stderr="  Authentication required\n")

    with patch("secgib.gibwork.client.subprocess.run", return_value=completed):
        result = GibworkClient()._run(["gibwork", "task", "available"])

    assert result.ok is False
    assert result.stderr == "Authentication required"
    assert result.error == "Authentication required"


def test_run_reports_nonzero_exit_without_output():
    completed = Mock(returncode=7, stdout="", stderr="")

    with patch("secgib.gibwork.client.subprocess.run", return_value=completed):
        result = GibworkClient()._run(["gibwork"])

    assert result.ok is False
    assert result.error == "Gibwork CLI exited with code 7."


def test_run_handles_timeout():
    with patch(
        "secgib.gibwork.client.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd=["gibwork"], timeout=3),
    ):
        result = GibworkClient(timeout=3)._run(["gibwork"])

    assert result.ok is False
    assert result.error == "Gibwork CLI timed out after 3 seconds."


def test_run_handles_os_error():
    with patch(
        "secgib.gibwork.client.subprocess.run",
        side_effect=OSError("executable not found"),
    ):
        result = GibworkClient()._run(["gibwork"])

    assert result.ok is False
    assert "Could not start Gibwork CLI" in result.error
    assert "executable not found" in result.error


def test_available_tasks_uses_json_and_parses_response():
    payload = {"ok": True, "tasks": [{"id": "demo-task"}]}
    completed = Mock(
        returncode=0,
        stdout=json.dumps(payload),
        stderr="",
    )

    with (
        patch.object(
            GibworkClient,
            "_base_command",
            return_value=["node", "npx-cli.js", "--yes", "@gibwork/cli"],
        ),
        patch(
            "secgib.gibwork.client.subprocess.run",
            return_value=completed,
        ) as run,
    ):
        result = GibworkClient().available_tasks(page=2, limit=10)

    assert result.ok is True
    assert result.data == payload
    assert run.call_args.args[0] == [
        "node",
        "npx-cli.js",
        "--yes",
        "@gibwork/cli",
        "--json",
        "task",
        "available",
        "--page",
        "2",
        "--limit",
        "10",
    ]


def test_available_tasks_returns_structured_credential_error():
    payload = {
        "ok": False,
        "error": {
            "code": "CREDENTIAL_ERROR",
            "message": "No wallet configured.",
        },
    }
    completed = Mock(
        returncode=10,
        stdout=json.dumps(payload),
        stderr="",
    )

    with (
        patch.object(GibworkClient, "_base_command", return_value=["gibwork"]),
        patch(
            "secgib.gibwork.client.subprocess.run",
            return_value=completed,
        ),
    ):
        result = GibworkClient().available_tasks()

    assert result.ok is False
    assert result.data == payload
    assert result.error == "No wallet configured."


def test_available_tasks_rejects_invalid_pagination_without_running_cli():
    with (
        patch.object(GibworkClient, "_base_command") as base,
        patch("secgib.gibwork.client.subprocess.run") as run,
    ):
        bad_page = GibworkClient().available_tasks(page=0)
        bad_limit = GibworkClient().available_tasks(limit=101)

    assert bad_page.ok is False
    assert "page" in bad_page.error
    assert bad_limit.ok is False
    assert "limit" in bad_limit.error
    base.assert_not_called()
    run.assert_not_called()


def test_available_tasks_rejects_boolean_pagination():
    result = GibworkClient().available_tasks(page=True, limit=False)

    assert result.ok is False
    assert "page" in result.error


def test_available_tasks_handles_invalid_json():
    completed = Mock(returncode=0, stdout="not-json", stderr="")

    with (
        patch.object(GibworkClient, "_base_command", return_value=["gibwork"]),
        patch(
            "secgib.gibwork.client.subprocess.run",
            return_value=completed,
        ),
    ):
        result = GibworkClient().available_tasks()

    assert result.ok is False
    assert result.error == "Gibwork CLI succeeded but returned invalid JSON."


def test_invalid_timeout_is_rejected():
    try:
        GibworkClient(timeout=0)
    except ValueError as exc:
        assert "timeout" in str(exc)
    else:
        raise AssertionError("Expected ValueError for timeout=0")
