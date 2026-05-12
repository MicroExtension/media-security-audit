"""Activity log views and exports for the local web interface."""

from __future__ import annotations

import json
from dataclasses import dataclass
from html import escape

from media_security_audit.models import ReportFormat, utc_now
from media_security_audit.storage import JsonStore
from media_security_audit.web_ui import format_datetime


@dataclass(frozen=True)
class ActivityExportLink:
    format: str
    label: str
    url: str


@dataclass(frozen=True)
class ActivityLogRow:
    id: str
    mission_id: str
    mission_name: str
    client_name: str
    action: str
    summary: str
    created_at: str
    created_at_iso: str
    metadata: dict[str, str]
    metadata_summary: str


@dataclass(frozen=True)
class ActivityLogView:
    rows: list[ActivityLogRow]
    total_events: int
    mission_count: int
    client_count: int
    export_links: list[ActivityExportLink]


@dataclass(frozen=True)
class ActivityLogExport:
    filename: str
    media_type: str
    content: str


def build_activity_log_view(store: JsonStore, limit: int | None = 200) -> ActivityLogView:
    clients = store.list_clients()
    missions = store.list_missions()
    client_names = {client.id: client.name for client in clients}
    rows: list[ActivityLogRow] = []

    for mission in missions:
        for event in store.list_activity_events(mission.id):
            rows.append(
                ActivityLogRow(
                    id=event.id,
                    mission_id=mission.id,
                    mission_name=mission.name,
                    client_name=client_names.get(mission.client_id, mission.client_id),
                    action=event.action,
                    summary=event.summary,
                    created_at=format_datetime(event.created_at),
                    created_at_iso=event.created_at.isoformat(),
                    metadata={str(key): str(value) for key, value in event.metadata.items()},
                    metadata_summary=metadata_summary(event.metadata),
                )
            )

    rows.sort(key=lambda row: row.created_at_iso, reverse=True)
    visible_rows = rows if limit is None else rows[:limit]
    return ActivityLogView(
        rows=visible_rows,
        total_events=len(rows),
        mission_count=len(missions),
        client_count=len(clients),
        export_links=activity_export_links(),
    )


def activity_export_links() -> list[ActivityExportLink]:
    return [
        ActivityExportLink(
            format=report_format.value,
            label=export_label(report_format),
            url=f"/activity/export/{report_format.value}",
        )
        for report_format in (ReportFormat.JSON, ReportFormat.MARKDOWN, ReportFormat.HTML)
    ]


def build_activity_log_export(store: JsonStore, export_format: ReportFormat) -> ActivityLogExport:
    view = build_activity_log_view(store, limit=None)
    filename = activity_export_filename(export_format)
    if export_format is ReportFormat.JSON:
        return ActivityLogExport(
            filename=filename,
            media_type="application/json",
            content=render_activity_log_json(view),
        )
    if export_format is ReportFormat.HTML:
        return ActivityLogExport(
            filename=filename,
            media_type="text/html; charset=utf-8",
            content=render_activity_log_html(view),
        )
    return ActivityLogExport(
        filename=filename,
        media_type="text/markdown; charset=utf-8",
        content=render_activity_log_markdown(view),
    )


def activity_export_filename(export_format: ReportFormat) -> str:
    extension = {
        ReportFormat.JSON: "json",
        ReportFormat.MARKDOWN: "md",
        ReportFormat.HTML: "html",
    }[export_format]
    return f"activity-log.{extension}"


def export_label(report_format: ReportFormat) -> str:
    if report_format is ReportFormat.JSON:
        return "JSON"
    if report_format is ReportFormat.HTML:
        return "HTML"
    return "Markdown"


def metadata_summary(metadata: dict[str, object]) -> str:
    if not metadata:
        return "-"
    return ", ".join(f"{key}={value}" for key, value in sorted(metadata.items()))


def render_activity_log_json(view: ActivityLogView) -> str:
    payload = {
        "generated_at": utc_now().isoformat(),
        "count": view.total_events,
        "missions": view.mission_count,
        "clients": view.client_count,
        "events": [
            {
                "id": row.id,
                "mission_id": row.mission_id,
                "mission_name": row.mission_name,
                "client_name": row.client_name,
                "action": row.action,
                "summary": row.summary,
                "created_at": row.created_at_iso,
                "metadata": row.metadata,
            }
            for row in view.rows
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def render_activity_log_markdown(view: ActivityLogView) -> str:
    lines = [
        "# Activity Log",
        "",
        f"Events: {view.total_events}",
        f"Missions: {view.mission_count}",
        f"Clients: {view.client_count}",
        "",
    ]
    for row in view.rows:
        lines.extend(
            [
                f"## {row.created_at} - {row.action}",
                "",
                f"- Client: {row.client_name}",
                f"- Mission: {row.mission_name}",
                f"- Summary: {row.summary}",
                f"- Metadata: {row.metadata_summary}",
                "",
            ]
        )
    if not view.rows:
        lines.extend(["No activity event recorded.", ""])
    return "\n".join(lines)


def render_activity_log_html(view: ActivityLogView) -> str:
    rows = "\n".join(render_activity_row_html(row) for row in view.rows)
    if not rows:
        rows = '<tr><td colspan="6">No activity event recorded.</td></tr>'
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Activity Log</title>
  <style>
    body {{ font-family: Arial, sans-serif; color: #1c2430; margin: 32px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border-bottom: 1px solid #d7dee8; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f3f6f9; color: #344054; font-size: 12px; text-transform: uppercase; }}
  </style>
</head>
<body>
  <h1>Activity Log</h1>
  <p>Events: {view.total_events} | Missions: {view.mission_count} | Clients: {view.client_count}</p>
  <table>
    <thead>
      <tr>
        <th>Created</th>
        <th>Client</th>
        <th>Mission</th>
        <th>Action</th>
        <th>Summary</th>
        <th>Metadata</th>
      </tr>
    </thead>
    <tbody>
      {rows}
    </tbody>
  </table>
</body>
</html>
"""


def render_activity_row_html(row: ActivityLogRow) -> str:
    return f"""<tr>
  <td>{escape(row.created_at)}</td>
  <td>{escape(row.client_name)}</td>
  <td>{escape(row.mission_name)}</td>
  <td>{escape(row.action)}</td>
  <td>{escape(row.summary)}</td>
  <td>{escape(row.metadata_summary)}</td>
</tr>"""
