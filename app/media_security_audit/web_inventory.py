"""Workspace inventory and integrity checks for appliance operations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from media_security_audit.models import ActivityEvent, Client, Finding, Mission, ScanRun
from media_security_audit.storage import JsonStore
from media_security_audit.web_authorization import list_authorization_briefs
from media_security_audit.web_exports import list_mission_export
from media_security_audit.web_reports import list_generated_reports

ModelT = TypeVar("ModelT", bound=BaseModel)


@dataclass(frozen=True)
class InventoryMetric:
    label: str
    value: int


@dataclass(frozen=True)
class InventoryIssue:
    status: str
    label: str
    detail: str


@dataclass(frozen=True)
class WorkspaceInventory:
    status: str
    metrics: list[InventoryMetric]
    issues: list[InventoryIssue]


def build_workspace_inventory(store: JsonStore, reports_dir: Path) -> WorkspaceInventory:
    clients = read_models(store.clients_dir, Client)
    missions = read_models(store.missions_dir, Mission)
    client_ids = {client.id for client in clients}
    mission_ids = {mission.id for mission in missions}

    findings_count = sum(
        len(read_models(store.findings_dir / mission.id, Finding)) for mission in missions
    )
    activity_count = sum(
        len(read_models(store.events_dir / mission.id, ActivityEvent)) for mission in missions
    )
    run_count = sum(
        len(read_models(store.runs_dir / mission.id, ScanRun)) for mission in missions
    )
    generated_report_count = sum(
        len(list_generated_reports(mission.id, reports_dir)) for mission in missions
    )
    authorization_brief_count = sum(
        len(list_authorization_briefs(mission.id, reports_dir)) for mission in missions
    )
    mission_export_count = len(
        [
            mission
            for mission in missions
            if list_mission_export(mission.id, reports_dir) is not None
        ]
    )
    ready_mission_count = len(
        [mission for mission in missions if mission.status.value == "ready_to_scan"]
    )

    issues = workspace_issues(store, reports_dir, client_ids, mission_ids, missions)

    return WorkspaceInventory(
        status=inventory_status(issues),
        metrics=[
            InventoryMetric("Clients", len(clients)),
            InventoryMetric("Missions", len(missions)),
            InventoryMetric("Ready missions", ready_mission_count),
            InventoryMetric("Findings", findings_count),
            InventoryMetric("Activity events", activity_count),
            InventoryMetric("Scan runs", run_count),
            InventoryMetric("Generated reports", generated_report_count),
            InventoryMetric("Authorization briefs", authorization_brief_count),
            InventoryMetric("Mission exports", mission_export_count),
        ],
        issues=issues or [
            InventoryIssue(
                status="ready",
                label="Workspace integrity",
                detail="No orphaned mission data or missing client references detected.",
            )
        ],
    )


def inventory_status(issues: list[InventoryIssue]) -> str:
    if any(issue.status == "blocked" for issue in issues):
        return "blocked"
    if any(issue.status == "warning" for issue in issues):
        return "warning"
    return "ready"


def workspace_issues(
    store: JsonStore,
    reports_dir: Path,
    client_ids: set[str],
    mission_ids: set[str],
    missions: list[Mission],
) -> list[InventoryIssue]:
    issues: list[InventoryIssue] = []
    missing_client_missions = [
        mission for mission in missions if mission.client_id not in client_ids
    ]
    if missing_client_missions:
        issues.append(
            InventoryIssue(
                status="blocked",
                label="Missing client references",
                detail=", ".join(mission.id for mission in missing_client_missions),
            )
        )

    for label, directory in (
        ("Orphan finding folders", store.findings_dir),
        ("Orphan activity folders", store.events_dir),
        ("Orphan scan run folders", store.runs_dir),
    ):
        orphan_names = orphan_directory_names(directory, mission_ids)
        if orphan_names:
            issues.append(
                InventoryIssue(
                    status="warning",
                    label=label,
                    detail=", ".join(orphan_names),
                )
            )

    orphan_reports = orphan_report_directory_names(reports_dir, mission_ids)
    if orphan_reports:
        issues.append(
            InventoryIssue(
                status="warning",
                label="Orphan report folders",
                detail=", ".join(orphan_reports),
            )
        )

    return issues


def read_models(directory: Path, model_type: type[ModelT]) -> list[ModelT]:
    if not directory.exists() or not directory.is_dir():
        return []
    return sorted(
        (
            model_type.model_validate_json(path.read_text(encoding="utf-8"))
            for path in directory.glob("*.json")
        ),
        key=lambda item: getattr(item, "created_at", ""),
    )


def orphan_directory_names(directory: Path, mission_ids: set[str]) -> list[str]:
    if not directory.exists() or not directory.is_dir():
        return []
    return sorted(
        path.name
        for path in directory.iterdir()
        if path.is_dir() and path.name not in mission_ids
    )


def orphan_report_directory_names(reports_dir: Path, mission_ids: set[str]) -> list[str]:
    if not reports_dir.exists() or not reports_dir.is_dir():
        return []
    return sorted(
        path.name
        for path in reports_dir.iterdir()
        if path.is_dir()
        and path.name not in mission_ids
        and path.name != "_workspace-backups"
    )
