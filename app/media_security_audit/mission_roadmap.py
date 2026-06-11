"""Mission roadmap exports for technician handoff."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from media_security_audit.storage import JsonStore
from media_security_audit.web_ui import MissionView, build_mission_view


MISSION_ROADMAP_SCHEMA_VERSION = 1


class MissionRoadmapExportFormat(str, Enum):
    JSON = "json"
    MARKDOWN = "markdown"


@dataclass(frozen=True)
class MissionRoadmapExport:
    format: MissionRoadmapExportFormat
    filename: str
    media_type: str
    content: str


def build_mission_roadmap_payload(
    store: JsonStore,
    mission_id: str,
    reports_dir: Path,
) -> dict[str, object]:
    view = build_mission_view(store, mission_id, reports_dir=reports_dir)
    return mission_roadmap_payload(view)


def mission_roadmap_payload(view: MissionView) -> dict[str, object]:
    return {
        "schema_version": MISSION_ROADMAP_SCHEMA_VERSION,
        "mission": {
            "id": view.mission.id,
            "name": view.mission.name,
            "client_id": view.mission.client_id,
            "client_name": view.mission.client_name,
            "audit_type": view.mission.audit_type,
            "status": view.mission.status,
            "preparation_status": view.mission.preparation_status,
        },
        "summary": {
            "steps": len(view.action_roadmap),
            "ready": len([step for step in view.action_roadmap if step.status == "ready"]),
            "warning": len(
                [
                    step
                    for step in view.action_roadmap
                    if step.status in {"warning", "missing"}
                ]
            ),
            "blocked": len(
                [step for step in view.action_roadmap if step.status == "blocked"]
            ),
        },
        "steps": [
            {
                "number": step.number,
                "label": step.label,
                "status": step.status,
                "detail": step.detail,
                "action_label": step.action_label,
                "action_href": step.action_href,
            }
            for step in view.action_roadmap
        ],
    }


def format_mission_roadmap_markdown(payload: dict[str, object]) -> str:
    mission = payload["mission"]
    summary = payload["summary"]
    lines = [
        "# Mission Roadmap",
        "",
        f"- Mission: `{mission['name']}`",
        f"- Mission id: `{mission['id']}`",
        f"- Client: `{mission['client_name']}`",
        f"- Audit type: `{mission['audit_type']}`",
        f"- Preparation status: `{mission['preparation_status']}`",
        f"- Ready steps: `{summary['ready']}`",
        f"- Warning steps: `{summary['warning']}`",
        f"- Blocked steps: `{summary['blocked']}`",
        "",
        "## Steps",
        "",
    ]
    for step in payload["steps"]:
        lines.extend(
            [
                f"### {step['number']}. {step['label']}",
                "",
                f"- Status: `{step['status']}`",
                f"- Detail: {step['detail']}",
                f"- Action: {step['action_label']} `{step['action_href']}`",
                "",
            ]
        )
    return "\n".join(lines)


def build_mission_roadmap_export(
    store: JsonStore,
    mission_id: str,
    reports_dir: Path,
    export_format: MissionRoadmapExportFormat,
) -> MissionRoadmapExport:
    payload = build_mission_roadmap_payload(store, mission_id, reports_dir)
    filename = mission_roadmap_export_filename(mission_id, export_format)
    if export_format is MissionRoadmapExportFormat.JSON:
        return MissionRoadmapExport(
            format=export_format,
            filename=filename,
            media_type="application/json",
            content=json.dumps(payload, indent=2, sort_keys=True),
        )
    return MissionRoadmapExport(
        format=export_format,
        filename=filename,
        media_type="text/markdown; charset=utf-8",
        content=format_mission_roadmap_markdown(payload),
    )


def mission_roadmap_export_filename(
    mission_id: str,
    export_format: MissionRoadmapExportFormat,
) -> str:
    suffix = "json" if export_format is MissionRoadmapExportFormat.JSON else "md"
    return f"{mission_id}-roadmap.{suffix}"
