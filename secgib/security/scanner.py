import ast
from pathlib import Path


RULES = {
    "SEC001": {
        "title": "Hardcoded Secret",
        "severity": "HIGH",
        "description": "A possible secret, API key, password, or token is hardcoded in source code.",
    },
    "SEC002": {
        "title": "Dangerous eval() Usage",
        "severity": "CRITICAL",
        "description": "eval() can execute attacker-controlled Python code.",
    },
    "SEC003": {
        "title": "Dangerous exec() Usage",
        "severity": "CRITICAL",
        "description": "exec() can execute attacker-controlled Python code.",
    },
    "SEC004": {
        "title": "Command Injection Risk",
        "severity": "CRITICAL",
        "description": "subprocess execution may allow command injection when user-controlled input reaches the command.",
    },
    "SEC005": {
        "title": "SQL Injection Risk",
        "severity": "HIGH",
        "description": "SQL queries appear to be constructed dynamically.",
    },
    "SEC006": {
        "title": "Debug Mode Enabled",
        "severity": "MEDIUM",
        "description": "Debug mode should not be enabled in production.",
    },
}


SECRET_NAMES = {
    "password",
    "passwd",
    "secret",
    "api_key",
    "apikey",
    "token",
    "auth_token",
    "access_token",
    "private_key",
}


def make_finding(rule_id, path, line, evidence):
    rule = RULES[rule_id]

    return {
        "rule_id": rule_id,
        "title": rule["title"],
        "severity": rule["severity"],
        "description": rule["description"],
        "file": str(path),
        "line": line,
        "evidence": evidence.strip(),
    }


def scan_python_file(file_path):
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if path.suffix.lower() != ".py":
        raise ValueError("Only Python files are supported.")

    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()

    findings = []

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return [{
            "rule_id": "PARSE001",
            "title": "Python Syntax Error",
            "severity": "INFO",
            "description": "The file could not be parsed as valid Python.",
            "file": str(path),
            "line": exc.lineno or 1,
            "evidence": str(exc),
        }]

    # -----------------------------------------------------
    # AST security checks
    # -----------------------------------------------------

    for node in ast.walk(tree):

        # eval()
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id == "eval":

                    findings.append(
                        make_finding(
                            "SEC002",
                            path,
                            node.lineno,
                            lines[node.lineno - 1],
                        )
                    )

        # exec()
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id == "exec":

                    findings.append(
                        make_finding(
                            "SEC003",
                            path,
                            node.lineno,
                            lines[node.lineno - 1],
                        )
                    )

        # subprocess
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):

                if node.func.attr in {
                    "run",
                    "Popen",
                    "call",
                    "check_call",
                    "check_output",
                }:

                    if isinstance(node.func.value, ast.Name):
                        if node.func.value.id == "subprocess":

                            findings.append(
                                make_finding(
                                    "SEC004",
                                    path,
                                    node.lineno,
                                    lines[node.lineno - 1],
                                )
                            )

        # Hardcoded secrets
        if isinstance(node, ast.Assign):

            for target in node.targets:

                if isinstance(target, ast.Name):

                    variable_name = target.id.lower()

                    if (
                        variable_name in SECRET_NAMES
                        and isinstance(node.value, ast.Constant)
                        and isinstance(node.value.value, str)
                        and node.value.value.strip()
                    ):

                        findings.append(
                            make_finding(
                                "SEC001",
                                path,
                                node.lineno,
                                lines[node.lineno - 1],
                            )
                        )

        # SQL construction
        if isinstance(node, ast.BinOp):

            source_segment = ast.get_source_segment(
                source,
                node,
            )

            if source_segment:

                upper_segment = source_segment.upper()

                sql_keywords = (
                    "SELECT",
                    "INSERT",
                    "UPDATE",
                    "DELETE",
                )

                if any(
                    keyword in upper_segment
                    for keyword in sql_keywords
                ):

                    findings.append(
                        make_finding(
                            "SEC005",
                            path,
                            node.lineno,
                            source_segment,
                        )
                    )

    # -----------------------------------------------------
    # Flask debug=True
    # -----------------------------------------------------

    for node in ast.walk(tree):

        if isinstance(node, ast.Call):

            if isinstance(node.func, ast.Attribute):

                if node.func.attr == "run":

                    for keyword in node.keywords:

                        if keyword.arg == "debug":

                            if (
                                isinstance(
                                    keyword.value,
                                    ast.Constant,
                                )
                                and keyword.value.value is True
                            ):

                                findings.append(
                                    make_finding(
                                        "SEC006",
                                        path,
                                        node.lineno,
                                        lines[node.lineno - 1],
                                    )
                                )

    # -----------------------------------------------------
    # Deduplicate findings
    # -----------------------------------------------------

    unique_findings = []
    seen = set()

    for finding in findings:

        key = (
            finding["rule_id"],
            finding["file"],
            finding["line"],
        )

        if key in seen:
            continue

        seen.add(key)
        unique_findings.append(finding)

    return unique_findings