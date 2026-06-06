"""Report rendering for normalized findings."""

from __future__ import annotations

import json
import textwrap
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

REVIEWED_DISPOSITION_STATUSES = {
    FindingStatus.ACCEPTED_RISK,
    FindingStatus.FALSE_POSITIVE,
}

CRITICAL_ATTENTION_SEVERITIES = {
    Severity.CRITICAL,
    Severity.HIGH,
}

SEVERITY_LABELS_FR = {
    "critical": "Critique",
    "high": "Élevée",
    "medium": "Moyenne",
    "low": "Faible",
    "info": "Information",
}

STATUS_LABELS_FR = {
    "new": "Nouveau",
    "confirmed": "Confirmé",
    "false_positive": "Faux positif",
    "accepted_risk": "Risque accepté",
    "remediated": "Corrigé",
    "counter_test_passed": "Contre-test validé",
    "counter_test_failed": "Contre-test échoué",
    "draft": "Brouillon",
    "blocked": "Bloquée",
    "ready_to_scan": "Prête à auditer",
    "in_progress": "En cours",
    "completed": "Terminée",
}

RISK_LEVEL_LABELS_FR = {
    "none": "Aucun",
    "low": "Faible",
    "medium": "Moyen",
    "high": "Élevé",
    "critical": "Critique",
}

EXECUTIVE_SUMMARY_LABELS_FR = {
    "No active findings are included in this report.": (
        "Aucun constat actif n’est inclus dans ce rapport."
    ),
    "Immediate remediation is required for critical security findings.": (
        "Une remédiation immédiate est requise pour les constats critiques."
    ),
    "High-priority remediation should be planned as soon as possible.": (
        "Les remédiations prioritaires doivent être planifiées dès que possible."
    ),
    "The audit identified moderate security improvements to prioritize.": (
        "L’audit identifie des améliorations de sécurité modérées à prioriser."
    ),
    "The audit identified low-risk hygiene improvements and informational observations.": (
        "L’audit identifie des améliorations d’hygiène à faible risque et des observations informatives."
    ),
}

AUDIT_TYPE_LABELS_FR = {
    "internal": "Interne",
    "external": "Externe",
    "mixed": "Mixte",
}

SCOPE_TYPE_LABELS_FR = {
    "cidr": "Réseau",
    "ip": "Adresse IP",
    "domain": "Domaine",
    "url": "URL",
}

MISSION_REPORT_FORMATS: tuple[ReportFormat, ...] = (
    ReportFormat.JSON,
    ReportFormat.MARKDOWN,
    ReportFormat.HTML,
    ReportFormat.PDF,
)


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


def finding_status_counts(findings: list[Finding]) -> dict[str, int]:
    counts = Counter(finding.status.value for finding in findings)
    return {status.value: counts.get(status.value, 0) for status in FindingStatus}


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


def display_report_value(value: str) -> str:
    return "Non renseigné" if value == "missing" else value


def display_severity(value: str) -> str:
    return SEVERITY_LABELS_FR.get(value, value)


def display_status(value: str) -> str:
    return STATUS_LABELS_FR.get(value, value)


def display_risk_level(value: object) -> str:
    text = str(value)
    return RISK_LEVEL_LABELS_FR.get(text, text)


def display_executive_summary(value: object) -> str:
    text = str(value)
    return EXECUTIVE_SUMMARY_LABELS_FR.get(text, text)


def display_generated_at(value: object) -> str:
    return str(value).replace("T", " ").replace("+00:00", " UTC")


def display_audit_type(value: str) -> str:
    return AUDIT_TYPE_LABELS_FR.get(value, value)


def display_scope_target(target: str) -> str:
    scope_type, separator, value = target.partition(":")
    if not separator:
        return target
    return f"{SCOPE_TYPE_LABELS_FR.get(scope_type, scope_type)} : {value}"


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


def finding_review_note(finding: Finding) -> str:
    return display_value(finding.metadata.get("review_note"))


