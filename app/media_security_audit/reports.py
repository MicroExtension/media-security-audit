"""Report rendering for normalized findings."""

from __future__ import annotations

import json
from collections import Counter
from html import escape
from pathlib import Path

from media_security_audit.models import (
    Finding,
    FindingStatus,
    Mission,
    Report,
    ReportFormat,
    SEVERITY_RANK,
    Severity,
    utc_now,
)


SEVERITY_SCORE: dict[Severity, int] = {
    Severity.CRITICAL: 40,
    Severity.HIGH: 25,
    Severity.MEDIUM: 10,
    Severity.LOW: 3,
    Severity.INFO: 0,
}


def active_findings(findings: list[Finding]) -> list[Finding]:
    return [finding for finding in findings if finding.status != FindingStatus.FALSE_POSITIVE]


def severity_counts(findings: list[Finding]) -> dict[str, int]:
    counts = Counter(finding.severity.value for finding in findings)
    return {
        "critical": counts.get("critical", 0),
        "high": counts.get("high", 0),
        "medium": counts.get("medium", 0),
        "low": counts.get("low", 0),
        "info": counts.get("info", 0),
    }


def sorted_findings(findings: list[Finding]) -> list[Finding]:
    return sorted(
        findings,
        key=lambda finding: (
            -SEVERITY_RANK[finding.severity],
            finding.affected_asset,
            finding.title,
        ),
    )


def risk_score(findings: list[Finding]) -> int:
    return min(100, sum(SEVERITY_SCORE[finding.severity] for finding in active_findings(findings)))


def risk_level(score: int) -> str:
    if score >= 80:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "medium"
    if score > 0:
        return "low"
    return "none"


def executive_summary(findings: list[Finding]) -> str:
    active = active_findings(findings)
    counts = severity_counts(active)

    if not active:
        return "No active findings are included in this report."
    if counts["critical"]:
        return "Immediate remediation is required for critical security findings."
    if counts["high"]:
        return "High-priority remediation should be planned as soon as possible."
    if counts["medium"]:
        return "The audit identified moderate security improvements to prioritize."
    return "The audit identified low-risk hygiene improvements and informational observations."


def scope_summary(mission: Mission) -> dict[str, object]:
    approved = [item for item in mission.scope if item.approved and not item.excluded]
    excluded = [item for item in mission.scope if item.excluded]
    draft = [item for item in mission.scope if not item.approved and not item.excluded]

    return {
        "approved_count": len(approved),
        "excluded_count": len(excluded),
        "draft_count": len(draft),
        "approved_targets": [f"{item.type.value}:{item.value}" for item in approved],
        "excluded_targets": [f"{item.type.value}:{item.value}" for item in excluded],
    }


def display_value(value: object | None) -> str:
    if value is None:
        return "missing"
    text = str(value).strip()
    return " ".join(text.split()) if text else "missing"


def authorization_summary(mission: Mission) -> dict[str, str]:
    return {
        "reference": display_value(mission.authorization_reference),
        "contact": display_value(mission.authorization_contact),
        "authorization_date": display_value(mission.authorization_date),
        "authorization_expires_at": display_value(mission.authorization_expires_at),
        "emergency_contact": display_value(mission.emergency_contact),
        "report_recipients": display_value(mission.report_recipients),
        "evidence_retention_days": display_value(mission.evidence_retention_days),
    }


def remediation_plan(findings: list[Finding], limit: int = 10) -> list[dict[str, str]]:
    prioritized = [
        finding
        for finding in sorted_findings(active_findings(findings))
        if finding.severity != Severity.INFO
    ]
    return [
        {
            "severity": finding.severity.value,
            "asset": finding.affected_asset,
            "title": finding.title,
            "remediation": finding.remediation,
            "counter_test": finding.counter_test,
        }
        for finding in prioritized[:limit]
    ]


