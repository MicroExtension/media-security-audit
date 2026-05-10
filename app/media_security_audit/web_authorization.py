"""Authorization brief exports for pre-audit review."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from html import escape
from pathlib import Path

from media_security_audit.models import Mission, ScopeItem, utc_now
from media_security_audit.reports import authorization_summary, scope_summary
from media_security_audit.storage import JsonStore
from media_security_audit.web_reports import mission_report_dir


class AuthorizationBriefFormat(str, Enum):
    MARKDOWN = "markdown"
    HTML = "html"


BRIEF_EXTENSIONS: dict[AuthorizationBriefFormat, str] = {
    AuthorizationBriefFormat.MARKDOWN: "md",
    AuthorizationBriefFormat.HTML: "html",
}


@dataclass(frozen=True)
class AuthorizationBriefLink:
    format: str
    filename: str
    size_bytes: int


def authorization_brief_path(
    reports_dir: Path,
    mission_id: str,
    brief_format: AuthorizationBriefFormat,
) -> Path:
    extension = BRIEF_EXTENSIONS[brief_format]
    return mission_report_dir(reports_dir, mission_id) / f"{mission_id}-authorization-brief.{extension}"


def approved_scope_items(mission: Mission) -> list[ScopeItem]:
    return [item for item in mission.scope if item.approved and not item.excluded]


def excluded_scope_items(mission: Mission) -> list[ScopeItem]:
    return [item for item in mission.scope if item.excluded]


def draft_scope_items(mission: Mission) -> list[ScopeItem]:
    return [item for item in mission.scope if not item.approved and not item.excluded]


def authorization_missing_items(mission: Mission) -> list[str]:
    missing = []
    if not mission.authorization_reference:
        missing.append("authorization reference")
    if not mission.authorization_contact:
        missing.append("authorization contact")
    if mission.authorization_date is None:
        missing.append("authorization date")
    if mission.authorization_expires_at is None:
        missing.append("authorization expiration date")
    if not mission.emergency_contact:
        missing.append("emergency contact")
    if not mission.report_recipients:
        missing.append("report recipients")
    if mission.evidence_retention_days is None:
        missing.append("evidence retention duration")
    if not approved_scope_items(mission):
        missing.append("approved scope")
    return missing


def authorization_blockers(mission: Mission) -> list[str]:
    blockers = []
    if not mission.authorization_reference:
        blockers.append("authorization reference")
    if not approved_scope_items(mission):
        blockers.append("approved scope")
    return blockers


def authorization_decision(mission: Mission) -> str:
    return "ready_for_guarded_cli_execution" if not authorization_blockers(mission) else "not_ready"


def scope_line(item: ScopeItem) -> str:
    notes = f" - {item.notes}" if item.notes else ""
    return f"{item.type.value}:{item.value} ({item.environment.value}){notes}"


def render_scope_list(items: list[ScopeItem]) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- `{scope_line(item)}`" for item in items]


def render_authorization_brief_markdown(
    mission: Mission,
    client_name: str | None = None,
) -> str:
    authorization = authorization_summary(mission)
    scope = scope_summary(mission)
    blockers = authorization_blockers(mission)
    missing = authorization_missing_items(mission)
    decision = authorization_decision(mission)
    generated_at = utc_now().isoformat()
    checks = ", ".join(check.value for check in mission.selected_checks) or "none"

    lines = [
        f"# Authorization Brief - {mission.name}",
        "",
        "## Decision",
        "",
        f"- Status: `{decision}`",
        f"- Blocking items: `{', '.join(blockers) if blockers else 'none'}`",
        f"- Recommended missing items: `{', '.join(missing) if missing else 'none'}`",
        "",
        "## Mission",
        "",
        f"- Mission id: `{mission.id}`",
        f"- Client: `{client_name or mission.client_id}`",
        f"- Client id: `{mission.client_id}`",
        f"- Audit type: `{mission.audit_type.value}`",
        f"- Mission status: `{mission.status.value}`",
        f"- Selected checks: `{checks}`",
        f"- Generated at: `{generated_at}`",
        "",
        "## Authorization",
        "",
        f"- Reference: `{authorization['reference']}`",
        f"- Contact: `{authorization['contact']}`",
        f"- Date: `{authorization['authorization_date']}`",
        f"- Expires: `{authorization['authorization_expires_at']}`",
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
        "### Approved Scope",
        "",
    ]
    lines.extend(render_scope_list(approved_scope_items(mission)))
    lines.extend(["", "### Excluded Scope", ""])
    lines.extend(render_scope_list(excluded_scope_items(mission)))
    lines.extend(["", "### Draft Scope", ""])
    lines.extend(render_scope_list(draft_scope_items(mission)))
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- No scan is executed by this brief.",
            "- Browser workflow remains planning and review only.",
            "- Guarded CLI execution still requires explicit `--execute`.",
            "- Authorization reference and approved scope remain mandatory before scanner execution.",
            "",
        ]
    )
    return "\n".join(lines)


def html_list(items: list[str]) -> str:
    return "".join(f"<li>{escape(item)}</li>" for item in items) if items else "<li>none</li>"


def scope_html(items: list[ScopeItem]) -> str:
    if not items:
        return "<li>none</li>"
    return "".join(f"<li><code>{escape(scope_line(item))}</code></li>" for item in items)


def render_authorization_brief_html(
    mission: Mission,
    client_name: str | None = None,
) -> str:
    authorization = authorization_summary(mission)
    scope = scope_summary(mission)
    blockers = authorization_blockers(mission)
    missing = authorization_missing_items(mission)
    decision = authorization_decision(mission)
    generated_at = utc_now().isoformat()
    checks = ", ".join(check.value for check in mission.selected_checks) or "none"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Authorization Brief - {escape(mission.name)}</title>
  <style>
    body {{ font-family: Arial, sans-serif; line-height: 1.5; margin: 2rem; color: #1f2933; }}
    header {{ border-bottom: 1px solid #d9e2ec; margin-bottom: 1.5rem; }}
    section {{ margin: 1.5rem 0; }}
    .decision {{ border-left: 6px solid #1570ef; background: #f8fafc; padding: 1rem; }}
    dl {{ display: grid; grid-template-columns: 190px 1fr; gap: .3rem .75rem; }}
    dt {{ font-weight: bold; }}
    code {{ background: #eef2f6; padding: .1rem .25rem; border-radius: 4px; }}
  </style>
</head>
<body>
  <header>
    <h1>Authorization Brief</h1>
    <p>{escape(mission.name)} | Mission {escape(mission.id)}</p>
  </header>
  <section class="decision">
    <h2>Decision</h2>
    <dl>
      <dt>Status</dt><dd>{escape(decision)}</dd>
      <dt>Blocking items</dt><dd><ul>{html_list(blockers)}</ul></dd>
      <dt>Recommended missing items</dt><dd><ul>{html_list(missing)}</ul></dd>
    </dl>
  </section>
  <section>
    <h2>Mission</h2>
    <dl>
      <dt>Client</dt><dd>{escape(client_name or mission.client_id)}</dd>
      <dt>Client ID</dt><dd>{escape(mission.client_id)}</dd>
      <dt>Audit type</dt><dd>{escape(mission.audit_type.value)}</dd>
      <dt>Mission status</dt><dd>{escape(mission.status.value)}</dd>
      <dt>Selected checks</dt><dd>{escape(checks)}</dd>
      <dt>Generated at</dt><dd>{escape(generated_at)}</dd>
    </dl>
  </section>
  <section>
    <h2>Authorization</h2>
    <dl>
      <dt>Reference</dt><dd>{escape(authorization["reference"])}</dd>
      <dt>Contact</dt><dd>{escape(authorization["contact"])}</dd>
      <dt>Date</dt><dd>{escape(authorization["authorization_date"])}</dd>
      <dt>Expires</dt><dd>{escape(authorization["authorization_expires_at"])}</dd>
      <dt>Emergency contact</dt><dd>{escape(authorization["emergency_contact"])}</dd>
      <dt>Report recipients</dt><dd>{escape(authorization["report_recipients"])}</dd>
      <dt>Evidence retention days</dt><dd>{escape(authorization["evidence_retention_days"])}</dd>
    </dl>
  </section>
  <section>
    <h2>Scope Summary</h2>
    <dl>
      <dt>Approved targets</dt><dd>{scope["approved_count"]}</dd>
      <dt>Excluded targets</dt><dd>{scope["excluded_count"]}</dd>
      <dt>Draft targets</dt><dd>{scope["draft_count"]}</dd>
    </dl>
    <h3>Approved Scope</h3>
    <ul>{scope_html(approved_scope_items(mission))}</ul>
    <h3>Excluded Scope</h3>
    <ul>{scope_html(excluded_scope_items(mission))}</ul>
    <h3>Draft Scope</h3>
    <ul>{scope_html(draft_scope_items(mission))}</ul>
  </section>
  <section>
    <h2>Guardrails</h2>
    <ul>
      <li>No scan is executed by this brief.</li>
      <li>Browser workflow remains planning and review only.</li>
      <li>Guarded CLI execution still requires explicit <code>--execute</code>.</li>
      <li>Authorization reference and approved scope remain mandatory before scanner execution.</li>
    </ul>
  </section>
</body>
</html>
"""


