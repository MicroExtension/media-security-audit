"""Activity log views and exports for the local web interface."""

from __future__ import annotations

import json
from csv import DictWriter
from dataclasses import dataclass
from datetime import date
from enum import Enum
from html import escape
from io import StringIO
from urllib.parse import urlencode

from media_security_audit.models import Client, Mission, utc_now
from media_security_audit.storage import JsonStore
from media_security_audit.web_ui import format_datetime


class ActivityExportFormat(str, Enum):
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"
    CSV = "csv"


@dataclass(frozen=True)
class ActivityExportLink:
    format: str
    label: str
    url: str


@dataclass(frozen=True)
class ActivityFilterOption:
    value: str
    label: str


@dataclass(frozen=True)
class ActivityLogRow:
    id: str
    client_id: str
    mission_id: str
    mission_name: str
    client_name: str
    action: str
    summary: str
    created_at: str
    created_at_iso: str
    created_date: str
    metadata: dict[str, str]
    metadata_summary: str


@dataclass(frozen=True)
class ActivityLogView:
    rows: list[ActivityLogRow]
    visible_events: int
    total_events: int
    mission_count: int
    client_count: int
    actions: list[str]
    clients: list[ActivityFilterOption]
    missions: list[ActivityFilterOption]
    action_filter: str
    client_filter: str
    mission_filter: str
    date_from_filter: str
    date_to_filter: str
    query: str
    export_links: list[ActivityExportLink]


@dataclass(frozen=True)
class ActivityLogExport:
    filename: str
    media_type: str
    content: str


def build_activity_log_view(
    store: JsonStore,
    query: str | None = None,
    action: str | None = None,
    client_id: str | None = None,
    mission_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int | None = 200,
) -> ActivityLogView:
    clients = store.list_clients()
    missions = store.list_missions()
    client_names = {client.id: client.name for client in clients}
    query_text = (query or "").strip()
    action_filter = (action or "").strip()
    client_filter = (client_id or "").strip()
    mission_filter = (mission_id or "").strip()
    date_from_filter = (date_from or "").strip()
    date_to_filter = (date_to or "").strip()
    rows: list[ActivityLogRow] = []

    for mission in missions:
        for event in store.list_activity_events(mission.id):
            rows.append(
                ActivityLogRow(
                    id=event.id,
                    client_id=mission.client_id,
                    mission_id=mission.id,
                    mission_name=mission.name,
                    client_name=client_names.get(mission.client_id, mission.client_id),
                    action=event.action,
                    summary=event.summary,
                    created_at=format_datetime(event.created_at),
                    created_at_iso=event.created_at.isoformat(),
                    created_date=event.created_at.date().isoformat(),
                    metadata={str(key): str(value) for key, value in event.metadata.items()},
                    metadata_summary=metadata_summary(event.metadata),
                )
            )

    rows.sort(key=lambda row: (row.created_at_iso, row.id), reverse=True)
    actions = sorted({row.action for row in rows})
    filtered_rows = filter_activity_rows(
        rows,
        query=query_text,
        action=action_filter,
        client_id=client_filter,
        mission_id=mission_filter,
        date_from=date_from_filter,
        date_to=date_to_filter,
    )
    visible_rows = filtered_rows if limit is None else filtered_rows[:limit]
    return ActivityLogView(
        rows=visible_rows,
        visible_events=len(filtered_rows),
        total_events=len(rows),
        mission_count=len(missions),
        client_count=len(clients),
        actions=actions,
        clients=client_filter_options(clients),
        missions=mission_filter_options(missions, client_names),
        action_filter=action_filter,
        client_filter=client_filter,
        mission_filter=mission_filter,
        date_from_filter=date_from_filter,
        date_to_filter=date_to_filter,
        query=query_text,
        export_links=activity_export_links(
            query=query_text,
            action=action_filter,
            client_id=client_filter,
            mission_id=mission_filter,
            date_from=date_from_filter,
            date_to=date_to_filter,
        ),
    )


