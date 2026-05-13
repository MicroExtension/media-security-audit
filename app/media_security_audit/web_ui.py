"""View models for the local web interface."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from html import escape
from pathlib import Path
from urllib.parse import urlencode

from media_security_audit.audit_templates import get_audit_template
from media_security_audit.models import (
    ActivityEvent,
    AuditCheck,
    Client,
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
from media_security_audit.remediation_library import RemediationEntry, filter_remediations
from media_security_audit.storage import JsonStore
from media_security_audit.web_readiness import (
    ReadinessItem,
    ScanPlanPreview,
    build_readiness_items,
    build_scan_plan_previews,
)
from media_security_audit.web_authorization import (
    AuthorizationBriefLink,
    list_authorization_briefs,
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
class ClientDetail:
    id: str
    name: str
    reference: str
    notes: str
    created_at: str


@dataclass(frozen=True)
class MissionRow:
    id: str
    name: str
    client_id: str
    client_name: str
    audit_type: str
    audit_template_id: str
    audit_template_title: str
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
    related_remediations: list[RemediationEntry]


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
class ClientActivityEventRow:
    id: str
    mission_id: str
    mission_name: str
    action: str
    summary: str
    created_at: str


@dataclass(frozen=True)
class ClientPreparationRow:
    mission_id: str
    mission_name: str
    status: str
    next_action: str
    authorization_status: str
    scope_status: str
    check_status: str
    warning_count: int
    blocked_count: int


@dataclass(frozen=True)
class DashboardPreparationRow:
    client_id: str
    client_name: str
    mission_id: str
    mission_name: str
    status: str
    next_action: str
    authorization_status: str
    scope_status: str
    check_status: str


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
    preparation_items: list[DashboardPreparationRow]
    total_clients: int
    total_missions: int
    total_findings: int
    high_or_critical_findings: int
    blocked_preparation_count: int
    warning_preparation_count: int
    ready_preparation_count: int


@dataclass(frozen=True)
class ClientView:
    client: ClientDetail
    missions: list[MissionRow]
    recent_activity_events: list[ClientActivityEventRow]
    preparation_items: list[ClientPreparationRow]
    activity_log_url: str
    blocked_preparation_count: int
    warning_preparation_count: int
    ready_preparation_count: int
    total_missions: int
    total_findings: int
    high_or_critical_findings: int
    approved_scope_count: int
    scope_count: int


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
    authorization_briefs: list[AuthorizationBriefLink]
    reports: list[GeneratedReportLink]
    mission_export: MissionExportLink | None
    readiness_items: list[ReadinessItem]
    scan_plans: list[ScanPlanPreview]
    template_guidance: TemplateGuidance | None


@dataclass(frozen=True)
class TemplateGuidance:
    id: str
    title: str
    summary: str
    cadence: str
    recommended_checks: list[str]
    scope_guidance: tuple[str, ...]
    authorization_requirements: tuple[str, ...]
    deliverables: tuple[str, ...]


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

PREPARATION_STATUS_RANK = {"blocked": 0, "warning": 1, "ready": 2}


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


def client_detail(client: Client) -> ClientDetail:
    return ClientDetail(
        id=client.id,
        name=client.name,
        reference=client.internal_reference or "",
        notes=client.notes or "",
        created_at=format_datetime(client.created_at),
    )


def mission_row(mission: Mission, findings: list[Finding], client_names: dict[str, str]) -> MissionRow:
    summary = build_report_summary(mission, findings)
    active_counts = summary["severity_counts"]
    approved_scope_count = len([item for item in mission.scope if item.approved and not item.excluded])
    audit_template = get_audit_template(mission.audit_template_id)

    return MissionRow(
        id=mission.id,
        name=mission.name,
        client_id=mission.client_id,
        client_name=client_names.get(mission.client_id, mission.client_id),
        audit_type=mission.audit_type.value,
        audit_template_id=mission.audit_template_id or "",
        audit_template_title=audit_template.title if audit_template else "",
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
        related_remediations=related_remediations(finding),
    )


def related_remediations(finding: Finding, limit: int = 3) -> list[RemediationEntry]:
    return filter_remediations(category=finding.category)[:limit]


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


def client_activity_event_row(event: ActivityEvent, mission: Mission) -> ClientActivityEventRow:
    return ClientActivityEventRow(
        id=event.id,
        mission_id=mission.id,
        mission_name=mission.name,
        action=event.action,
        summary=event.summary,
        created_at=format_datetime(event.created_at),
    )


def client_activity_log_url(client_id: str) -> str:
    return f"/activity?{urlencode({'client_id': client_id})}"


def client_preparation_row(mission: Mission, findings: list[Finding]) -> ClientPreparationRow:
    approved_scope_count = len(
        [item for item in mission.scope if item.approved and not item.excluded]
    )
    blocked_actions: list[str] = []
    warning_actions: list[str] = []

    if not mission.is_authorized:
        blocked_actions.append("Add written authorization reference.")
    if approved_scope_count == 0:
        blocked_actions.append("Approve at least one scope target.")
    if not mission.selected_checks:
        blocked_actions.append("Select audit checks for planning.")

    new_finding_count = len(
        [finding for finding in findings if finding.status == FindingStatus.NEW]
    )
    if new_finding_count:
        warning_actions.append(f"Review {new_finding_count} new finding(s).")

    if blocked_actions:
        status = "blocked"
        next_action = blocked_actions[0]
    elif warning_actions:
        status = "warning"
        next_action = warning_actions[0]
    else:
        status = "ready"
        next_action = "Ready for guarded CLI execution or reporting."

    return ClientPreparationRow(
        mission_id=mission.id,
        mission_name=mission.name,
        status=status,
        next_action=next_action,
        authorization_status="ready" if mission.is_authorized else "missing",
        scope_status="ready" if approved_scope_count else "missing",
        check_status="ready" if mission.selected_checks else "missing",
        warning_count=len(warning_actions),
        blocked_count=len(blocked_actions),
    )


def dashboard_preparation_row(
    mission: Mission,
    findings: list[Finding],
    client_names: dict[str, str],
) -> DashboardPreparationRow:
    preparation = client_preparation_row(mission, findings)
    return DashboardPreparationRow(
        client_id=mission.client_id,
        client_name=client_names.get(mission.client_id, mission.client_id),
        mission_id=preparation.mission_id,
        mission_name=preparation.mission_name,
        status=preparation.status,
        next_action=preparation.next_action,
        authorization_status=preparation.authorization_status,
        scope_status=preparation.scope_status,
        check_status=preparation.check_status,
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


def template_guidance(mission: Mission) -> TemplateGuidance | None:
    template = get_audit_template(mission.audit_template_id)
    if template is None:
        return None
    return TemplateGuidance(
        id=template.id,
        title=template.title,
        summary=template.summary,
        cadence=template.cadence,
        recommended_checks=[CHECK_LABELS[check] for check in template.recommended_checks],
        scope_guidance=template.scope_guidance,
        authorization_requirements=template.authorization_requirements,
        deliverables=template.deliverables,
    )


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
    preparation_rows: list[tuple[int, datetime, str, DashboardPreparationRow]] = []
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
        preparation = dashboard_preparation_row(mission, findings, client_names)
        preparation_rows.append(
            (
                PREPARATION_STATUS_RANK[preparation.status],
                mission.created_at,
                mission.id,
                preparation,
            )
        )

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
    preparation_rows.sort(key=lambda item: (item[0], item[1], item[2]))
    preparation_items = [row for _, _, _, row in preparation_rows]

    return DashboardView(
        clients=client_rows,
        missions=mission_rows,
        preparation_items=preparation_items,
        total_clients=len(client_rows),
        total_missions=len(mission_rows),
        total_findings=total_findings,
        high_or_critical_findings=high_or_critical,
        blocked_preparation_count=len(
            [item for item in preparation_items if item.status == "blocked"]
        ),
        warning_preparation_count=len(
            [item for item in preparation_items if item.status == "warning"]
        ),
        ready_preparation_count=len(
            [item for item in preparation_items if item.status == "ready"]
        ),
    )


def build_client_view(store: JsonStore, client_id: str) -> ClientView:
    client = store.get_client(client_id)
    client_names = {client.id: client.name}
    client_missions = [
        mission for mission in store.list_missions() if mission.client_id == client.id
    ]
    mission_rows: list[MissionRow] = []
    activity_rows: list[tuple[datetime, str, ClientActivityEventRow]] = []
    preparation_rows: list[tuple[int, datetime, str, ClientPreparationRow]] = []
    total_findings = 0
    high_or_critical = 0
    approved_scope_count = 0
    scope_count = 0

    for mission in client_missions:
        findings = store.list_findings(mission.id)
        total_findings += len(findings)
        high_or_critical += len(
            [finding for finding in findings if finding.severity.value in {"critical", "high"}]
        )
        approved_scope_count += len(
            [item for item in mission.scope if item.approved and not item.excluded]
        )
        scope_count += len(mission.scope)
        mission_rows.append(mission_row(mission, findings, client_names))
        for event in store.list_activity_events(mission.id):
            activity_rows.append(
                (event.created_at, event.id, client_activity_event_row(event, mission))
            )
        preparation = client_preparation_row(mission, findings)
        preparation_rows.append(
            (
                PREPARATION_STATUS_RANK[preparation.status],
                mission.created_at,
                mission.id,
                preparation,
            )
        )

    mission_rows.sort(key=lambda item: item.created_at, reverse=True)
    activity_rows.sort(key=lambda item: (item[0], item[1]), reverse=True)
    preparation_rows.sort(key=lambda item: (item[0], item[1], item[2]))
    preparation_items = [row for _, _, _, row in preparation_rows]

    return ClientView(
        client=client_detail(client),
        missions=mission_rows,
        recent_activity_events=[row for _, _, row in activity_rows[:10]],
        preparation_items=preparation_items,
        activity_log_url=client_activity_log_url(client.id),
        blocked_preparation_count=len(
            [item for item in preparation_items if item.status == "blocked"]
        ),
        warning_preparation_count=len(
            [item for item in preparation_items if item.status == "warning"]
        ),
        ready_preparation_count=len(
            [item for item in preparation_items if item.status == "ready"]
        ),
        total_missions=len(mission_rows),
        total_findings=total_findings,
        high_or_critical_findings=high_or_critical,
        approved_scope_count=approved_scope_count,
        scope_count=scope_count,
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
    authorization_briefs = list_authorization_briefs(mission_id, reports_dir) if reports_dir else []
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
        authorization_briefs=authorization_briefs,
        reports=reports,
        mission_export=mission_export,
        readiness_items=build_readiness_items(mission, findings, len(reports)),
        scan_plans=build_scan_plan_previews(mission),
        template_guidance=template_guidance(mission),
    )


def severity_class(value: str) -> str:
    allowed = {"critical", "high", "medium", "low", "info"}
    return value if value in allowed else "info"


def html_escape(value: object) -> str:
    return escape(str(value), quote=True)
