SEVERITY_SCORES = {
    "CRITICAL": 95,
    "HIGH": 80,
    "MEDIUM": 60,
    "LOW": 35,
    "INFO": 10,
}


def calculate_risk(severity):
    return SEVERITY_SCORES.get(
        severity.upper(),
        0,
    )


def analyze_findings(findings):
    analyzed = []

    for finding in findings:

        severity = finding.get(
            "severity",
            "INFO",
        ).upper()

        risk_score = calculate_risk(severity)

        result = dict(finding)

        result["risk_score"] = risk_score

        if risk_score >= 90:
            priority = "URGENT"
        elif risk_score >= 75:
            priority = "HIGH"
        elif risk_score >= 50:
            priority = "MEDIUM"
        else:
            priority = "LOW"

        result["priority"] = priority

        result["recommendation"] = build_recommendation(
            finding.get("rule_id")
        )

        analyzed.append(result)

    analyzed.sort(
        key=lambda item: item["risk_score"],
        reverse=True,
    )

    return analyzed


def build_recommendation(rule_id):

    recommendations = {
        "SEC001": (
            "Move secrets to environment variables or a dedicated "
            "secret-management system."
        ),
        "SEC002": (
            "Avoid eval(). Use safe parsing or explicit logic instead."
        ),
        "SEC003": (
            "Avoid exec(). Never execute untrusted input as Python code."
        ),
        "SEC004": (
            "Use argument arrays instead of shell commands and validate "
            "all user-controlled input."
        ),
        "SEC005": (
            "Use parameterized SQL queries instead of string concatenation."
        ),
        "SEC006": (
            "Disable debug mode in production deployments."
        ),
        "PARSE001": (
            "Fix the Python syntax error before deploying the application."
        ),
    }

    return recommendations.get(
        rule_id,
        "Review the finding and apply the appropriate security control.",
    )