def filter_activity_rows(
    rows: list[ActivityLogRow],
    query: str = "",
    action: str = "",
    client_id: str = "",
    mission_id: str = "",
    date_from: str = "",
    date_to: str = "",
) -> list[ActivityLogRow]:
    query_text = query.casefold()
    lower_date = parse_date_filter(date_from)
    upper_date = parse_date_filter(date_to)
    filtered_rows = rows
    if client_id:
        filtered_rows = [row for row in filtered_rows if row.client_id == client_id]
    if mission_id:
        filtered_rows = [row for row in filtered_rows if row.mission_id == mission_id]
    if action:
        filtered_rows = [row for row in filtered_rows if row.action == action]
    if lower_date:
        filtered_rows = [
            row for row in filtered_rows if date.fromisoformat(row.created_date) >= lower_date
        ]
    if upper_date:
        filtered_rows = [
            row for row in filtered_rows if date.fromisoformat(row.created_date) <= upper_date
        ]
    if query_text:
        filtered_rows = [
            row
            for row in filtered_rows
            if query_text in activity_search_text(row).casefold()
        ]
    return filtered_rows


def activity_search_text(row: ActivityLogRow) -> str:
    return " ".join(
        [
            row.id,
            row.client_id,
            row.mission_id,
            row.mission_name,
            row.client_name,
            row.action,
            row.summary,
            row.metadata_summary,
        ]
    )


