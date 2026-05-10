"""View models for the local web interface."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from html import escape
from pathlib import Path

from media_security_audit.models import (
    ActivityEvent,
    AuditCheck,
    Finding,
    FindingStatus,
    Mission,
    ScanRun,
    ScopeItem,
)
from media_security_audit.reports import (
    build_report_summary,
    remediation_plan,
    sorted_findings,
)
from media_security_audit.storage import JsonStore
from media_security_audit.web_readiness import (
    ReadinessItem,
    ScanPlanPreview,
    build_readiness_items,
    build_scan_plan_previews,
)
from media_security_audit.web_exports import MissionExportLink, list_mission_export
from media_security_audit.web_reports import GeneratedReportLink, list_generated_reports


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
    authorization_reference: str
    authorization_contact: str
    authorization_date: str
    authorization_expires_at: str
    emergency_contact: str
    report_recipients: str
    evidence_retention_days: str
    scope_count: int
    approved_scope_count: int
    finding_count: int
    risk_score: int
    risk_level: str
    severity_counts: dict[str, int]
    notes: str
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
class CounterTestRow:
    id: str
    title: str
    severity: str
    status: str
    affected_asset: str
    remediation: str
    counter_test: str


@dataclass(frozen=True)
class ActivityEventRow:
    id: str
    action: str
    summary: str
    created_at: str


@dataclass(frozen=True)
class CheckSelectionRow:
    value: str
    label: str
    description: str
    selected: bool


@dataclass(frozen=True)
class ScanRunRow:
    id: str
    check: str
    status: str
    started_at: str
    command_count: int
    finding_count: int
    evidence_count: int
    error: str


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
    counter_test_items: list[CounterTestRow]
    activity_events: list[ActivityEventRow]
    check_selection: list[CheckSelectionRow]
    scan_runs: list[ScanRunRow]
    remediation_items: list[dict[str, str]]
    executive_summary: str
    reports: list[GeneratedReportLink]
    mission_export: MissionExportLink | None
    readiness_items: list[ReadinessItem]
    scan_plans: list[ScanPlanPreview]


CHECK_LABELS: dict[AuditCheck, str] = {
    AuditCheck.NMAP: "Nmap services",
    AuditCheck.HTTP_HEADERS: "HTTP headers",
    AuditCheck.DNS_MAIL: "DNS/Mail",
}

CHECK_DESCRIPTIONS: dict[AuditCheck, str] = {
    AuditCheck.NMAP: "Conservative TCP service discovery on approved IP, host, domain, or CIDR scope.",
    AuditCheck.HTTP_HEADERS: "Browser security header review on approved URL scope.",
    AuditCheck.DNS_MAIL: "SPF, DMARC, and explicit DKIM TXT lookup plan on approved domain scope.",
}


def format_datetime(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M UTC")


def format_date(value: date | None) -> str:
    return value.isoformat() if value else ""


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
        authorization_reference=mission.authorization_reference or "",
        authorization_contact=mission.authorization_contact or "",
        authorization_date=format_date(mission.authorization_date),
        authorization_expires_at=format_date(mission.authorization_expires_at),
        emergency_contact=mission.emergency_contact or "",
        report_recipients=mission.report_recipients or "",
        evidence_retention_days=(
            str(mission.evidence_retention_days)
            if mission.evidence_retention_days is not None
            else ""
        ),
        scope_count=len(mission.scope),
        approved_scope_count=approved_scope_count,
        finding_count=len(findings),
        risk_score=int(summary["risk_score"]),
        risk_level=str(summary["risk_level"]),
        severity_counts=dict(active_counts),
        notes=mission.notes or "",
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


def counter_test_row(finding: Finding) -> CounterTestRow:
    return CounterTestRow(
        id=finding.id,
        title=finding.title,
        severity=finding.severity.value,
        status=finding.status.value,
        affected_asset=finding.affected_asset,
        remediation=finding.remediation,
        counter_test=finding.counter_test,
    )


def counter_test_findings(findings: list[Finding]) -> list[Finding]:
    actionable_statuses = {
        FindingStatus.CONFIRMED,
        FindingStatus.REMEDIATED,
        FindingStatus.COUNTER_TEST_FAILED,
    }
    return [finding for finding in sorted_findings(findings) if finding.status in actionable_statuses]


def activity_event_row(event: ActivityEvent) -> ActivityEventRow:
    return ActivityEventRow(
        id=event.id,
        action=event.action,
        summary=event.summary,
        created_at=format_datetime(event.created_at),
    )


def check_selection_rows(mission: Mission) -> list[CheckSelectionRow]:
    selected = set(mission.selected_checks)
    return [
        CheckSelectionRow(
            value=check.value,
            label=CHECK_LABELS[check],
            description=CHECK_DESCRIPTIONS[check],
            selected=check in selected,
        )
        for check in AuditCheck
    ]


def scan_run_row(run: ScanRun) -> ScanRunRow:
    return ScanRunRow(
        id=run.id,
        check=run.check.value,
        status=run.status.value,
        started_at=format_datetime(run.started_at),
        command_count=run.command_count,
        finding_count=run.finding_count,
        evidence_count=len(run.evidence_paths),
        error=run.error or "",
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


def build_mission_view(
    store: JsonStore,
    mission_id: str,
    reports_dir: Path | None = None,
) -> MissionView:
    mission = store.get_mission(mission_id)
    findings = store.list_findings(mission_id)
    activity_events = store.list_activity_events(mission_id)
    scan_runs = store.list_scan_runs(mission_id)
    summary = build_report_summary(mission, findings)
    reports = list_generated_reports(mission_id, reports_dir) if reports_dir else []
    mission_export = list_mission_export(mission_id, reports_dir) if reports_dir else None

    return MissionView(
        mission=mission_row(mission, findings, client_name_by_id(store)),
        scope=[scope_row(item) for item in mission.scope],
        findings=[finding_row(finding) for finding in sorted_findings(findings)],
        counter_test_items=[counter_test_row(finding) for finding in counter_test_findings(findings)],
        activity_events=[activity_event_row(event) for event in activity_events],
        check_selection=check_selection_rows(mission),
        scan_runs=[scan_run_row(run) for run in scan_runs],
        remediation_items=remediation_plan(findings),
        executive_summary=str(summary["executive_summary"]),
        reports=reports,
        mission_export=mission_export,
        readiness_items=build_readiness_items(mission, findings, len(reports)),
        scan_plans=build_scan_plan_previews(mission),
    )


def severity_class(value: str) -> str:
    allowed = {"critical", "high", "medium", "low", "info"}
    return value if value in allowed else "info"


def html_escape(value: object) -> str:
    return escape(str(value), quote=True)
