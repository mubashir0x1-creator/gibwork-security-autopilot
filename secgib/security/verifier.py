from pathlib import Path


def verify_finding(finding):
    path = Path(finding["file"])

    if not path.exists():
        return {
            "verified": False,
            "reason": "Target file no longer exists.",
        }

    lines = path.read_text(
        encoding="utf-8"
    ).splitlines()

    line_number = finding.get("line", 0)

    if line_number < 1 or line_number > len(lines):
        return {
            "verified": False,
            "reason": "Reported line number is outside the file.",
        }

    actual_line = lines[line_number - 1].strip()

    evidence = finding.get(
        "evidence",
        "",
    ).strip()

    verified = (
        not evidence
        or evidence in actual_line
        or actual_line in evidence
    )

    return {
        "verified": verified,
        "line": line_number,
        "actual_code": actual_line,
        "reason": (
            "Finding evidence matches the source line."
            if verified
            else "Finding evidence no longer matches the source line."
        ),
    }


def verify_findings(findings):
    results = []

    for finding in findings:

        verification = verify_finding(
            finding
        )

        result = dict(finding)

        result["verification"] = verification

        results.append(result)

    return results