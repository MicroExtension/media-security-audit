"""View helpers for the remediation library page."""

from __future__ import annotations

import json
from dataclasses import dataclass
from html import escape
from urllib.parse import urlencode

from media_security_audit.models import ReportFormat
from media_security_audit.remediation_library import (
    RemediationEntry,
    filter_remediations,
    remediation_categories,
)


REMEDIATION_EXPORT_FORMATS: tuple[ReportFormat, ...] = (
    ReportFormat.JSON,
    ReportFormat.MARKDOWN,
    ReportFormat.HTML,
)


@dataclass(frozen=True)
class RemediationExportLink:
    format: str
    label: str
    url: str


@dataclass(frozen=True)
class RemediationLibraryView:
    entries: list[RemediationEntry]
    categories: list[str]
    selected_category: str
    query: str
    total_count: int
    export_links: list[RemediationExportLink]


@dataclass(frozen=True)
class RemediationLibraryExport:
    filename: str
    media_type: str
    content: str


def build_remediation_library_view(
    query: str | None = None,
    category: str | None = None,
) -> RemediationLibraryView:
    selected_category = (category or "").strip()
    query_text = (query or "").strip()
    entries = filter_remediations(query=query_text, category=selected_category)
    return RemediationLibraryView(
        entries=entries,
        categories=remediation_categories(),
        selected_category=selected_category,
        query=query_text,
        total_count=len(entries),
        export_links=remediation_export_links(query_text, selected_category),
    )


def remediation_export_links(query: str = "", category: str = "") -> list[RemediationExportLink]:
    return [
        RemediationExportLink(
            format=report_format.value,
            label=export_label(report_format),
            url=remediation_export_url(report_format, query=query, category=category),
        )
        for report_format in REMEDIATION_EXPORT_FORMATS
    ]


def remediation_export_url(report_format: ReportFormat, query: str = "", category: str = "") -> str:
    params = {key: value for key, value in {"q": query, "category": category}.items() if value}
    query_string = urlencode(params)
    suffix = f"?{query_string}" if query_string else ""
    return f"/remediations/export/{report_format.value}{suffix}"


def export_label(report_format: ReportFormat) -> str:
    if report_format is ReportFormat.JSON:
        return "JSON"
    if report_format is ReportFormat.HTML:
        return "HTML"
    return "Markdown"


def build_remediation_library_export(
    export_format: ReportFormat,
    query: str | None = None,
    category: str | None = None,
) -> RemediationLibraryExport:
    if export_format not in REMEDIATION_EXPORT_FORMATS:
        raise ValueError(f"unsupported remediation export format: {export_format.value}")
    view = build_remediation_library_view(query=query, category=category)
    filename = remediation_export_filename(export_format, view)
    if export_format is ReportFormat.JSON:
        return RemediationLibraryExport(
            filename=filename,
            media_type="application/json",
            content=render_remediation_library_json(view),
        )
    if export_format is ReportFormat.HTML:
        return RemediationLibraryExport(
            filename=filename,
            media_type="text/html; charset=utf-8",
            content=render_remediation_library_html(view),
        )
    return RemediationLibraryExport(
        filename=filename,
        media_type="text/markdown; charset=utf-8",
        content=render_remediation_library_markdown(view),
    )


def remediation_export_filename(export_format: ReportFormat, view: RemediationLibraryView) -> str:
    extension = {
        ReportFormat.JSON: "json",
        ReportFormat.MARKDOWN: "md",
        ReportFormat.HTML: "html",
    }[export_format]
    parts = ["remediation-library"]
    if view.selected_category:
        parts.append(view.selected_category.replace("_", "-"))
    if view.query:
        parts.append("filtered")
    return "-".join(parts) + f".{extension}"


def render_remediation_library_json(view: RemediationLibraryView) -> str:
    payload = {
        "query": view.query,
        "category": view.selected_category or None,
        "count": view.total_count,
        "entries": [
            {
                "id": entry.id,
                "title": entry.title,
                "category": entry.category,
                "severity": entry.severity.value,
                "effort": entry.effort,
                "applies_to": list(entry.applies_to),
                "risk": entry.risk,
                "remediation": entry.remediation,
                "counter_test": entry.counter_test,
            }
            for entry in view.entries
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def render_remediation_library_markdown(view: RemediationLibraryView) -> str:
    lines = [
        "# Remediation Library",
        "",
        f"Visible entries: {view.total_count}",
        f"Category filter: {view.selected_category or 'all'}",
        f"Search filter: {view.query or 'none'}",
        "",
    ]
    for entry in view.entries:
        lines.extend(
            [
                f"## {entry.title}",
                "",
                f"- ID: {entry.id}",
                f"- Category: {entry.category}",
                f"- Severity: {entry.severity.value}",
                f"- Effort: {entry.effort}",
                f"- Applies to: {', '.join(entry.applies_to)}",
                "",
                "Risk:",
                entry.risk,
                "",
                "Remediation:",
                entry.remediation,
                "",
                "Counter-test:",
                "```text",
                entry.counter_test,
                "```",
                "",
            ]
        )
    if not view.entries:
        lines.extend(["No remediation entry found.", ""])
    return "\n".join(lines)


def render_remediation_library_html(view: RemediationLibraryView) -> str:
    entries = "\n".join(render_remediation_entry_html(entry) for entry in view.entries)
    if not entries:
        entries = "<p>No remediation entry found.</p>"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Remediation Library</title>
  <style>
    body {{ font-family: Arial, sans-serif; color: #1c2430; margin: 32px; }}
    article {{ border: 1px solid #d7dee8; border-radius: 6px; margin: 16px 0; padding: 16px; }}
    h1 {{ margin-bottom: 4px; }}
    h2 {{ margin-bottom: 6px; }}
    dt {{ color: #667085; font-weight: 700; margin-top: 10px; }}
    dd {{ margin-left: 0; }}
    pre {{ background: #f8fafc; border: 1px solid #d7dee8; padding: 8px; white-space: pre-wrap; }}
  </style>
</head>
<body>
  <h1>Remediation Library</h1>
  <p>Visible entries: {view.total_count}</p>
  <p>Category filter: {escape(view.selected_category or "all")}</p>
  <p>Search filter: {escape(view.query or "none")}</p>
  {entries}
</body>
</html>
"""


def render_remediation_entry_html(entry: RemediationEntry) -> str:
    return f"""<article>
  <h2>{escape(entry.title)}</h2>
  <dl>
    <dt>ID</dt><dd>{escape(entry.id)}</dd>
    <dt>Category</dt><dd>{escape(entry.category)}</dd>
    <dt>Severity</dt><dd>{escape(entry.severity.value)}</dd>
    <dt>Effort</dt><dd>{escape(entry.effort)}</dd>
    <dt>Applies to</dt><dd>{escape(", ".join(entry.applies_to))}</dd>
    <dt>Risk</dt><dd>{escape(entry.risk)}</dd>
    <dt>Remediation</dt><dd>{escape(entry.remediation)}</dd>
    <dt>Counter-test</dt><dd><pre>{escape(entry.counter_test)}</pre></dd>
  </dl>
</article>"""