def parse_date_filter(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def client_filter_options(clients: list[Client]) -> list[ActivityFilterOption]:
    return sorted(
        [ActivityFilterOption(value=client.id, label=client.name) for client in clients],
        key=lambda option: option.label.casefold(),
    )


def mission_filter_options(
    missions: list[Mission],
    client_names: dict[str, str],
) -> list[ActivityFilterOption]:
    return sorted(
        [
            ActivityFilterOption(
                value=mission.id,
                label=f"{client_names.get(mission.client_id, mission.client_id)} / {mission.name}",
            )
            for mission in missions
        ],
        key=lambda option: option.label.casefold(),
    )


def activity_export_links(
    query: str = "",
    action: str = "",
    client_id: str = "",
    mission_id: str = "",
    date_from: str = "",
    date_to: str = "",
) -> list[ActivityExportLink]:
    return [
        ActivityExportLink(
            format=report_format.value,
            label=export_label(report_format),
            url=activity_export_url(
                report_format,
                query=query,
                action=action,
                client_id=client_id,
                mission_id=mission_id,
                date_from=date_from,
                date_to=date_to,
            ),
        )
        for report_format in (
            ActivityExportFormat.JSON,
            ActivityExportFormat.MARKDOWN,
            ActivityExportFormat.HTML,
            ActivityExportFormat.CSV,
        )
    ]


def activity_export_url(
    report_format: ActivityExportFormat,
    query: str = "",
    action: str = "",
    client_id: str = "",
    mission_id: str = "",
    date_from: str = "",
    date_to: str = "",
) -> str:
    params = {
        key: value
        for key, value in {
            "q": query,
            "action": action,
            "client_id": client_id,
            "mission_id": mission_id,
            "date_from": date_from,
            "date_to": date_to,
        }.items()
        if value
    }
    query_string = urlencode(params)
    suffix = f"?{query_string}" if query_string else ""
    return f"/activity/export/{report_format.value}{suffix}"


def build_activity_log_export(
    store: JsonStore,
    export_format: ActivityExportFormat,
    query: str | None = None,
    action: str | None = None,
    client_id: str | None = None,
    mission_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> ActivityLogExport:
    view = build_activity_log_view(
        store,
        query=query,
        action=action,
        client_id=client_id,
        mission_id=mission_id,
        date_from=date_from,
        date_to=date_to,
        limit=None,
    )
    filename = activity_export_filename(export_format, view)
    if export_format is ActivityExportFormat.JSON:
        return ActivityLogExport(
            filename=filename,
            media_type="application/json",
            content=render_activity_log_json(view),
        )
    if export_format is ActivityExportFormat.HTML:
        return ActivityLogExport(
            filename=filename,
            media_type="text/html; charset=utf-8",
            content=render_activity_log_html(view),
        )
    if export_format is ActivityExportFormat.CSV:
        return ActivityLogExport(
            filename=filename,
            media_type="text/csv; charset=utf-8",
            content=render_activity_log_csv(view),
        )
    return ActivityLogExport(
        filename=filename,
        media_type="text/markdown; charset=utf-8",
        content=render_activity_log_markdown(view),
    )


def activity_export_filename(export_format: ActivityExportFormat, view: ActivityLogView) -> str:
    extension = {
        ActivityExportFormat.JSON: "json",
        ActivityExportFormat.MARKDOWN: "md",
        ActivityExportFormat.HTML: "html",
        ActivityExportFormat.CSV: "csv",
    }[export_format]
    parts = ["activity-log"]
    if view.client_filter:
        parts.append("client")
    if view.mission_filter:
        parts.append("mission")
    if view.date_from_filter or view.date_to_filter:
        parts.append("dates")
    if view.action_filter:
        parts.append(slugify(view.action_filter))
    if (
        view.query
        or view.client_filter
        or view.mission_filter
        or view.date_from_filter
        or view.date_to_filter
    ):
        parts.append("filtered")
    return "-".join(parts) + f".{extension}"


def slugify(value: str) -> str:
    slug = "".join(character if character.isalnum() else "-" for character in value.lower())
    slug = "-".join(part for part in slug.split("-") if part)
    return slug or "filtered"


def export_label(report_format: ActivityExportFormat) -> str:
    if report_format is ActivityExportFormat.JSON:
        return "JSON"
    if report_format is ActivityExportFormat.HTML:
        return "HTML"
    if report_format is ActivityExportFormat.CSV:
        return "CSV"
    return "Markdown"


def metadata_summary(metadata: dict[str, object]) -> str:
    if not metadata:
        return "-"
    return ", ".join(f"{key}={value}" for key, value in sorted(metadata.items()))


def render_activity_log_json(view: ActivityLogView) -> str:
    payload = {
        "generated_at": utc_now().isoformat(),
        "count": view.visible_events,
        "total_events": view.total_events,
        "missions": view.mission_count,
        "clients": view.client_count,
        "query": view.query,
        "action": view.action_filter or None,
        "client_id": view.client_filter or None,
        "mission_id": view.mission_filter or None,
        "date_from": view.date_from_filter or None,
        "date_to": view.date_to_filter or None,
        "events": [
            {
                "id": row.id,
                "client_id": row.client_id,
                "mission_id": row.mission_id,
                "mission_name": row.mission_name,
                "client_name": row.client_name,
                "action": row.action,
                "summary": row.summary,
                "created_at": row.created_at_iso,
                "created_date": row.created_date,
                "metadata": row.metadata,
            }
            for row in view.rows
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def render_activity_log_csv(view: ActivityLogView) -> str:
    output = StringIO()
    writer = DictWriter(
        output,
        fieldnames=[
            "id",
            "client_id",
            "client_name",
            "mission_id",
            "mission_name",
            "action",
            "summary",
            "created_at",
            "created_date",
            "metadata",
        ],
    )
    writer.writeheader()
    for row in view.rows:
        writer.writerow(
            {
                "id": row.id,
                "client_id": row.client_id,
                "client_name": row.client_name,
                "mission_id": row.mission_id,
                "mission_name": row.mission_name,
                "action": row.action,
                "summary": row.summary,
                "created_at": row.created_at_iso,
                "created_date": row.created_date,
                "metadata": row.metadata_summary,
            }
        )
    return output.getvalue()


def render_activity_log_markdown(view: ActivityLogView) -> str:
    lines = [
        "# Activity Log",
        "",
        f"Visible events: {view.visible_events}",
        f"Total events: {view.total_events}",
        f"Missions: {view.mission_count}",
        f"Clients: {view.client_count}",
        f"Action filter: {view.action_filter or 'all'}",
        f"Client filter: {view.client_filter or 'all'}",
        f"Mission filter: {view.mission_filter or 'all'}",
        f"Date from: {view.date_from_filter or 'none'}",
        f"Date to: {view.date_to_filter or 'none'}",
        f"Search filter: {view.query or 'none'}",
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
  <p>Visible events: {view.visible_events} | Total events: {view.total_events} | Missions: {view.mission_count} | Clients: {view.client_count}</p>
  <p>Action filter: {escape(view.action_filter or "all")} | Client filter: {escape(view.client_filter or "all")} | Mission filter: {escape(view.mission_filter or "all")} | Date from: {escape(view.date_from_filter or "none")} | Date to: {escape(view.date_to_filter or "none")} | Search filter: {escape(view.query or "none")}</p>
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
