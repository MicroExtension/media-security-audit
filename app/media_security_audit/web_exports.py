"""Mission export packages for the local web interface."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from pathlib import Path
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile

from pydantic import BaseModel

from media_security_audit.audit_templates import get_audit_template
from media_security_audit.mission_readiness import (
    MissionReadinessExport,
    MissionReadinessExportFormat,
    build_mission_readiness_export,
    build_mission_readiness_payload,
)
from media_security_audit.models import Client, Mission, ReportFormat, ScanRun, utc_now
from media_security_audit.reports import scope_summary
from media_security_audit.scan_plan_exports import (
    ScanPlanExport,
    ScanPlanExportFormat,
    build_scan_plan_export,
    scan_plan_payload,
)
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
    checked_files: int
    missing_files: list[str]
    mismatched_files: list[str]
    unexpected_files: list[str]

    @property
    def missing_count(self) -> int:
        return len(self.missing_files)

    @property
    def mismatched_count(self) -> int:
        return len(self.mismatched_files)

    @property
    def unexpected_count(self) -> int:
        return len(self.unexpected_files)

    @property
    def has_integrity_issues(self) -> bool:
        return bool(self.missing_files or self.mismatched_files or self.unexpected_files)


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


class MissionExportVerificationFormat(str, Enum):
    JSON = "json"
    MARKDOWN = "markdown"


@dataclass(frozen=True)
class MissionExportVerificationExport:
    format: MissionExportVerificationFormat
    filename: str
    media_type: str
    content: str


class MissionExportManifestFormat(str, Enum):
    JSON = "json"
    MARKDOWN = "markdown"


@dataclass(frozen=True)
class MissionExportManifestExport:
    format: MissionExportManifestFormat
    filename: str
    media_type: str
    content: str


class MissionExportInventoryFormat(str, Enum):
    JSON = "json"
    MARKDOWN = "markdown"


@dataclass(frozen=True)
class MissionExportInventoryExport:
    format: MissionExportInventoryFormat
    filename: str
    media_type: str
    content: str


@dataclass(frozen=True)
class MissionExportInventoryItem:
    mission_id: str
    mission_name: str
    client_id: str
    client_name: str | None
    package_path: str
    filename: str | None
    size_bytes: int
    status: str
    detail: str
    checked_files: int
    missing_files: int
    mismatched_files: int
    unexpected_files: int


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
    scan_plan_exports = [
        build_scan_plan_export(mission, export_format)
        for export_format in ScanPlanExportFormat
    ]
    readiness_exports = [
        build_mission_readiness_export(store, mission_id, reports_dir, export_format)
        for export_format in MissionReadinessExportFormat
    ]
    readiness_payload = build_mission_readiness_payload(store, mission_id, reports_dir)

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
        scan_plan_exports=scan_plan_exports,
        readiness_exports=readiness_exports,
    )
    manifest = build_mission_export_manifest(
        mission=mission,
        client=client,
        finding_count=len(findings),
        activity_event_count=len(activity_events),
        scan_runs=scan_runs,
        report_paths=report_paths,
        authorization_brief_paths=authorization_brief_paths,
        scan_plan_exports=scan_plan_exports,
        readiness_exports=readiness_exports,
        readiness_payload=readiness_payload,
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
    scan_plan_exports: list[ScanPlanExport],
    readiness_exports: list[MissionReadinessExport],
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
    for export in scan_plan_exports:
        members.append(text_member(f"scan-plan/{export.filename}", export.content))
    for export in readiness_exports:
        members.append(text_member(f"readiness/{export.filename}", export.content))
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
    scan_plan_exports: list[ScanPlanExport],
    readiness_exports: list[MissionReadinessExport],
    readiness_payload: dict[str, object],
    archive_members: list[ArchiveMember] | None = None,
) -> dict[str, object]:
    template = get_audit_template(mission.audit_template_id)
    reports = [f"reports/{path.name}" for path in report_paths]
    authorization_briefs = [f"authorization/{path.name}" for path in authorization_brief_paths]
    scan_plans = [f"scan-plan/{export.filename}" for export in scan_plan_exports]
    readiness_exports_list = [f"readiness/{export.filename}" for export in readiness_exports]
    evidence_path_count = sum(len(run.evidence_paths) for run in scan_runs)
    archive_files = archive_member_entries(archive_members or [])

    return {
        "manifest_version": 4,
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
        "scan_plan_count": len(scan_plans),
        "scan_plan_summary": scan_plan_payload(mission)["summary"],
        "readiness_export_count": len(readiness_exports_list),
        "readiness_status": readiness_payload["status"],
        "readiness_summary": readiness_payload["summary"],
        "archive_file_count": len(archive_files),
        "archive_files": archive_files,
        "reports": reports,
        "authorization_briefs": authorization_briefs,
        "scan_plans": scan_plans,
        "readiness_exports": readiness_exports_list,
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
        checked_files=verification.checked_files,
        missing_files=verification.missing_files,
        mismatched_files=verification.mismatched_files,
        unexpected_files=verification.unexpected_files,
    )


def build_mission_export_inventory(
    store: JsonStore,
    reports_dir: Path,
    include_missing: bool = False,
) -> list[MissionExportInventoryItem]:
    items: list[MissionExportInventoryItem] = []
    missions = sorted(store.list_missions(), key=lambda mission: (mission.name.lower(), mission.id))
    for mission in missions:
        package_path = mission_export_path(reports_dir, mission.id)
        export_link = list_mission_export(mission.id, reports_dir)
        if export_link is None:
            if include_missing:
                items.append(
                    mission_export_inventory_item(
                        mission=mission,
                        client_name=mission_export_inventory_client_name(store, mission),
                        package_path=package_path,
                        export_link=None,
                    )
                )
            continue
        items.append(
            mission_export_inventory_item(
                mission=mission,
                client_name=mission_export_inventory_client_name(store, mission),
                package_path=package_path,
                export_link=export_link,
            )
        )
    return items


def mission_export_inventory_client_name(store: JsonStore, mission: Mission) -> str | None:
    try:
        return store.get_client(mission.client_id).name
    except FileNotFoundError:
        return None


def mission_export_inventory_item(
    mission: Mission,
    client_name: str | None,
    package_path: Path,
    export_link: MissionExportLink | None,
) -> MissionExportInventoryItem:
    if export_link is None:
        return MissionExportInventoryItem(
            mission_id=mission.id,
            mission_name=mission.name,
            client_id=mission.client_id,
            client_name=client_name,
            package_path=str(package_path),
            filename=None,
            size_bytes=0,
            status="missing",
            detail="mission export package not found",
            checked_files=0,
            missing_files=0,
            mismatched_files=0,
            unexpected_files=0,
        )
    return MissionExportInventoryItem(
        mission_id=mission.id,
        mission_name=mission.name,
        client_id=mission.client_id,
        client_name=client_name,
        package_path=str(package_path),
        filename=export_link.filename,
        size_bytes=export_link.size_bytes,
        status=export_link.integrity_status,
        detail=export_link.integrity_detail,
        checked_files=export_link.checked_files,
        missing_files=export_link.missing_count,
        mismatched_files=export_link.mismatched_count,
        unexpected_files=export_link.unexpected_count,
    )


def mission_export_inventory_payload(items: list[MissionExportInventoryItem]) -> dict[str, object]:
    statuses = {status: 0 for status in ("ready", "warning", "failed", "missing")}
    for item in items:
        statuses[item.status] = statuses.get(item.status, 0) + 1
    return {
        "schema_version": 1,
        "summary": {
            "packages": len([item for item in items if item.status != "missing"]),
            "items": len(items),
            "ready": statuses.get("ready", 0),
            "warning": statuses.get("warning", 0),
            "failed": statuses.get("failed", 0),
            "missing": statuses.get("missing", 0),
        },
        "items": [
            {
                "mission_id": item.mission_id,
                "mission_name": item.mission_name,
                "client_id": item.client_id,
                "client_name": item.client_name,
                "package_path": item.package_path,
                "filename": item.filename,
                "size_bytes": item.size_bytes,
                "status": item.status,
                "detail": item.detail,
                "checked_files": item.checked_files,
                "missing_files": item.missing_files,
                "mismatched_files": item.mismatched_files,
                "unexpected_files": item.unexpected_files,
            }
            for item in items
        ],
    }


def format_mission_export_inventory_json(items: list[MissionExportInventoryItem]) -> str:
    return json.dumps(mission_export_inventory_payload(items), indent=2, sort_keys=True)


def format_mission_export_inventory_markdown(items: list[MissionExportInventoryItem]) -> str:
    payload = mission_export_inventory_payload(items)
    summary = payload["summary"]
    lines = [
        "# Mission Export Inventory",
        "",
        f"- Items: `{summary['items']}`",
        f"- Packages: `{summary['packages']}`",
        f"- Ready: `{summary['ready']}`",
        f"- Warning: `{summary['warning']}`",
        f"- Failed: `{summary['failed']}`",
        f"- Missing: `{summary['missing']}`",
        "- Execution: `not_executed`",
        "",
        "| Mission | Client | Status | Package | Integrity | Counters |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    if not items:
        lines.append("| None | - | - | - | No mission export package found. | - |")
    for item in items:
        package = item.filename or "missing"
        counters = (
            f"checked {item.checked_files}; missing {item.missing_files}; "
            f"mismatched {item.mismatched_files}; unexpected {item.unexpected_files}"
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(f"{item.mission_name} ({item.mission_id})"),
                    markdown_cell(item.client_name or item.client_id),
                    markdown_cell(item.status),
                    markdown_cell(package),
                    markdown_cell(item.detail),
                    markdown_cell(counters),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def markdown_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def format_mission_export_inventory_text(items: list[MissionExportInventoryItem]) -> str:
    payload = mission_export_inventory_payload(items)
    summary = payload["summary"]
    lines = [
        "Mission export inventory",
        f"Items: {summary['items']}",
        f"Packages: {summary['packages']}",
        (
            f"Ready: {summary['ready']} | Warning: {summary['warning']} | "
            f"Failed: {summary['failed']} | Missing: {summary['missing']}"
        ),
        "Execution: not executed by this command",
    ]
    for item in items:
        lines.append(
            f"[{item.status}] {item.mission_id} | {item.mission_name} | "
            f"{item.filename or '<missing>'} | {item.detail}"
        )
    return "\n".join(lines)


def build_mission_export_inventory_export(
    store: JsonStore,
    reports_dir: Path,
    export_format: MissionExportInventoryFormat,
    include_missing: bool = True,
) -> MissionExportInventoryExport:
    items = build_mission_export_inventory(
        store,
        reports_dir,
        include_missing=include_missing,
    )
    filename = mission_export_inventory_export_filename(export_format)
    if export_format is MissionExportInventoryFormat.JSON:
        return MissionExportInventoryExport(
            format=export_format,
            filename=filename,
            media_type="application/json",
            content=format_mission_export_inventory_json(items),
        )
    return MissionExportInventoryExport(
        format=export_format,
        filename=filename,
        media_type="text/markdown; charset=utf-8",
        content=format_mission_export_inventory_markdown(items),
    )


def mission_export_inventory_export_filename(export_format: MissionExportInventoryFormat) -> str:
    suffix = "json" if export_format is MissionExportInventoryFormat.JSON else "md"
    return f"mission-export-inventory.{suffix}"


def mission_export_file(reports_dir: Path, mission_id: str) -> Path:
    path = mission_export_path(reports_dir, mission_id)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError("mission export package not found")
    return path


def build_mission_export_manifest_export(
    mission_id: str,
    reports_dir: Path,
    export_format: MissionExportManifestFormat,
) -> MissionExportManifestExport:
    path = mission_export_file(reports_dir, mission_id)
    manifest = read_mission_export_manifest(path)
    filename = mission_export_manifest_export_filename(mission_id, export_format)
    if export_format is MissionExportManifestFormat.JSON:
        return MissionExportManifestExport(
            format=export_format,
            filename=filename,
            media_type="application/json",
            content=format_mission_export_manifest_json(manifest),
        )
    return MissionExportManifestExport(
        format=export_format,
        filename=filename,
        media_type="text/markdown; charset=utf-8",
        content=format_mission_export_manifest_markdown(manifest),
    )


def mission_export_manifest_export_filename(
    mission_id: str,
    export_format: MissionExportManifestFormat,
) -> str:
    suffix = "json" if export_format is MissionExportManifestFormat.JSON else "md"
    return f"{mission_id}-export-manifest.{suffix}"


def read_mission_export_manifest(path: Path) -> dict[str, object]:
    try:
        with ZipFile(path) as archive:
            if "manifest.json" not in archive.namelist():
                raise FileNotFoundError("manifest.json is missing")
            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
    except (BadZipFile, json.JSONDecodeError, OSError, UnicodeDecodeError) as error:
        raise ValueError(f"mission export manifest cannot be read: {error}") from error
    if not isinstance(manifest, dict):
        raise ValueError("mission export manifest must be a JSON object")
    return manifest


def build_mission_export_verification_export(
    mission_id: str,
    reports_dir: Path,
    export_format: MissionExportVerificationFormat,
) -> MissionExportVerificationExport:
    path = mission_export_file(reports_dir, mission_id)
    verification = verify_mission_export(path)
    filename = mission_export_verification_export_filename(mission_id, export_format)
    if export_format is MissionExportVerificationFormat.JSON:
        return MissionExportVerificationExport(
            format=export_format,
            filename=filename,
            media_type="application/json",
            content=format_mission_export_verification_json(path, verification),
        )
    return MissionExportVerificationExport(
        format=export_format,
        filename=filename,
        media_type="text/markdown; charset=utf-8",
        content=format_mission_export_verification_markdown(path, verification),
    )


def mission_export_verification_export_filename(
    mission_id: str,
    export_format: MissionExportVerificationFormat,
) -> str:
    suffix = "json" if export_format is MissionExportVerificationFormat.JSON else "md"
    return f"{mission_id}-export-verification.{suffix}"


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


def mission_export_verification_payload(
    package_path: Path,
    verification: MissionExportVerification,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "package": str(package_path),
        "package_name": package_path.name,
        "status": verification.status,
        "detail": verification.detail,
        "execution": "not_executed",
        "summary": {
            "checked_files": verification.checked_files,
            "missing_files": len(verification.missing_files),
            "mismatched_files": len(verification.mismatched_files),
            "unexpected_files": len(verification.unexpected_files),
        },
        "missing_files": verification.missing_files,
        "mismatched_files": verification.mismatched_files,
        "unexpected_files": verification.unexpected_files,
    }


def format_mission_export_verification_json(
    package_path: Path,
    verification: MissionExportVerification,
) -> str:
    return json.dumps(
        mission_export_verification_payload(package_path, verification),
        indent=2,
        sort_keys=True,
    )


def format_mission_export_manifest_json(manifest: dict[str, object]) -> str:
    return json.dumps(manifest, indent=2, sort_keys=True)


def format_mission_export_manifest_markdown(manifest: dict[str, object]) -> str:
    archive_files = manifest.get("archive_files")
    archive_entries = archive_files if isinstance(archive_files, list) else []
    lines = [
        "# Mission Export Manifest",
        "",
        f"- Manifest version: `{manifest.get('manifest_version', 'unknown')}`",
        f"- Generated at: `{manifest.get('generated_at', 'unknown')}`",
        f"- Mission: `{manifest.get('mission_name', 'unknown')}`",
        f"- Mission id: `{manifest.get('mission_id', 'unknown')}`",
        f"- Client: `{manifest.get('client_name', 'unknown')}`",
        f"- Audit type: `{manifest.get('audit_type', 'unknown')}`",
        f"- Authorization decision: `{manifest.get('authorization_decision', 'unknown')}`",
        f"- Finding count: `{manifest.get('finding_count', 0)}`",
        f"- Report count: `{manifest.get('report_count', 0)}`",
        f"- Archive file count: `{manifest.get('archive_file_count', len(archive_entries))}`",
        "- Execution: `not_executed`",
        "",
        "## Package Members",
        "",
    ]
    if archive_entries:
        for entry in archive_entries:
            if isinstance(entry, dict):
                path = entry.get("path", "<unknown>")
                size_bytes = entry.get("size_bytes", "unknown")
                checksum = entry.get("sha256", "unknown")
                lines.append(f"- `{path}` ({size_bytes} bytes, sha256 `{checksum}`)")
    else:
        lines.append("No packaged files listed.")
    lines.append("")
    for title, key in (
        ("Reports", "reports"),
        ("Authorization Briefs", "authorization_briefs"),
        ("Scan Plans", "scan_plans"),
        ("Readiness Exports", "readiness_exports"),
    ):
        values = manifest.get(key)
        if isinstance(values, list) and values:
            lines.extend([f"## {title}", ""])
            lines.extend(f"- `{value}`" for value in values)
            lines.append("")
    return "\n".join(lines)


def format_mission_export_verification_markdown(
    package_path: Path,
    verification: MissionExportVerification,
) -> str:
    lines = [
        "# Mission Export Verification",
        "",
        f"- Package: `{package_path.name}`",
        f"- Status: `{verification.status}`",
        f"- Detail: {verification.detail}",
        f"- Checked files: `{verification.checked_files}`",
        f"- Missing files: `{len(verification.missing_files)}`",
        f"- Mismatched files: `{len(verification.mismatched_files)}`",
        f"- Unexpected files: `{len(verification.unexpected_files)}`",
        "- Execution: `not_executed`",
        "",
    ]
    issue_groups = [
        ("Missing Files", verification.missing_files),
        ("Mismatched Files", verification.mismatched_files),
        ("Unexpected Files", verification.unexpected_files),
    ]
    if any(files for _, files in issue_groups):
        for title, files in issue_groups:
            if files:
                lines.extend([f"## {title}", ""])
                lines.extend(f"- `{filename}`" for filename in files)
                lines.append("")
    else:
        lines.extend(["## Integrity Issues", "", "No integrity issues detected.", ""])
    return "\n".join(lines)


def format_mission_export_verification_text(
    package_path: Path,
    verification: MissionExportVerification,
) -> str:
    lines = [
        f"Mission export verification: {verification.status}",
        f"Package: {package_path}",
        f"Detail: {verification.detail}",
        f"Checked files: {verification.checked_files}",
        f"Missing files: {len(verification.missing_files)}",
        f"Mismatched files: {len(verification.mismatched_files)}",
        f"Unexpected files: {len(verification.unexpected_files)}",
        "Execution: not executed by this command",
    ]
    for label, files in (
        ("Missing file list", verification.missing_files),
        ("Mismatched file list", verification.mismatched_files),
        ("Unexpected file list", verification.unexpected_files),
    ):
        if files:
            lines.append(f"{label}:")
            lines.extend(f"- {name}" for name in files)
    return "\n".join(lines)


def mission_export_verification_exit_code(
    verification: MissionExportVerification,
    strict: bool = False,
) -> int:
    if verification.status == "failed":
        return 1
    if strict and verification.status != "ready":
        return 1
    return 0


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