def build_report_summary(mission: Mission, findings: list[Finding]) -> dict[str, object]:
    active = active_findings(findings)
    score = risk_score(findings)
    return {
        "generated_at": utc_now().isoformat(),
        "finding_count": len(findings),
        "active_finding_count": len(active),
        "severity_counts": severity_counts(active),
        "risk_score": score,
        "risk_level": risk_level(score),
        "executive_summary": executive_summary(findings),
        "authorization_present": mission.is_authorized,
        "authorization": authorization_summary(mission),
        "scope": scope_summary(mission),
    }


def render_json(mission: Mission, findings: list[Finding]) -> str:
    payload = {
        "mission": mission.model_dump(mode="json"),
        "summary": build_report_summary(mission, findings),
        "remediation_plan": remediation_plan(findings),
        "findings": [finding.model_dump(mode="json") for finding in sorted_findings(findings)],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def render_markdown(mission: Mission, findings: list[Finding]) -> str:
    ordered_findings = sorted_findings(findings)
    summary = build_report_summary(mission, ordered_findings)
    counts = summary["severity_counts"]
    scope = summary["scope"]
    authorization = summary["authorization"]
    plan = remediation_plan(ordered_findings)

    lines = [
        f"# Security Audit Report - {mission.name}",
        "",
        "## Executive Summary",
        "",
        str(summary["executive_summary"]),
        "",
        f"- Risk score: `{summary['risk_score']}/100`",
        f"- Risk level: `{summary['risk_level']}`",
        f"- Active findings: {summary['active_finding_count']}",
        f"- Authorization present: `{str(summary['authorization_present']).lower()}`",
        "",
        "## Mission Context",
        "",
        f"- Mission id: `{mission.id}`",
        f"- Client id: `{mission.client_id}`",
        f"- Audit type: `{mission.audit_type.value}`",
        f"- Mission status: `{mission.status.value}`",
        f"- Authorization reference: `{authorization['reference']}`",
        f"- Authorization contact: `{authorization['contact']}`",
        f"- Authorization date: `{authorization['authorization_date']}`",
        f"- Authorization expires: `{authorization['authorization_expires_at']}`",
        f"- Emergency contact: `{authorization['emergency_contact']}`",
        f"- Report recipients: `{authorization['report_recipients']}`",
        f"- Evidence retention days: `{authorization['evidence_retention_days']}`",
        "",
        "## Scope Summary",
        "",
        f"- Approved targets: {scope['approved_count']}",
        f"- Excluded targets: {scope['excluded_count']}",
        f"- Draft targets: {scope['draft_count']}",
        "",
    ]

    approved_targets = scope["approved_targets"]
    if approved_targets:
        lines.extend(["Approved target list:", ""])
        lines.extend(f"- `{target}`" for target in approved_targets)
        lines.append("")

    lines.extend(
        [
            "## Severity Counts",
            "",
            f"- Critical: {counts['critical']}",
            f"- High: {counts['high']}",
            f"- Medium: {counts['medium']}",
            f"- Low: {counts['low']}",
            f"- Info: {counts['info']}",
            "",
            "## Remediation Plan",
            "",
        ]
    )

    if plan:
        for index, item in enumerate(plan, start=1):
            lines.extend(
                [
                    f"{index}. `{item['severity']}` {item['title']} on `{item['asset']}`",
                    f"   Remediation: {item['remediation']}",
                    f"   Counter-test: {item['counter_test']}",
                    "",
                ]
            )
    else:
        lines.extend(["No prioritized remediation items were included.", ""])

    lines.extend(["## Findings", ""])

    if not ordered_findings:
        lines.append("No findings were included in this report.")
        return "\n".join(lines) + "\n"

    for finding in ordered_findings:
        lines.extend(
            [
                f"### {finding.title}",
                "",
                f"- Severity: `{finding.severity.value}`",
                f"- Asset: `{finding.affected_asset}`",
                f"- Category: `{finding.category}`",
                f"- Status: `{finding.status.value}`",
                f"- Confidence: `{finding.confidence:.2f}`",
                f"- Sources: `{', '.join(finding.sources)}`",
                "",
                "**Proof**",
                "",
                finding.proof,
                "",
                "**Risk**",
                "",
                finding.risk,
                "",
                "**Remediation**",
                "",
                finding.remediation,
                "",
                "**Counter-test**",
                "",
                finding.counter_test,
                "",
            ]
        )

    return "\n".join(lines)


def _render_html_remediation_plan(plan: list[dict[str, str]]) -> str:
    if not plan:
        return "<p>No prioritized remediation items were included.</p>"

    rows = []
    for item in plan:
        rows.append(
            f"""
<tr>
  <td>{escape(item["severity"])}</td>
  <td>{escape(item["asset"])}</td>
  <td>{escape(item["title"])}</td>
  <td>{escape(item["remediation"])}</td>
  <td>{escape(item["counter_test"])}</td>
</tr>
""".strip()
        )

    return f"""
<table>
  <thead>
    <tr>
      <th>Severity</th>
      <th>Asset</th>
      <th>Finding</th>
      <th>Remediation</th>
      <th>Counter-test</th>
    </tr>
  </thead>
  <tbody>
    {"".join(rows)}
  </tbody>
</table>
""".strip()


def render_html(mission: Mission, findings: list[Finding]) -> str:
    ordered_findings = sorted_findings(findings)
    summary = build_report_summary(mission, ordered_findings)
    counts = summary["severity_counts"]
    scope = summary["scope"]
    authorization = summary["authorization"]
    plan = remediation_plan(ordered_findings)
    finding_blocks = []

    for finding in ordered_findings:
        finding_blocks.append(
            f"""
<article class="finding severity-{escape(finding.severity.value)}">
  <h2>{escape(finding.title)}</h2>
  <dl>
    <dt>Severity</dt><dd>{escape(finding.severity.value)}</dd>
    <dt>Asset</dt><dd>{escape(finding.affected_asset)}</dd>
    <dt>Category</dt><dd>{escape(finding.category)}</dd>
    <dt>Status</dt><dd>{escape(finding.status.value)}</dd>
    <dt>Confidence</dt><dd>{finding.confidence:.2f}</dd>
    <dt>Sources</dt><dd>{escape(", ".join(finding.sources))}</dd>
  </dl>
  <h3>Proof</h3>
  <pre>{escape(finding.proof)}</pre>
  <h3>Risk</h3>
  <p>{escape(finding.risk)}</p>
  <h3>Remediation</h3>
  <p>{escape(finding.remediation)}</p>
  <h3>Counter-test</h3>
  <p>{escape(finding.counter_test)}</p>
</article>
""".strip()
        )

    if not finding_blocks:
        finding_blocks.append("<p>No findings were included in this report.</p>")

    approved_targets = scope["approved_targets"]
    approved_targets_html = (
        "".join(f"<li><code>{escape(target)}</code></li>" for target in approved_targets)
        if approved_targets
        else "<li>No approved targets were recorded.</li>"
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Security Audit Report - {escape(mission.name)}</title>
  <style>
    body {{ font-family: Arial, sans-serif; line-height: 1.5; margin: 2rem; color: #1f2933; background: #ffffff; }}
    header {{ border-bottom: 1px solid #d9e2ec; margin-bottom: 1.5rem; }}
    section {{ margin: 1.75rem 0; }}
    .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: .75rem; }}
    .metric {{ border: 1px solid #d9e2ec; border-radius: 6px; padding: .75rem; background: #fbfcfd; }}
    .metric strong {{ display: block; font-size: 1.5rem; }}
    .executive {{ border-left: 6px solid #1570ef; background: #f8fafc; padding: 1rem; }}
    .finding {{ border: 1px solid #d9e2ec; border-radius: 6px; padding: 1rem; margin: 1rem 0; }}
    .severity-critical {{ border-left: 6px solid #b42318; }}
    .severity-high {{ border-left: 6px solid #d92d20; }}
    .severity-medium {{ border-left: 6px solid #dc6803; }}
    .severity-low {{ border-left: 6px solid #1570ef; }}
    .severity-info {{ border-left: 6px solid #667085; }}
    dl {{ display: grid; grid-template-columns: 160px 1fr; gap: .25rem .75rem; }}
    dt {{ font-weight: bold; }}
    pre {{ background: #f8fafc; border: 1px solid #d9e2ec; padding: .75rem; overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border: 1px solid #d9e2ec; padding: .5rem; vertical-align: top; text-align: left; }}
    th {{ background: #f8fafc; }}
    code {{ background: #eef2f6; padding: .1rem .25rem; border-radius: 4px; }}
  </style>
</head>
<body>
  <header>
    <h1>Security Audit Report</h1>
    <p>{escape(mission.name)} | Mission {escape(mission.id)}</p>
  </header>
  <section class="executive">
    <h2>Executive Summary</h2>
    <p>{escape(str(summary["executive_summary"]))}</p>
  </section>
  <section>
    <h2>Risk Overview</h2>
    <div class="summary">
      <div class="metric"><span>Risk score</span><strong>{summary["risk_score"]}/100</strong></div>
      <div class="metric"><span>Risk level</span><strong>{escape(str(summary["risk_level"]))}</strong></div>
      <div class="metric"><span>Active findings</span><strong>{summary["active_finding_count"]}</strong></div>
      <div class="metric"><span>Critical</span><strong>{counts["critical"]}</strong></div>
      <div class="metric"><span>High</span><strong>{counts["high"]}</strong></div>
      <div class="metric"><span>Medium</span><strong>{counts["medium"]}</strong></div>
      <div class="metric"><span>Low</span><strong>{counts["low"]}</strong></div>
      <div class="metric"><span>Info</span><strong>{counts["info"]}</strong></div>
    </div>
  </section>
  <section>
    <h2>Mission Context</h2>
    <dl>
      <dt>Client ID</dt><dd>{escape(mission.client_id)}</dd>
      <dt>Audit type</dt><dd>{escape(mission.audit_type.value)}</dd>
      <dt>Mission status</dt><dd>{escape(mission.status.value)}</dd>
      <dt>Authorization</dt><dd>{escape(authorization["reference"])}</dd>
      <dt>Authorization contact</dt><dd>{escape(authorization["contact"])}</dd>
      <dt>Authorization date</dt><dd>{escape(authorization["authorization_date"])}</dd>
      <dt>Authorization expires</dt><dd>{escape(authorization["authorization_expires_at"])}</dd>
      <dt>Emergency contact</dt><dd>{escape(authorization["emergency_contact"])}</dd>
      <dt>Report recipients</dt><dd>{escape(authorization["report_recipients"])}</dd>
      <dt>Evidence retention days</dt><dd>{escape(authorization["evidence_retention_days"])}</dd>
      <dt>Approved targets</dt><dd>{scope["approved_count"]}</dd>
      <dt>Excluded targets</dt><dd>{scope["excluded_count"]}</dd>
    </dl>
    <h3>Approved target list</h3>
    <ul>{approved_targets_html}</ul>
  </section>
  <section>
    <h2>Remediation Plan</h2>
    {_render_html_remediation_plan(plan)}
  </section>
  <section>
    <h2>Findings</h2>
    {"".join(finding_blocks)}
  </section>
</body>
</html>
"""


def write_report(
    mission: Mission,
    findings: list[Finding],
    output_dir: Path,
    report_format: ReportFormat,
) -> Report:
    output_dir.mkdir(parents=True, exist_ok=True)

    if report_format == ReportFormat.JSON:
        content = render_json(mission, findings)
        extension = "json"
    elif report_format == ReportFormat.MARKDOWN:
        content = render_markdown(mission, findings)
        extension = "md"
    elif report_format == ReportFormat.HTML:
        content = render_html(mission, findings)
        extension = "html"
    else:
        raise ValueError(f"unsupported report format: {report_format}")

    output_path = output_dir / f"{mission.id}.{extension}"
    output_path.write_text(content, encoding="utf-8")

    return Report(
        mission_id=mission.id,
        format=report_format,
        finding_count=len(findings),
        output_path=str(output_path),
    )
