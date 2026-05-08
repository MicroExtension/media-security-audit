"""Report rendering for normalized findings."""

from __future__ import annotations

import json
from collections import Counter
from html import escape
from pathlib import Path

from media_security_audit.models import Finding, Mission, Report, ReportFormat, SEVERITY_RANK, utc_now


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


def render_json(mission: Mission, findings: list[Finding]) -> str:
    payload = {
        "mission": mission.model_dump(mode="json"),
        "summary": {
            "generated_at": utc_now().isoformat(),
            "finding_count": len(findings),
            "severity_counts": severity_counts(findings),
        },
        "findings": [finding.model_dump(mode="json") for finding in sorted_findings(findings)],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def render_markdown(mission: Mission, findings: list[Finding]) -> str:
    ordered_findings = sorted_findings(findings)
    counts = severity_counts(ordered_findings)
    lines = [
        f"# Security Audit Report - {mission.name}",
        "",
        "## Summary",
        "",
        f"- Mission id: `{mission.id}`",
        f"- Client id: `{mission.client_id}`",
        f"- Findings: {len(ordered_findings)}",
        f"- Critical: {counts['critical']}",
        f"- High: {counts['high']}",
        f"- Medium: {counts['medium']}",
        f"- Low: {counts['low']}",
        f"- Info: {counts['info']}",
        "",
        "## Findings",
        "",
    ]

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


def render_html(mission: Mission, findings: list[Finding]) -> str:
    ordered_findings = sorted_findings(findings)
    counts = severity_counts(ordered_findings)
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

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Security Audit Report - {escape(mission.name)}</title>
  <style>
    body {{ font-family: Arial, sans-serif; line-height: 1.5; margin: 2rem; color: #1f2933; }}
    header {{ border-bottom: 1px solid #d9e2ec; margin-bottom: 1.5rem; }}
    .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: .75rem; }}
    .metric {{ border: 1px solid #d9e2ec; border-radius: 6px; padding: .75rem; }}
    .metric strong {{ display: block; font-size: 1.5rem; }}
    .finding {{ border: 1px solid #d9e2ec; border-radius: 6px; padding: 1rem; margin: 1rem 0; }}
    .severity-critical {{ border-left: 6px solid #b42318; }}
    .severity-high {{ border-left: 6px solid #d92d20; }}
    .severity-medium {{ border-left: 6px solid #dc6803; }}
    .severity-low {{ border-left: 6px solid #1570ef; }}
    .severity-info {{ border-left: 6px solid #667085; }}
    dl {{ display: grid; grid-template-columns: 140px 1fr; gap: .25rem .75rem; }}
    dt {{ font-weight: bold; }}
    pre {{ background: #f8fafc; border: 1px solid #d9e2ec; padding: .75rem; overflow-x: auto; }}
  </style>
</head>
<body>
  <header>
    <h1>Security Audit Report</h1>
    <p>{escape(mission.name)} | Mission {escape(mission.id)}</p>
  </header>
  <section>
    <h2>Summary</h2>
    <div class="summary">
      <div class="metric"><span>Findings</span><strong>{len(ordered_findings)}</strong></div>
      <div class="metric"><span>Critical</span><strong>{counts["critical"]}</strong></div>
      <div class="metric"><span>High</span><strong>{counts["high"]}</strong></div>
      <div class="metric"><span>Medium</span><strong>{counts["medium"]}</strong></div>
      <div class="metric"><span>Low</span><strong>{counts["low"]}</strong></div>
      <div class="metric"><span>Info</span><strong>{counts["info"]}</strong></div>
    </div>
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

