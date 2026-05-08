"""Read-only view models for the local web interface."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from html import escape

from media_security_audit.models import Finding, Mission, ScopeItem
from media_security_audit.reports import (
    build_report_summary,
    remediation_plan,
    sorted_findings,
)
from media_security_audit.storage import JsonStore


@dataclass(frozen=True)
class ClientRow:
    id: str
    name: str
    reference: str
    mission_count: int


@dataclass(frozen=True)
class MissionRow:
    id: str
    name: str
    client_id: str
    client_name: str
    audit_type: str
    status: str
    authorization_present: bool
    scope_count: int
    approved_scope_count: int
    finding_count: int
    risk_score: int
    risk_level: str
    severity_counts: dict[str, int]
    created_at: str


@dataclass(frozen=True)
class ScopeRow:
    id: str
    type: str
    value: str
    environment: str
    status: str
    notes: str


@dataclass(frozen=True)
class FindingRow:
    id: str
    title: str
    severity: str
    status: str
    affected_asset: str
    category: str
    source_module: str
    confidence: str
    proof: str
    risk: str
    remediation: str
    counter_test: str
    review_note: str


@dataclass(frozen=True)
class DashboardView:
    clients: list[ClientRow]
    missions: list[MissionRow]
    total_clients: int
    total_missions: int
    total_findings: int
    high_or_critical_findings: int


@dataclass(frozen=True)
class MissionView:
    mission: MissionRow
    scope: list[ScopeRow]
    findings: list[FindingRow]
    remediation_items: list[dict[str, str]]
    executive_summary: str


def format_datetime(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M UTC")


def scope_status(item: ScopeItem) -> str:
    if item.excluded:
        return "excluded"
    if item.approved:
        return "approved"
    return "draft"


def client_name_by_id(store: JsonStore) -> dict[str, str]:
    return {client.id: client.name for client in store.list_clients()}


def mission_row(mission: Mission, findings: list[Finding], client_names: dict[str, str]) -> MissionRow:
    summary = build_report_summary(mission, findings)
    active_counts = summary["severity_counts"]
    approved_scope_count = len([item for item in mission.scope if item.approved and not item.excluded])

    return MissionRow(
        id=mission.id,
        name=mission.name,
        client_id=mission.client_id,
        client_name=client_names.get(mission.client_id, mission.client_id),
        audit_type=mission.audit_type.value,
        status=mission.status.value,
        authorization_present=mission.is_authorized,
        scope_count=len(mission.scope),
        approved_scope_count=approved_scope_count,
        finding_count=len(findings),
        risk_score=int(summary["risk_score"]),
        risk_level=str(summary["risk_level"]),
        severity_counts=dict(active_counts),
        created_at=format_datetime(mission.created_at),
    )


def scope_row(item: ScopeItem) -> ScopeRow:
    return ScopeRow(
        id=item.id,
        type=item.type.value,
        value=item.value,
        environment=item.environment.value,
        status=scope_status(item),
        notes=item.notes or "",
    )


def finding_row(finding: Finding) -> FindingRow:
    return FindingRow(
        id=finding.id,
        title=finding.title,
        severity=finding.severity.value,
        status=finding.status.value,
        affected_asset=finding.affected_asset,
        category=finding.category,
        source_module=finding.source_module,
        confidence=f"{finding.confidence:.2f}",
        proof=finding.proof,
        risk=finding.risk,
        remediation=finding.remediation,
        counter_test=finding.counter_test,
        review_note=str(finding.metadata.get("review_note", "")),
    )


def build_dashboard_view(store: JsonStore) -> DashboardView:
    clients = store.list_clients()
    missions = store.list_missions()
    client_names = {client.id: client.name for client in clients}
    mission_counts = {client.id: 0 for client in clients}

    mission_rows: list[MissionRow] = []
    total_findings = 0
    high_or_critical = 0
    for mission in missions:
        mission_counts[mission.client_id] = mission_counts.get(mission.client_id, 0) + 1
        findings = store.list_findings(mission.id)
        total_findings += len(findings)
        high_or_critical += len(
            [finding for finding in findings if finding.severity.value in {"critical", "high"}]
        )
        mission_rows.append(mission_row(mission, findings, client_names))

    client_rows = [
        ClientRow(
            id=client.id,
            name=client.name,
            reference=client.internal_reference or "",
            mission_count=mission_counts.get(client.id, 0),
        )
        for client in clients
    ]

    mission_rows.sort(key=lambda item: item.created_at, reverse=True)

    return DashboardView(
        clients=client_rows,
        missions=mission_rows,
        total_clients=len(client_rows),
        total_missions=len(mission_rows),
        total_findings=total_findings,
        high_or_critical_findings=high_or_critical,
    )


def build_mission_view(store: JsonStore, mission_id: str) -> MissionView:
    mission = store.get_mission(mission_id)
    findings = store.list_findings(mission_id)
    summary = build_report_summary(mission, findings)

    return MissionView(
        mission=mission_row(mission, findings, client_name_by_id(store)),
        scope=[scope_row(item) for item in mission.scope],
        findings=[finding_row(finding) for finding in sorted_findings(findings)],
        remediation_items=remediation_plan(findings),
        executive_summary=str(summary["executive_summary"]),
    )


def severity_class(value: str) -> str:
    allowed = {"critical", "high", "medium", "low", "info"}
    return value if value in allowed else "info"


def html_escape(value: object) -> str:
    return escape(str(value), quote=True)
