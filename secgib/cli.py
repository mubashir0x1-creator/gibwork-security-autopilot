
import argparse
import json
import sys
from pathlib import Path

from secgib.gibwork.client import GibworkClient
from secgib.security.analyzer import analyze_findings
from secgib.security.scanner import scan_python_file
from secgib.security.verifier import verify_findings


def build_parser():
    parser = argparse.ArgumentParser(
        prog="secgib",
        description="Gibwork Security Autopilot",
    )

    subparsers = parser.add_subparsers(dest="command")

    scan_parser = subparsers.add_parser(
        "scan",
        help="Scan a Python file for security issues.",
    )
    scan_parser.add_argument(
        "target",
        help="Path to the Python file to scan.",
    )
    scan_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON.",
    )
    scan_parser.add_argument(
        "--output",
        metavar="PATH",
        help="Write the JSON report to a file.",
    )

    subparsers.add_parser(
        "gibwork-doctor",
        help="Check Gibwork CLI and MCP diagnostics.",
    )

    tasks_parser = subparsers.add_parser(
        "gibwork-tasks",
        help="Discover available Gibwork tasks (read-only).",
    )
    tasks_parser.add_argument(
        "--page",
        type=int,
        default=1,
        help="Page number (default: 1).",
    )
    tasks_parser.add_argument(
        "--limit",
        type=int,
        default=15,
        help="Tasks per page, from 1 to 100 (default: 15).",
    )

    return parser


def print_human_results(target, findings):
    print()
    print("=" * 60)
    print("GIBWORK SECURITY AUTOPILOT")
    print("=" * 60)
    print(f"Target: {target}")
    print(f"Findings: {len(findings)}")
    print()

    if not findings:
        print("No security findings detected.")
        print()
        return

    for index, finding in enumerate(findings, start=1):
        verification = finding.get("verification", {})

        print(f"[{index}] {finding['severity']} {finding['rule_id']}")
        print(f"    {finding['title']}")
        print(f"    File: {finding['file']}")
        print(f"    Line: {finding['line']}")
        print(f"    Risk: {finding['risk_score']}/100")
        print(f"    Priority: {finding['priority']}")
        print(
            "    Evidence verified: "
            f"{'YES' if verification.get('verified') else 'NO'}"
        )
        print(f"    Evidence: {finding['evidence']}")
        print(f"    Fix: {finding['recommendation']}")
        print("-" * 60)

    print(
        "\nNote: Evidence verification checks source matching; "
        "it does not prove exploitability."
    )


def command_scan(args):
    try:
        findings = scan_python_file(args.target)
        findings = analyze_findings(findings)
        findings = verify_findings(findings)

        report = {
            "target": args.target,
            "findings": findings,
        }

        if args.output:
            output_path = Path(args.output)
            output_path.write_text(
                json.dumps(report, indent=2),
                encoding="utf-8",
            )

        if args.json:
            print(json.dumps(report, indent=2))
        elif args.output:
            print(f"JSON report saved to: {args.output}")
        else:
            print_human_results(args.target, findings)

    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


def command_gibwork_doctor():
    client = GibworkClient()

    checks = {
        "version": client.version(),
        "mcp_doctor": client.mcp_doctor(),
    }

    results = {}

    for name, result in checks.items():
        results[name] = {
            "ok": result.ok,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "error": result.error,
        }

    print(json.dumps(results, indent=2))

    return 0 if all(result.ok for result in checks.values()) else 1


def command_gibwork_tasks(args):
    client = GibworkClient()
    result = client.available_tasks(page=args.page, limit=args.limit)

    if result.data is not None:
        print(json.dumps(result.data, indent=2, ensure_ascii=False))
    elif result.ok:
        print(json.dumps({"output": result.stdout}, indent=2))
    else:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": result.error or "Task discovery failed.",
                    "stderr": result.stderr,
                },
                indent=2,
                ensure_ascii=False,
            )
        )

    return 0 if result.ok else 1


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "scan":
        return command_scan(args)

    if args.command == "gibwork-doctor":
        return command_gibwork_doctor()

    if args.command == "gibwork-tasks":
        return command_gibwork_tasks(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
