"""Read-only scan plan exports shared by CLI and web workflows."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum

from media_security_audit.models import Mission
from media_security_audit.web_readiness import ScanPlanPreview, build_scan_plan_previews


SCAN_PLAN_SCHEMA_VERSION = 1


class ScanPlanExportFormat(str, Enum):
    JSON = "json"
    MARKDOWN = "markdown"


@dataclass(frozen=True)
class ScanPlanExport:
    format: ScanPlanExportFormat
    filename: str
    media_type: str
    content: str


def scan_plan_payload(
    mission: Mission,
    plans: list[ScanPlanPreview] | None = None,
) -> dict[str, object]:
    planned = plans if plans is not None else build_scan_plan_previews(mission)
    ready_count = len([plan for plan in planned if plan.status == "ready"])
    blocked_count = len([plan for plan in planned if plan.status == "blocked"])
    command_count = sum(len(plan.commands) for plan in planned)
    approved_scope_count = len([item for item in mission.scope if item.approved and not item.excluded])

    return {
        "schema_version": SCAN_PLAN_SCHEMA_VERSION,
        "mission": {
            "id": mission.id,
            "name": mission.name,
            "status": mission.status.value,
            "authorized": mission.is_authorized,
            "approved_scope_count": approved_scope_count,
            "selected_check_count": len(mission.selected_checks),
        },
        "summary": {
            "checks": len(planned),
            "ready": ready_count,
            "blocked": blocked_count,
            "planned_commands": command_count,
            "execution": "not_executed",
        },
        "plans": [
            {
                "label": plan.label,
                "status": plan.status,
                "detail": plan.detail,
                "commands": plan.commands,
            }
            for plan in planned
        ],
    }


def format_scan_plan_json(
    mission: Mission,
    plans: list[ScanPlanPreview] | None = None,
) -> str:
    return json.dumps(scan_plan_payload(mission, plans), indent=2, sort_keys=True)


def format_scan_plan_text(
    mission: Mission,
    plans: list[ScanPlanPreview] | None = None,
) -> str:
    planned = plans if plans is not None else build_scan_plan_previews(mission)
    ready_count = len([plan for plan in planned if plan.status == "ready"])
    blocked_count = len([plan for plan in planned if plan.status == "blocked"])
    command_count = sum(len(plan.commands) for plan in planned)
    approved_scope_count = len([item for item in mission.scope if item.approved and not item.excluded])
    lines = [
        f"Scan plan for mission: {mission.name}",
        f"Mission ID: {mission.id}",
        f"Status: {mission.status.value}",
        f"Authorization: {'recorded' if mission.is_authorized else 'missing'}",
        f"Approved scope: {approved_scope_count}",
        f"Selected checks: {len(mission.selected_checks)}",
        f"Ready checks: {ready_count}",
        f"Blocked checks: {blocked_count}",
        f"Planned commands: {command_count}",
        "Execution: not executed by this command",
        "",
    ]
    for plan in planned:
        lines.append(f"[{plan.status}] {plan.label}")
        lines.append(f"  {plan.detail}")
        if plan.commands:
            lines.extend(f"  - {command}" for command in plan.commands)
        else:
            lines.append("  - no command")
        lines.append("")
    return "\n".join(lines).rstrip()


def format_scan_plan_markdown(
    mission: Mission,
    plans: list[ScanPlanPreview] | None = None,
) -> str:
    text = format_scan_plan_text(mission, plans)
    lines = ["# Scan Plan", ""]
    for line in text.splitlines():
        if line.startswith("["):
            lines.append(f"## {line}")
        elif line.startswith("  - "):
            lines.append(f"- `{line[4:]}`")
        elif line.startswith("  "):
            lines.append(line.strip())
        elif line:
            lines.append(line)
        else:
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_scan_plan_export(
    mission: Mission,
    export_format: ScanPlanExportFormat,
) -> ScanPlanExport:
    filename = scan_plan_export_filename(mission.id, export_format)
    if export_format is ScanPlanExportFormat.JSON:
        return ScanPlanExport(
            format=export_format,
            filename=filename,
            media_type="application/json",
            content=format_scan_plan_json(mission),
        )
    return ScanPlanExport(
        format=export_format,
        filename=filename,
        media_type="text/markdown; charset=utf-8",
        content=format_scan_plan_markdown(mission),
    )


def scan_plan_export_filename(mission_id: str, export_format: ScanPlanExportFormat) -> str:
    suffix = "json" if export_format is ScanPlanExportFormat.JSON else "md"
    return f"{mission_id}-scan-plan.{suffix}"
