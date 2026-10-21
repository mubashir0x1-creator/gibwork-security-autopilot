
import json
import subprocess
import sys
from pathlib import Path

import pytest

from secgib.security.scanner import scan_python_file
from secgib.security.analyzer import analyze_findings
from secgib.security.verifier import verify_findings


def write_python_file(tmp_path, source):
    path = tmp_path / "sample.py"
    path.write_text(source, encoding="utf-8")
    return path


def test_detects_four_demo_vulnerabilities():
    target = Path("fixtures/vulnerable_demo/app.py")
    findings = scan_python_file(target)
    rule_ids = {finding["rule_id"] for finding in findings}

    assert {"SEC001", "SEC002", "SEC004", "SEC005"} <= rule_ids


def test_detects_exec(tmp_path):
    target = write_python_file(tmp_path, "exec(user_input)\n")
    findings = scan_python_file(target)

    assert any(f["rule_id"] == "SEC003" for f in findings)


def test_rejects_missing_file():
    with pytest.raises(FileNotFoundError):
        scan_python_file("this_file_should_not_exist.py")


def test_rejects_non_python_file(tmp_path):
    target = tmp_path / "sample.txt"
    target.write_text("hello", encoding="utf-8")

    with pytest.raises(ValueError):
        scan_python_file(target)


def test_reports_syntax_error(tmp_path):
    target = write_python_file(tmp_path, "if True print('broken')\n")
    findings = scan_python_file(target)

    assert findings[0]["rule_id"] == "PARSE001"


def test_analyzer_assigns_risk_and_priority():
    findings = [
        {"rule_id": "SEC001", "severity": "HIGH"},
        {"rule_id": "SEC002", "severity": "CRITICAL"},
    ]

    results = analyze_findings(findings)

    assert results[0]["risk_score"] == 95
    assert results[0]["priority"] == "URGENT"
    assert results[1]["risk_score"] == 80
    assert results[1]["priority"] == "HIGH"


def test_verifier_matches_evidence(tmp_path):
    target = write_python_file(tmp_path, "result = eval(user_input)\n")
    finding = {
        "file": str(target),
        "line": 1,
        "evidence": "result = eval(user_input)",
    }

    result = verify_findings([finding])[0]["verification"]

    assert result["verified"] is True


def test_verifier_detects_changed_evidence(tmp_path):
    target = write_python_file(tmp_path, "result = safe_function()\n")
    finding = {
        "file": str(target),
        "line": 1,
        "evidence": "result = eval(user_input)",
    }

    result = verify_findings([finding])[0]["verification"]

    assert result["verified"] is False


def test_cli_json_output():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "secgib.cli",
            "scan",
            "fixtures/vulnerable_demo/app.py",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)

    assert "target" in payload
    assert len(payload["findings"]) >= 4


def test_cli_saves_json_report(tmp_path):
    report_path = tmp_path / "scan-results.json"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "secgib.cli",
            "scan",
            "fixtures/vulnerable_demo/app.py",
            "--output",
            str(report_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    assert report_path.is_file()
    assert "JSON report saved to:" in result.stdout

    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert payload["target"] == "fixtures/vulnerable_demo/app.py"
    assert len(payload["findings"]) >= 4


def test_cli_json_output_and_file_together(tmp_path):
    report_path = tmp_path / "scan-results.json"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "secgib.cli",
            "scan",
            "fixtures/vulnerable_demo/app.py",
            "--json",
            "--output",
            str(report_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    stdout_payload = json.loads(result.stdout)
    file_payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert stdout_payload == file_payload
