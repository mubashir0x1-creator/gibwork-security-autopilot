# Gibwork Security Autopilot

A Python static-analysis prototype that detects selected potentially unsafe patterns in Python source code and produces human-readable or JSON security findings. It also provides a read-only bridge to the official Gibwork CLI for diagnostics and available-task discovery.

## Features

- AST-based Python source analysis
- Detection of potentially hardcoded secrets
- Detection of `eval()` and `exec()` usage
- Checks for potentially risky subprocess usage
- Detection of potential SQL injection patterns
- Detection of Flask debug configuration
- Severity levels, risk scores, priorities, and remediation guidance
- Source-line evidence verification
- JSON reports for automation and further processing
- Optional integration with the official Gibwork CLI
- CLI and MCP diagnostics
- Read-only Gibwork available-task discovery command
- Automated tests for scanner and CLI-client behavior

## Requirements

- Python 3.10 or newer
- `pytest` for running tests
- Node.js and npm/npx for the optional Gibwork CLI integration
- Appropriate local Gibwork CLI credentials for live task discovery, where required by the installed CLI

The core scanner uses Python's standard library and has no required third-party runtime dependencies.

## Setup

Run these commands from the project root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks virtual-environment activation, you can run the environment's Python executable directly:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Usage

### Show available commands

```powershell
python -m secgib.cli --help
```

### Scan a Python file

```powershell
python -m secgib.cli scan .\fixtures\vulnerable_demo\app.py
```

The report includes finding IDs, severity, source location, risk score, priority, evidence, and suggested remediation.

### Output JSON

Print a JSON report to the console:

```powershell
python -m secgib.cli scan .\fixtures\vulnerable_demo\app.py --json
```

Save a JSON report directly to a file:

```powershell
python -m secgib.cli scan .\fixtures\vulnerable_demo\app.py --json --output .\scan-results.json
```

Validate the saved JSON:

```powershell
python -m json.tool .\scan-results.json
```

The demo intentionally contains unsafe patterns. Use it only for testing; do not use it as production application code.

## Security rules

| Rule | Purpose |
|---|---|
| SEC001 | Potential hardcoded secrets |
| SEC002 | Use of `eval()` |
| SEC003 | Use of `exec()` |
| SEC004 | Potential command injection through subprocess usage |
| SEC005 | Potential SQL injection patterns |
| SEC006 | Flask debug configuration |
| PARSE001 | Python syntax or parsing errors |

Findings are indicators for human review, not proof that a vulnerability is exploitable. Static analysis can miss issues and produce false positives. Evidence verification checks whether reported evidence corresponds to source code; it does not independently prove exploitability.

Risk scores and priorities are triage aids, not guarantees of real-world impact.

## Gibwork CLI integration

The project uses the official Gibwork CLI for optional diagnostics and read-only available-task discovery.

### Check CLI version

```powershell
npx --yes @gibwork/cli --version
```

### Run project diagnostics

```powershell
python -m secgib.cli gibwork-doctor
```

This checks the CLI version and MCP diagnostics. A successful CLI version check does not necessarily mean MCP is ready.

You can also run the official MCP diagnostic directly:

```powershell
npx --yes @gibwork/cli mcp doctor
```

### Discover available tasks

```powershell
python -m secgib.cli gibwork-tasks --page 1 --limit 5
```

Options:

- `--page`: page number, starting at 1
- `--limit`: number of tasks requested, from 1 to 100

This command requests available tasks through the installed CLI. Successful live discovery depends on the credentials and configuration required by that CLI.

**Current integration limitation:** task discovery returned `CREDENTIAL_ERROR` when no wallet was configured. Successful live task discovery has not yet been verified. Do not interpret the existence of this command as proof that live task discovery or submission works.

This prototype does not create wallets, store private keys, submit work, approve payments, or authorize transactions. Never share a private key or seed phrase. Configure credentials locally and review any transaction details and fees before authorizing financial operations.

## Tests

Run the full test suite:

```powershell
python -m pytest -q
```

Compile the project modules:

```powershell
python -m compileall -f secgib
```

The current development test run completed with 25 passing tests. Re-run the suite after making changes to verify the current checkout.

## Limitations

- Only selected Python security patterns are checked.
- Static analysis does not prove that a reported issue is exploitable.
- Findings may include false positives or miss vulnerabilities.
- Evidence verification checks source correspondence, not exploitability.
- Live Gibwork task discovery has not yet been verified with working credentials.
- Task submission and payment workflows are not implemented as verified project features.

## License

No license has been selected yet. Until a license is added, do not assume the project has an open-source license.