def disposition_notes(findings: list[Finding]) -> list[dict[str, str]]:
    notes = []
    for finding in sorted_findings(findings):
        note = finding_review_note(finding)
        if finding.status in REVIEWED_DISPOSITION_STATUSES or note != "missing":
            notes.append(
                {
                    "status": finding.status.value,
                    "asset": finding.affected_asset,
                    "title": finding.title,
                    "review_note": note,
                }
            )
    return notes


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


def critical_attention_items(findings: list[Finding], limit: int = 5) -> list[dict[str, str]]:
    prioritized = [
        finding
        for finding in sorted_findings(active_findings(findings))
        if finding.severity in CRITICAL_ATTENTION_SEVERITIES
    ]
    return [
        {
            "severity": finding.severity.value,
            "asset": finding.affected_asset,
            "title": finding.title,
            "status": finding.status.value,
            "risk": finding.risk,
            "remediation": finding.remediation,
            "counter_test": finding.counter_test,
        }
        for finding in prioritized[:limit]
    ]


def build_report_summary(mission: Mission, findings: list[Finding]) -> dict[str, object]:
    active = active_findings(findings)
    score = risk_score(findings)
    attention_count = len(
        [
            finding
            for finding in active
            if finding.severity in CRITICAL_ATTENTION_SEVERITIES
        ]
    )
    return {
        "generated_at": utc_now().isoformat(),
        "finding_count": len(findings),
        "active_finding_count": len(active),
        "critical_attention_count": attention_count,
        "severity_counts": severity_counts(active),
        "status_counts": finding_status_counts(findings),
        "disposition_notes": disposition_notes(findings),
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
        "critical_attention": critical_attention_items(findings),
        "findings": [finding.model_dump(mode="json") for finding in sorted_findings(findings)],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def render_markdown(mission: Mission, findings: list[Finding]) -> str:
    ordered_findings = sorted_findings(findings)
    summary = build_report_summary(mission, ordered_findings)
    counts = summary["severity_counts"]
    status_counts = summary["status_counts"]
    disposition_items = summary["disposition_notes"]
    scope = summary["scope"]
    authorization = summary["authorization"]
    plan = remediation_plan(ordered_findings)
    attention_items = critical_attention_items(ordered_findings)

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
            "## Finding Dispositions",
            "",
            f"- New: {status_counts['new']}",
            f"- Confirmed: {status_counts['confirmed']}",
            f"- False positive: {status_counts['false_positive']}",
            f"- Accepted risk: {status_counts['accepted_risk']}",
            f"- Remediated: {status_counts['remediated']}",
            f"- Counter-test passed: {status_counts['counter_test_passed']}",
            f"- Counter-test failed: {status_counts['counter_test_failed']}",
            "",
        ]
    )

    if disposition_items:
        lines.extend(["Disposition notes:", ""])
        for item in disposition_items:
            lines.append(
                f"- `{item['status']}` {item['title']} on "
                f"`{item['asset']}`: {item['review_note']}"
            )
        lines.append("")
    else:
        lines.extend(["No reviewed disposition notes were included.", ""])

    lines.extend(["## Points critiques à traiter", ""])

    if attention_items:
        for index, item in enumerate(attention_items, start=1):
            lines.extend(
                [
                    (
                        f"{index}. `{item['severity']}` {item['title']} "
                        f"on `{item['asset']}`"
                    ),
                    f"   Risk: {item['risk']}",
                    f"   Remediation: {item['remediation']}",
                    f"   Counter-test: {item['counter_test']}",
                    "",
                ]
            )
    else:
        lines.extend(["No active critical or high findings were included.", ""])

    lines.extend(["## Remediation Plan", ""])

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
        review_note = finding_review_note(finding)
        if review_note != "missing":
            lines.extend(["**Review note**", "", review_note, ""])

    return "\n".join(lines)


