"""Mission export packages for the local web interface."""

from __future__ import annotations

import json
from hashlib import sha256
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile

from pydantic import BaseModel

from media_security_audit.audit_templates import get_audit_template
from media_security_audit.models import Client, Mission, ReportFormat, ScanRun, utc_now
from media_security_audit.reports import scope_summary
from media_security_audit.storage import JsonStore
from media_security_audit.web_authorization import (
    AuthorizationBriefFormat,
    authorization_decision,
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
    integrity_status: str
    integrity_detail: str


@dataclass(frozen=True)
class ArchiveMember:
    name: str
    content: bytes


@dataclass(frozen=True)
class MissionExportVerification:
    status: str
    detail: str
    checked_files: int
    missing_files: list[str]
    mismatched_files: list[str]
    unexpected_files: list[str]


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
    members = mission_export_members(
        client=client,
        mission=mission,
        findings=findings,
        activity_events=activity_events,
        scan_runs=scan_runs,
        report_paths=report_paths,
        authorization_brief_paths=authorization_brief_paths,
    )
    manifest = build_mission_export_manifest(
        mission=mission,
        client=client,
        finding_count=len(findings),
        activity_event_count=len(activity_events),
        scan_runs=scan_runs,
        report_paths=report_paths,
        authorization_brief_paths=authorization_brief_paths,
        archive_members=members,
    )

    with ZipFile(output_path, mode="w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
        for member in members:
            archive.writestr(member.name, member.content)

    return output_path


def mission_export_members(
    client: Client | None,
    mission: Mission,
    findings: list[BaseModel],
    activity_events: list[BaseModel],
    scan_runs: list[ScanRun],
    report_paths: list[Path],
    authorization_brief_paths: list[Path],
) -> list[ArchiveMember]:
    members: list[ArchiveMember] = []
    if client is not None:
        members.append(text_member("data/client.json", model_json(client)))
    members.append(text_member("data/mission.json", model_json(mission)))
    for finding in findings:
        members.append(text_member(f"data/findings/{finding.id}.json", model_json(finding)))
    for event in activity_events:
        members.append(text_member(f"data/activity/{event.id}.json", model_json(event)))
    for run in scan_runs:
        members.append(text_member(f"data/runs/{run.id}.json", model_json(run)))
    for path in authorization_brief_paths:
        members.append(file_member(f"authorization/{path.name}", path))
    for path in report_paths:
        members.append(file_member(f"reports/{path.name}", path))
    return members


def build_mission_export_manifest(
    mission: Mission,
    client: Client | None,
    finding_count: int,
    activity_event_count: int,
    scan_runs: list[ScanRun],
    report_paths: list[Path],
    authorization_brief_paths: list[Path],
    archive_members: list[ArchiveMember] | None = None,
) -> dict[str, object]:
    template = get_audit_template(mission.audit_template_id)
    reports = [f"reports/{path.name}" for path in report_paths]
    authorization_briefs = [f"authorization/{path.name}" for path in authorization_brief_paths]
    evidence_path_count = sum(len(run.evidence_paths) for run in scan_runs)
    archive_files = archive_member_entries(archive_members or [])

    return {
        "manifest_version": 2,
        "generated_at": utc_now().isoformat(),
        "mission_id": mission.id,
        "mission_name": mission.name,
        "client_id": mission.client_id,
        "client_name": client.name if client else None,
        "audit_type": mission.audit_type.value,
        "audit_template_id": mission.audit_template_id,
        "audit_template_title": template.title if template else None,
        "mission_status": mission.status.value,
        "authorization_decision": authorization_decision(mission),
        "selected_checks": [check.value for check in mission.selected_checks],
        "scope": scope_summary(mission),
        "finding_count": finding_count,
        "activity_event_count": activity_event_count,
        "scan_run_count": len(scan_runs),
        "evidence_path_count": evidence_path_count,
        "report_count": len(reports),
        "authorization_brief_count": len(authorization_briefs),
        "archive_file_count": len(archive_files),
        "archive_files": archive_files,
        "reports": reports,
        "authorization_briefs": authorization_briefs,
    }


def list_mission_export(mission_id: str, reports_dir: Path) -> MissionExportLink | None:
    path = mission_export_path(reports_dir, mission_id)
    if not path.exists() or not path.is_file():
        return None
    verification = verify_mission_export(path)
    return MissionExportLink(
        filename=path.name,
        size_bytes=path.stat().st_size,
        integrity_status=verification.status,
        integrity_detail=verification.detail,
    )


def mission_export_file(reports_dir: Path, mission_id: str) -> Path:
    path = mission_export_path(reports_dir, mission_id)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError("mission export package not found")
    return path


def verify_mission_export(path: Path) -> MissionExportVerification:
    try:
        with ZipFile(path) as archive:
            names = set(archive.namelist())
            if "manifest.json" not in names:
                return export_verification_failed("manifest.json is missing")

            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
            manifest_entries = manifest.get("archive_files")
            if not isinstance(manifest_entries, list):
                return export_verification_failed("manifest archive_files is missing")
            if not manifest_entries:
                return export_verification_failed("manifest archive_files is empty")

            missing_files: list[str] = []
            mismatched_files: list[str] = []
            checked_files = 0
            expected_names: set[str] = set()

            for entry in manifest_entries:
                if not isinstance(entry, dict):
                    mismatched_files.append("<invalid-manifest-entry>")
                    continue

                member_name = str(entry.get("path") or "").strip()
                if not member_name:
                    mismatched_files.append("<missing-member-path>")
                    continue

                expected_names.add(member_name)
                if member_name not in names:
                    missing_files.append(member_name)
                    continue

                content = archive.read(member_name)
                checked_files += 1
                if entry.get("size_bytes") != len(content):
                    mismatched_files.append(member_name)
                    continue
                if entry.get("sha256") != sha256(content).hexdigest():
                    mismatched_files.append(member_name)

            unexpected_files = sorted(names - expected_names - {"manifest.json"})
    except (FileNotFoundError, BadZipFile, json.JSONDecodeError, OSError, UnicodeDecodeError) as error:
        return export_verification_failed(f"package cannot be verified: {error}")

    return export_verification_result(
        checked_files=checked_files,
        missing_files=sorted(missing_files),
        mismatched_files=sorted(set(mismatched_files)),
        unexpected_files=unexpected_files,
    )


def export_verification_result(
    checked_files: int,
    missing_files: list[str],
    mismatched_files: list[str],
    unexpected_files: list[str],
) -> MissionExportVerification:
    if missing_files or mismatched_files:
        issue_count = len(missing_files) + len(mismatched_files)
        return MissionExportVerification(
            status="failed",
            detail=f"Integrity check failed: {issue_count} packaged file issue(s).",
            checked_files=checked_files,
            missing_files=missing_files,
            mismatched_files=mismatched_files,
            unexpected_files=unexpected_files,
        )
    if unexpected_files:
        return MissionExportVerification(
            status="warning",
            detail=f"{checked_files} packaged file(s) verified; {len(unexpected_files)} unexpected file(s).",
            checked_files=checked_files,
            missing_files=missing_files,
            mismatched_files=mismatched_files,
            unexpected_files=unexpected_files,
        )
    return MissionExportVerification(
        status="ready",
        detail=f"{checked_files} packaged file(s) verified.",
        checked_files=checked_files,
        missing_files=missing_files,
        mismatched_files=mismatched_files,
        unexpected_files=unexpected_files,
    )


def export_verification_failed(detail: str) -> MissionExportVerification:
    return MissionExportVerification(
        status="failed",
        detail=detail,
        checked_files=0,
        missing_files=[],
        mismatched_files=[],
        unexpected_files=[],
    )


def text_member(name: str, content: str) -> ArchiveMember:
    return ArchiveMember(name=name, content=content.encode("utf-8"))


def file_member(name: str, path: Path) -> ArchiveMember:
    return ArchiveMember(name=name, content=path.read_bytes())


def archive_member_entries(members: list[ArchiveMember]) -> list[dict[str, object]]:
    return [
        {
            "path": member.name,
            "size_bytes": len(member.content),
            "sha256": sha256(member.content).hexdigest(),
        }
        for member in members
    ]


def model_json(model: BaseModel) -> str:
    return json.dumps(model.model_dump(mode="json"), indent=2, ensure_ascii=False)
