"""Mission export packages for the local web interface."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from pydantic import BaseModel

from media_security_audit.models import ReportFormat, utc_now
from media_security_audit.storage import JsonStore
from media_security_audit.web_authorization import (
    AuthorizationBriefFormat,
    authorization_brief_path,
)
from media_security_audit.web_reports import (
    mission_report_dir,
    mission_report_path,
)


@dataclass(frozen=True)
class MissionExportLink:
    filename: str
    size_bytes: int


def mission_export_path(reports_dir: Path, mission_id: str) -> Path:
    return mission_report_dir(reports_dir, mission_id) / f"{mission_id}-package.zip"


def generate_mission_export(store: JsonStore, mission_id: str, reports_dir: Path) -> Path:
    client = None
    mission = store.get_mission(mission_id)
    try:
        client = store.get_client(mission.client_id)
    except FileNotFoundError:
        client = None

    findings = store.list_findings(mission_id)
    activity_events = store.list_activity_events(mission_id)
    scan_runs = store.list_scan_runs(mission_id)
    report_paths = [
        path
        for path in (
            mission_report_path(reports_dir, mission_id, report_format)
            for report_format in ReportFormat
        )
        if path.exists() and path.is_file()
    ]
    authorization_brief_paths = [
        path
        for path in (
            authorization_brief_path(reports_dir, mission_id, brief_format)
            for brief_format in AuthorizationBriefFormat
        )
        if path.exists() and path.is_file()
    ]

    output_path = mission_export_path(reports_dir, mission_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "generated_at": utc_now().isoformat(),
        "mission_id": mission.id,
        "client_id": mission.client_id,
        "finding_count": len(findings),
        "activity_event_count": len(activity_events),
        "scan_run_count": len(scan_runs),
        "reports": [f"reports/{path.name}" for path in report_paths],
        "authorization_briefs": [
            f"authorization/{path.name}" for path in authorization_brief_paths
        ],
    }

    with ZipFile(output_path, mode="w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
        if client is not None:
            archive.writestr("data/client.json", model_json(client))
        archive.writestr("data/mission.json", model_json(mission))
        for finding in findings:
            archive.writestr(f"data/findings/{finding.id}.json", model_json(finding))
        for event in activity_events:
            archive.writestr(f"data/activity/{event.id}.json", model_json(event))
        for run in scan_runs:
            archive.writestr(f"data/runs/{run.id}.json", model_json(run))
        for path in authorization_brief_paths:
            archive.write(path, f"authorization/{path.name}")
        for path in report_paths:
            archive.write(path, f"reports/{path.name}")

    return output_path


def list_mission_export(mission_id: str, reports_dir: Path) -> MissionExportLink | None:
    path = mission_export_path(reports_dir, mission_id)
    if not path.exists() or not path.is_file():
        return None
    return MissionExportLink(filename=path.name, size_bytes=path.stat().st_size)


def mission_export_file(reports_dir: Path, mission_id: str) -> Path:
    path = mission_export_path(reports_dir, mission_id)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError("mission export package not found")
    return path


def model_json(model: BaseModel) -> str:
    return json.dumps(model.model_dump(mode="json"), indent=2, ensure_ascii=False)