def _render_html_remediation_plan(plan: list[dict[str, str]]) -> str:
    if not plan:
        return '<p class="empty">Aucune action prioritaire n’est incluse dans ce rapport.</p>'

    rows = []
    for index, item in enumerate(plan, start=1):
        rows.append(
            f"""
<tr>
  <td class="rank">{index}</td>
  <td><span class="severity-pill severity-{escape(item["severity"])}">{escape(display_severity(item["severity"]))}</span></td>
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
      <th>#</th>
      <th>Gravité</th>
      <th>Actif concerné</th>
      <th>Constat</th>
      <th>Remédiation</th>
      <th>Contre-test</th>
    </tr>
  </thead>
  <tbody>
    {"".join(rows)}
  </tbody>
</table>
""".strip()


def _render_html_critical_attention(items: list[dict[str, str]]) -> str:
    if not items:
        return (
            '<p class="empty">Aucun constat critique ou élevé actif n’est inclus '
            "dans ce rapport.</p>"
        )

    cards = []
    for item in items:
        cards.append(
            f"""
<article class="attention-card severity-{escape(item["severity"])}">
  <div class="attention-meta">
    <span class="severity-pill severity-{escape(item["severity"])}">{escape(display_severity(item["severity"]))}</span>
    <span>{escape(display_status(item["status"]))}</span>
  </div>
  <h3>{escape(item["title"])}</h3>
  <dl>
    <dt>Actif concerné</dt><dd>{escape(item["asset"])}</dd>
  </dl>
  <h4>Risque</h4>
  <p>{escape(item["risk"])}</p>
  <h4>Remédiation prioritaire</h4>
  <p>{escape(item["remediation"])}</p>
  <h4>Contre-test attendu</h4>
  <p>{escape(item["counter_test"])}</p>
</article>
""".strip()
        )

    return f'<div class="attention-grid">{"".join(cards)}</div>'


def _render_html_disposition_summary(
    status_counts: dict[str, int],
    disposition_items: list[dict[str, str]],
) -> str:
    note_rows = []
    for item in disposition_items:
        note_rows.append(
            f"""
<tr>
  <td>{escape(display_status(item["status"]))}</td>
  <td>{escape(item["asset"])}</td>
  <td>{escape(item["title"])}</td>
  <td>{escape(item["review_note"])}</td>
</tr>
""".strip()
        )

    notes_html = (
        f"""
<h3>Notes de revue</h3>
<table>
  <thead>
    <tr>
      <th>Statut</th>
      <th>Actif concerné</th>
      <th>Constat</th>
      <th>Note de revue</th>
    </tr>
  </thead>
  <tbody>
    {"".join(note_rows)}
  </tbody>
</table>
""".strip()
        if note_rows
        else '<p class="empty">Aucune note de revue n’est incluse.</p>'
    )

    return f"""
<div class="summary">
  <div class="metric"><span>Nouveau</span><strong>{status_counts["new"]}</strong></div>
  <div class="metric"><span>Confirmé</span><strong>{status_counts["confirmed"]}</strong></div>
  <div class="metric"><span>Faux positif</span><strong>{status_counts["false_positive"]}</strong></div>
  <div class="metric"><span>Risque accepté</span><strong>{status_counts["accepted_risk"]}</strong></div>
  <div class="metric"><span>Corrigé</span><strong>{status_counts["remediated"]}</strong></div>
  <div class="metric"><span>Contre-test validé</span><strong>{status_counts["counter_test_passed"]}</strong></div>
  <div class="metric"><span>Contre-test échoué</span><strong>{status_counts["counter_test_failed"]}</strong></div>
</div>
{notes_html}
""".strip()


def render_html(mission: Mission, findings: list[Finding]) -> str:
    ordered_findings = sorted_findings(findings)
    summary = build_report_summary(mission, ordered_findings)
    counts = summary["severity_counts"]
    status_counts = summary["status_counts"]
    disposition_items = summary["disposition_notes"]
    scope = summary["scope"]
    authorization = summary["authorization"]
    plan = remediation_plan(ordered_findings)
    attention_items = critical_attention_items(ordered_findings)
    finding_blocks = []
    risk_level = str(summary["risk_level"])
    generated_at = display_generated_at(summary["generated_at"])
    authorization_present = "Oui" if summary["authorization_present"] else "Non"
    retention_days = display_report_value(authorization["evidence_retention_days"])
    retention_label = retention_days if retention_days == "Non renseigné" else f"{retention_days} jours"

    for finding in ordered_findings:
        review_note = finding_review_note(finding)
        review_note_html = (
            f"<dt>Note de revue</dt><dd>{escape(review_note)}</dd>"
            if review_note != "missing"
            else ""
        )
        finding_blocks.append(
            f"""
<article class="finding severity-{escape(finding.severity.value)}">
  <h2>{escape(finding.title)}</h2>
  <dl>
    <dt>Gravité</dt><dd><span class="severity-pill severity-{escape(finding.severity.value)}">{escape(display_severity(finding.severity.value))}</span></dd>
    <dt>Actif concerné</dt><dd>{escape(finding.affected_asset)}</dd>
    <dt>Catégorie</dt><dd>{escape(finding.category)}</dd>
    <dt>Statut</dt><dd>{escape(display_status(finding.status.value))}</dd>
    <dt>Confiance</dt><dd>{finding.confidence:.2f}</dd>
    <dt>Sources</dt><dd>{escape(", ".join(finding.sources))}</dd>
    {review_note_html}
  </dl>
  <h3>Preuve</h3>
  <pre>{escape(finding.proof)}</pre>
  <h3>Risque</h3>
  <p>{escape(finding.risk)}</p>
  <h3>Remédiation</h3>
  <p>{escape(finding.remediation)}</p>
  <h3>Contre-test</h3>
  <p>{escape(finding.counter_test)}</p>
</article>
""".strip()
        )

    if not finding_blocks:
        finding_blocks.append('<p class="empty">Aucun constat n’est inclus dans ce rapport.</p>')

    approved_targets = scope["approved_targets"]
    approved_targets_html = (
        "".join(f"<li><code>{escape(display_scope_target(target))}</code></li>" for target in approved_targets)
        if approved_targets
        else "<li>Aucune cible approuvée n’est enregistrée.</li>"
    )

    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Rapport d’audit sécurité - {escape(mission.name)}</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #172033;
      --muted: #5b667a;
      --line: #d7deea;
      --surface: #f6f8fb;
      --panel: #ffffff;
      --brand: #0b6073;
      --accent: #2457a6;
      --critical: #b42318;
      --high: #d92d20;
      --medium: #b65c00;
      --low: #1570ef;
      --info: #667085;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      font-family: Arial, Helvetica, sans-serif;
      line-height: 1.55;
      margin: 0;
      color: var(--ink);
      background: #eef2f6;
    }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 24px; }}
    header {{
      background: var(--panel);
      border-bottom: 4px solid var(--brand);
      padding: 28px 32px;
    }}
    header .brand {{ color: var(--brand); font-size: .78rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }}
    h1 {{ margin: .3rem 0 .35rem; font-size: 2rem; }}
    h2 {{ margin: 0 0 1rem; font-size: 1.2rem; }}
    h3 {{ margin: 1rem 0 .45rem; font-size: 1rem; }}
    p {{ margin: .35rem 0; }}
    .subtitle {{ color: var(--muted); }}
    .section {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      margin: 18px 0;
      padding: 20px;
    }}
    .executive {{
      border-left: 6px solid var(--brand);
      display: grid;
      grid-template-columns: 1fr 220px;
      gap: 18px;
      align-items: start;
    }}
    .risk-badge {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      background: var(--surface);
    }}
    .risk-badge strong {{ display: block; font-size: 2rem; }}
    .risk-badge span {{ color: var(--muted); }}
    .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(145px, 1fr)); gap: 10px; }}
    .metric {{ border: 1px solid var(--line); border-radius: 8px; padding: 12px; background: var(--surface); }}
    .metric span {{ color: var(--muted); font-size: .82rem; }}
    .metric strong {{ display: block; font-size: 1.45rem; margin-top: 3px; }}
    .context-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }}
    dl {{ display: grid; grid-template-columns: minmax(150px, 220px) 1fr; gap: .35rem .75rem; margin: 0; }}
    dt {{ font-weight: 700; color: #253044; }}
    dd {{ margin: 0; color: #26364f; }}
    ul {{ margin: .4rem 0 0; padding-left: 1.2rem; }}
    .empty {{ color: var(--muted); font-style: italic; }}
    .attention-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; }}
    .attention-card {{ border: 1px solid var(--line); border-radius: 8px; padding: 16px; background: var(--surface); }}
    .attention-card h3 {{ margin-top: .7rem; }}
    .attention-card h4 {{ color: #253044; font-size: .92rem; margin: .9rem 0 .2rem; }}
    .attention-meta {{ display: flex; align-items: center; justify-content: space-between; gap: 10px; color: var(--muted); font-size: .86rem; }}
    .finding {{ border: 1px solid var(--line); border-radius: 8px; padding: 18px; margin: 14px 0; background: var(--panel); }}
    .severity-critical {{ border-left: 6px solid var(--critical); }}
    .severity-high {{ border-left: 6px solid var(--high); }}
    .severity-medium {{ border-left: 6px solid var(--medium); }}
    .severity-low {{ border-left: 6px solid var(--low); }}
    .severity-info {{ border-left: 6px solid var(--info); }}
    .severity-pill {{ border-radius: 999px; color: #ffffff; display: inline-block; font-size: .78rem; font-weight: 700; padding: .18rem .55rem; }}
    .severity-pill.severity-critical {{ background: var(--critical); }}
    .severity-pill.severity-high {{ background: var(--high); }}
    .severity-pill.severity-medium {{ background: var(--medium); }}
    .severity-pill.severity-low {{ background: var(--low); }}
    .severity-pill.severity-info {{ background: var(--info); }}
    pre {{ background: var(--surface); border: 1px solid var(--line); border-radius: 6px; padding: .75rem; overflow-x: auto; white-space: pre-wrap; }}
    table {{ width: 100%; border-collapse: collapse; font-size: .92rem; }}
    th, td {{ border: 1px solid var(--line); padding: .65rem; vertical-align: top; text-align: left; }}
    th {{ background: var(--surface); color: #253044; }}
    .rank {{ font-weight: 700; text-align: center; width: 48px; }}
    code {{ background: #edf2f7; padding: .1rem .3rem; border-radius: 4px; }}
    @media (max-width: 760px) {{
      main {{ padding: 12px; }}
      header {{ padding: 20px; }}
      .executive, .context-grid {{ grid-template-columns: 1fr; }}
      dl {{ grid-template-columns: 1fr; }}
      table {{ display: block; overflow-x: auto; }}
    }}
    @media print {{
      body {{ background: #ffffff; }}
      main {{ max-width: none; padding: 0; }}
      .section {{ break-inside: avoid; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="brand">M.E.D.I.A. Security Audit Platform</div>
    <h1>Rapport d’audit sécurité</h1>
    <p class="subtitle">{escape(mission.name)} · Mission {escape(mission.id)} · Généré le {escape(generated_at)}</p>
  </header>
  <main>
    <section class="section executive">
      <div>
        <h2>Synthèse direction</h2>
        <p>{escape(display_executive_summary(summary["executive_summary"]))}</p>
        <p>Ce rapport présente uniquement les éléments observés dans le périmètre autorisé et les actions de remédiation associées.</p>
      </div>
      <div class="risk-badge">
        <span>Score de risque</span>
        <strong>{summary["risk_score"]}/100</strong>
        <span>Niveau : {escape(display_risk_level(risk_level))}</span>
      </div>
    </section>

    <section class="section">
      <h2>Vue d’ensemble du risque</h2>
      <div class="summary">
        <div class="metric"><span>Constats actifs</span><strong>{summary["active_finding_count"]}</strong></div>
        <div class="metric"><span>Critiques</span><strong>{counts["critical"]}</strong></div>
        <div class="metric"><span>Élevés</span><strong>{counts["high"]}</strong></div>
        <div class="metric"><span>Moyens</span><strong>{counts["medium"]}</strong></div>
        <div class="metric"><span>Faibles</span><strong>{counts["low"]}</strong></div>
        <div class="metric"><span>Information</span><strong>{counts["info"]}</strong></div>
        <div class="metric"><span>Autorisation</span><strong>{authorization_present}</strong></div>
      </div>
    </section>

    <section class="section">
      <h2>Points critiques à traiter</h2>
      {_render_html_critical_attention(attention_items)}
    </section>

    <section class="section">
      <h2>Contexte de mission et périmètre</h2>
      <div class="context-grid">
        <dl>
          <dt>Client</dt><dd>{escape(mission.client_id)}</dd>
          <dt>Type d’audit</dt><dd>{escape(display_audit_type(mission.audit_type.value))}</dd>
          <dt>Statut mission</dt><dd>{escape(display_status(mission.status.value))}</dd>
          <dt>Référence autorisation</dt><dd>{escape(display_report_value(authorization["reference"]))}</dd>
          <dt>Contact autorisation</dt><dd>{escape(display_report_value(authorization["contact"]))}</dd>
          <dt>Date autorisation</dt><dd>{escape(display_report_value(authorization["authorization_date"]))}</dd>
          <dt>Expiration autorisation</dt><dd>{escape(display_report_value(authorization["authorization_expires_at"]))}</dd>
        </dl>
        <dl>
          <dt>Contact urgence</dt><dd>{escape(display_report_value(authorization["emergency_contact"]))}</dd>
          <dt>Destinataires rapport</dt><dd>{escape(display_report_value(authorization["report_recipients"]))}</dd>
          <dt>Conservation preuves</dt><dd>{escape(retention_label)}</dd>
          <dt>Cibles approuvées</dt><dd>{scope["approved_count"]}</dd>
          <dt>Cibles exclues</dt><dd>{scope["excluded_count"]}</dd>
        </dl>
      </div>
      <h3>Périmètre approuvé</h3>
      <ul>{approved_targets_html}</ul>
    </section>

    <section class="section">
      <h2>Plan de remédiation priorisé</h2>
      {_render_html_remediation_plan(plan)}
    </section>

    <section class="section">
      <h2>Statut de traitement des constats</h2>
      {_render_html_disposition_summary(status_counts, disposition_items)}
    </section>

    <section class="section">
      <h2>Détails techniques des constats</h2>
      {"".join(finding_blocks)}
    </section>
  </main>
</body>
</html>
"""


class PdfReport:
    """Small PDF writer for dependency-free, text-focused mission reports."""

    page_width = 595.0
    page_height = 842.0
    margin = 48.0

    def __init__(self) -> None:
        self.pages: list[list[str]] = []
        self.current: list[str] = []
        self.y = 0.0
        self.add_page()

    def add_page(self) -> None:
        self.current = []
        self.pages.append(self.current)
        self.y = self.page_height - self.margin

    def add_rule(self, color: tuple[float, float, float] = (0.04, 0.38, 0.45)) -> None:
        self.ensure_space(10)
        x = self.margin
        width = self.page_width - (self.margin * 2)
        self.current.append(
            f"q {color[0]:.3f} {color[1]:.3f} {color[2]:.3f} rg "
            f"{x:.1f} {self.y:.1f} {width:.1f} 2 re f Q"
        )
        self.y -= 10

    def add_heading(self, text: str, size: int = 16) -> None:
        self.ensure_space(size + 12)
        self.add_text(text, size=size, bold=True, leading=size + 6)

    def add_section_heading(self, text: str) -> None:
        self.ensure_space(28)
        self.y -= 6
        self.add_text(text, size=13, bold=True, color=(0.04, 0.38, 0.45), leading=18)

    def add_text(
        self,
        text: str,
        size: int = 10,
        bold: bool = False,
        indent: float = 0.0,
        leading: float | None = None,
        color: tuple[float, float, float] = (0.09, 0.13, 0.20),
    ) -> None:
        leading = leading or size + 4
        available_width = self.page_width - (self.margin * 2) - indent
        wrap_width = max(24, int(available_width / (size * 0.52)))
        paragraphs = str(text).splitlines() or [""]
        for paragraph in paragraphs:
            lines = textwrap.wrap(
                paragraph.strip(),
                width=wrap_width,
                break_long_words=True,
                replace_whitespace=True,
            ) or [""]
            for line in lines:
                self.ensure_space(leading)
                font = "F2" if bold else "F1"
                escaped = pdf_escape(line)
                x = self.margin + indent
                self.current.append(
                    "q "
                    f"{color[0]:.3f} {color[1]:.3f} {color[2]:.3f} rg "
                    f"BT /{font} {size} Tf {x:.1f} {self.y:.1f} Td ({escaped}) Tj ET Q"
                )
                self.y -= leading

    def ensure_space(self, needed: float) -> None:
        if self.y - needed < self.margin:
            self.add_page()

    def to_bytes(self) -> bytes:
        objects: list[bytes] = []
        page_count = len(self.pages)
        font_regular_id = 3
        font_bold_id = 4
        first_page_id = 5
        first_content_id = first_page_id + page_count
        page_ids = [first_page_id + index for index in range(page_count)]
        content_ids = [first_content_id + index for index in range(page_count)]

        objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
        kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
        objects.append(
            f"<< /Type /Pages /Kids [{kids}] /Count {page_count} >>".encode("ascii")
        )
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")

        for content_id in content_ids:
            objects.append(
                (
                    "<< /Type /Page /Parent 2 0 R "
                    f"/MediaBox [0 0 {self.page_width:.0f} {self.page_height:.0f}] "
                    f"/Resources << /Font << /F1 {font_regular_id} 0 R "
                    f"/F2 {font_bold_id} 0 R >> >> "
                    f"/Contents {content_id} 0 R >>"
                ).encode("ascii")
            )

        for page in self.pages:
            stream = "\n".join(page).encode("cp1252", errors="replace")
            objects.append(
                b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n"
                + stream
                + b"\nendstream"
            )

        return build_pdf(objects)


def build_pdf(objects: list[bytes]) -> bytes:
    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for object_id, body in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{object_id} 0 obj\n".encode("ascii"))
        output.extend(body)
        output.extend(b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            "startxref\n"
            f"{xref_offset}\n"
            "%%EOF\n"
        ).encode("ascii")
    )
    return bytes(output)


def pdf_escape(text: str) -> str:
    normalized = " ".join(str(text).split())
    return normalized.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def render_pdf(mission: Mission, findings: list[Finding]) -> bytes:
    ordered_findings = sorted_findings(findings)
    summary = build_report_summary(mission, ordered_findings)
    counts = summary["severity_counts"]
    status_counts = summary["status_counts"]
    scope = summary["scope"]
    authorization = summary["authorization"]
    plan = remediation_plan(ordered_findings)
    attention_items = critical_attention_items(ordered_findings)
    generated_at = display_generated_at(summary["generated_at"])
    authorization_present = "oui" if summary["authorization_present"] else "non"

    pdf = PdfReport()
    pdf.add_text(
        "M.E.D.I.A. Security Audit Platform",
        size=10,
        bold=True,
        color=(0.04, 0.38, 0.45),
    )
    pdf.add_heading("Rapport d'audit securite", size=20)
    pdf.add_text(f"{mission.name} - Mission {mission.id}", size=11)
    pdf.add_text(f"Genere le {generated_at}", size=9, color=(0.35, 0.40, 0.48))
    pdf.add_rule()

    pdf.add_section_heading("Synthese direction")
    pdf.add_text(display_executive_summary(summary["executive_summary"]), size=11)
    pdf.add_text(
        f"Score de risque: {summary['risk_score']}/100 - "
        f"Niveau: {display_risk_level(summary['risk_level'])}",
        size=12,
        bold=True,
    )

    pdf.add_section_heading("Vue d'ensemble du risque")
    pdf.add_text(
        " | ".join(
            [
                f"Constats actifs: {summary['active_finding_count']}",
                f"Critiques: {counts['critical']}",
                f"Eleves: {counts['high']}",
                f"Moyens: {counts['medium']}",
                f"Faibles: {counts['low']}",
                f"Info: {counts['info']}",
            ]
        )
    )

    pdf.add_section_heading("Points critiques a traiter")
    if attention_items:
        for index, item in enumerate(attention_items, start=1):
            pdf.add_text(
                (
                    f"{index}. [{display_severity(item['severity'])}] "
                    f"{item['title']} - {item['asset']}"
                ),
                bold=True,
            )
            pdf.add_text(f"Risque: {item['risk']}", indent=12)
            pdf.add_text(f"Remediation: {item['remediation']}", indent=12)
            pdf.add_text(f"Contre-test: {item['counter_test']}", indent=12)
    else:
        pdf.add_text("Aucun constat critique ou eleve actif n'est inclus dans ce rapport.")

    pdf.add_section_heading("Contexte de mission")
    context_lines = [
        f"Client: {mission.client_id}",
        f"Type d'audit: {display_audit_type(mission.audit_type.value)}",
        f"Statut: {display_status(mission.status.value)}",
        f"Autorisation presente: {authorization_present}",
        f"Reference autorisation: {display_report_value(authorization['reference'])}",
        f"Contact autorisation: {display_report_value(authorization['contact'])}",
        f"Date autorisation: {display_report_value(authorization['authorization_date'])}",
        (
            "Expiration autorisation: "
            f"{display_report_value(authorization['authorization_expires_at'])}"
        ),
        f"Contact urgence: {display_report_value(authorization['emergency_contact'])}",
        f"Destinataires rapport: {display_report_value(authorization['report_recipients'])}",
    ]
    for line in context_lines:
        pdf.add_text(f"- {line}")

    pdf.add_section_heading("Perimetre approuve")
    approved_targets = scope["approved_targets"]
    if approved_targets:
        for target in approved_targets:
            pdf.add_text(f"- {display_scope_target(str(target))}")
    else:
        pdf.add_text("Aucune cible approuvee n'est enregistree.")

    pdf.add_section_heading("Plan de remediation priorise")
    if plan:
        for index, item in enumerate(plan, start=1):
            pdf.add_text(
                (
                    f"{index}. [{display_severity(item['severity'])}] "
                    f"{item['title']} - {item['asset']}"
                ),
                bold=True,
            )
            pdf.add_text(f"Remediation: {item['remediation']}", indent=12)
            pdf.add_text(f"Contre-test: {item['counter_test']}", indent=12)
    else:
        pdf.add_text("Aucune action prioritaire n'est incluse dans ce rapport.")

    pdf.add_section_heading("Statut de traitement")
    pdf.add_text(
        " | ".join(
            [
                f"Nouveau: {status_counts['new']}",
                f"Confirme: {status_counts['confirmed']}",
                f"Faux positif: {status_counts['false_positive']}",
                f"Risque accepte: {status_counts['accepted_risk']}",
                f"Corrige: {status_counts['remediated']}",
                f"Contre-test OK: {status_counts['counter_test_passed']}",
                f"Contre-test KO: {status_counts['counter_test_failed']}",
            ]
        )
    )

    pdf.add_section_heading("Details techniques des constats")
    if not ordered_findings:
        pdf.add_text("Aucun constat n'est inclus dans ce rapport.")
    for finding in ordered_findings:
        pdf.add_text(
            f"{finding.title} - {display_severity(finding.severity.value)}",
            size=12,
            bold=True,
            color=(0.04, 0.38, 0.45),
        )
        pdf.add_text(f"Actif: {finding.affected_asset}")
        pdf.add_text(f"Statut: {display_status(finding.status.value)}")
        pdf.add_text(f"Preuve: {finding.proof}")
        pdf.add_text(f"Risque: {finding.risk}")
        pdf.add_text(f"Remediation: {finding.remediation}")
        pdf.add_text(f"Contre-test: {finding.counter_test}")
        review_note = finding_review_note(finding)
        if review_note != "missing":
            pdf.add_text(f"Note de revue: {review_note}")
        pdf.add_text("")

    return pdf.to_bytes()


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
    elif report_format == ReportFormat.PDF:
        content = render_pdf(mission, findings)
        extension = "pdf"
    else:
        raise ValueError(f"unsupported report format: {report_format}")

    output_path = output_dir / f"{mission.id}.{extension}"
    if isinstance(content, bytes):
        output_path.write_bytes(content)
    else:
        output_path.write_text(content, encoding="utf-8")

    return Report(
        mission_id=mission.id,
        format=report_format,
        finding_count=len(findings),
        output_path=str(output_path),
    )