def generate_authorization_brief(store: JsonStore, mission_id: str, reports_dir: Path) -> list[Path]:
    mission = store.get_mission(mission_id)
    try:
        client_name = store.get_client(mission.client_id).name
    except FileNotFoundError:
        client_name = None

    output_dir = mission_report_dir(reports_dir, mission_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = [
        authorization_brief_path(reports_dir, mission_id, AuthorizationBriefFormat.MARKDOWN),
        authorization_brief_path(reports_dir, mission_id, AuthorizationBriefFormat.HTML),
    ]
    paths[0].write_text(
        render_authorization_brief_markdown(mission, client_name=client_name),
        encoding="utf-8",
    )
    paths[1].write_text(
        render_authorization_brief_html(mission, client_name=client_name),
        encoding="utf-8",
    )
    return paths


def list_authorization_briefs(mission_id: str, reports_dir: Path) -> list[AuthorizationBriefLink]:
    links = []
    for brief_format in AuthorizationBriefFormat:
        path = authorization_brief_path(reports_dir, mission_id, brief_format)
        if path.exists() and path.is_file():
            links.append(
                AuthorizationBriefLink(
                    format=brief_format.value,
                    filename=path.name,
                    size_bytes=path.stat().st_size,
                )
            )
    return links


def authorization_brief_file(
    reports_dir: Path,
    mission_id: str,
    brief_format: AuthorizationBriefFormat,
) -> Path:
    path = authorization_brief_path(reports_dir, mission_id, brief_format)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"authorization brief not found: {brief_format.value}")
    return path
