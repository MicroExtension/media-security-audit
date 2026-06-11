"""View models for the local web interface."""

from __future__ import annotations

from collections import Counter
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
    Severity,
)
from media_security_audit.reports import (
    active_findings,
    build_report_summary,
    finding_status_counts,
    remediation_plan,
    risk_level,
    risk_score,
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
from media_security_audit.vulnerability_catalog import (
    CATALOG_FINDING_SOURCE,
    VulnerabilityMatch,
    correlate_vulnerability_catalog,
    load_vulnerability_catalog,
)


@dataclass(frozen=True)
class ClientRow:
    id: str
    name: str
    reference: str
    mission_count: int
    preparation_priority: str
    next_action: str
    next_action_label: str
    next_action_href: str
    export_inventory_url: str
    next_action_mission_id: str
    next_action_mission_name: str
    blocked_preparation_count: int
    warning_preparation_count: int
    ready_preparation_count: int
    new_finding_count: int
    accepted_risk_count: int
    false_positive_count: int
    active_finding_count: int
    high_or_critical_finding_count: int
    risk_score: int
    risk_level: str


@dataclass(frozen=True)
class ClientDetail:
    id: str
    name: str
    reference: str
    notes: str
    created_at: str


@dataclass(frozen=True)
class MissionPreparationSummary:
    status: str
    next_action: str
    next_action_label: str
    next_action_anchor: str
    authorization_status: str
    scope_status: str
    check_status: str
    warning_count: int
    blocked_count: int


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
    preparation_status: str
    preparation_next_action: str
    preparation_action_label: str
    preparation_action_href: str
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
    new_finding_count: int
    accepted_risk_count: int
    false_positive_count: int
    counter_test_ready_count: int
    counter_test_passed_count: int
    counter_test_failed_count: int
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
class FindingDispositionRow:
    status: str
    label: str
    count: int


@dataclass(frozen=True)
class CounterTestRow:
    id: str
    title: str
    severity: str
    status: str
    affected_asset: str
    remediation: str
    counter_test: str
    review_note: str


@dataclass(frozen=True)
class CounterTestSummaryRow:
    status: str
    label: str
    count: int
    detail: str


@dataclass(frozen=True)
class DashboardOnboardingStep:
    label: str
    status: str
    detail: str
    action_label: str
    action_href: str


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
    next_action_label: str
    next_action_href: str
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
    next_action_label: str
    next_action_href: str
    authorization_status: str
    scope_status: str
    check_status: str


@dataclass(frozen=True)
class ClientPrioritySummaryRow:
    status: str
    label: str
    count: int


@dataclass(frozen=True)
class ClientRiskSummaryRow:
    level: str
    label: str
    count: int


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
class MissionCockpitStep:
    label: str
    status: str
    detail: str
    action_label: str
    action_href: str


@dataclass(frozen=True)
class MissionCockpitService:
    value: str
    label: str
    status: str
    selected: bool
    detail: str
    run_status: str
    run_detail: str
    action_label: str
    action_href: str


@dataclass(frozen=True)
class MissionCockpit:
    status: str
    next_action: str
    next_action_label: str
    next_action_href: str
    ready_step_count: int
    total_step_count: int
    approved_scope_count: int
    selected_check_count: int
    ready_check_count: int
    blocked_check_count: int
    report_count: int
    handoff_status: str
    steps: list[MissionCockpitStep]
    services: list[MissionCockpitService]


@dataclass(frozen=True)
class ScanLaunchCenter:
    status: str
    detail: str
    action_label: str
    action_href: str
    ready_count: int
    blocked_count: int
    run_count: int
    ready_services: list[str]
    blocked_services: list[str]


@dataclass(frozen=True)
class MissionActionStep:
    number: int
    label: str
    status: str
    detail: str
    action_label: str
    action_href: str


@dataclass(frozen=True)
class DashboardView:
    clients: list[ClientRow]
    missions: list[MissionRow]
    preparation_items: list[DashboardPreparationRow]
    ready_missions: list[DashboardPreparationRow]
    review_missions: list[DashboardPreparationRow]
    blocked_missions: list[DashboardPreparationRow]
    client_priority_items: list[ClientPrioritySummaryRow]
    client_risk_items: list[ClientRiskSummaryRow]
    no_mission_clients: list[ClientRow]
    blocked_clients: list[ClientRow]
    top_risk_clients: list[ClientRow]
    review_backlog_clients: list[ClientRow]
    finding_dispositions: list[FindingDispositionRow]
    counter_test_summary: list[CounterTestSummaryRow]
    failed_counter_test_missions: list[MissionRow]
    onboarding_steps: list[DashboardOnboardingStep]
    onboarding_ready_count: int
    onboarding_total_count: int
    onboarding_next_action: str
    onboarding_next_action_label: str
    onboarding_next_action_href: str
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
    finding_dispositions: list[FindingDispositionRow]
    counter_test_summary: list[CounterTestSummaryRow]
    failed_counter_test_missions: list[MissionRow]
    activity_log_url: str
    export_inventory_url: str
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
    cockpit: MissionCockpit
    scan_launch: ScanLaunchCenter
    action_roadmap: list[MissionActionStep]
    activity_log_url: str
    scope: list[ScopeRow]
    findings: list[FindingRow]
    finding_dispositions: list[FindingDispositionRow]
    counter_test_summary: list[CounterTestSummaryRow]
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
    vulnerability_summary: VulnerabilitySummary
    vulnerability_catalog_count: int
    vulnerability_matches: list[VulnerabilityMatchRow]
    template_guidance: TemplateGuidance | None


@dataclass(frozen=True)
class VulnerabilitySummary:
    status: str
    detail: str
    action_label: str
    action_href: str
    catalog_count: int
    match_count: int
    known_exploited_count: int
    critical_or_high_count: int
    stored_candidate_count: int


@dataclass(frozen=True)
class VulnerabilityMatchRow:
    cve_id: str
    title: str
    severity: str
    known_exploited: bool
    affected_asset: str
    matched_finding_id: str
    matched_terms: str
    remediation: str


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
    AuditCheck.TLS: "TLS posture",
    AuditCheck.SMB: "SMB basic",
    AuditCheck.LDAP: "LDAP basic",
}

CHECK_DESCRIPTIONS: dict[AuditCheck, str] = {
    AuditCheck.NMAP: "Conservative TCP service discovery on approved IP, host, domain, or CIDR scope.",
    AuditCheck.HTTP_HEADERS: "Browser security header review on approved URL scope.",
    AuditCheck.DNS_MAIL: "SPF, DMARC, and explicit DKIM TXT lookup plan on approved domain scope.",
    AuditCheck.TLS: "testssl.sh TLS protocol, cipher, and certificate review on approved endpoints.",
    AuditCheck.SMB: "Anonymous SMB listing check on approved host, IP, or domain scope.",
    AuditCheck.LDAP: "Anonymous LDAP RootDSE metadata check on approved host, IP, or domain scope.",
}

PREPARATION_STATUS_RANK = {"blocked": 0, "warning": 1, "ready": 2}
CLIENT_PRIORITY_RANK = {"blocked": 0, "warning": 1, "ready": 2, "none": 3}
CLIENT_PRIORITY_LABELS = {
    "blocked": "Blocked",
    "warning": "Review",
    "ready": "Ready",
    "none": "No mission",
}
CLIENT_RISK_LABELS = {
    "critical": "Critical",
    "high": "High",
    "medium": "Medium",
    "low": "Low",
    "none": "None",
}

FINDING_DISPOSITION_LABELS = {
    "new": "New",
    "confirmed": "Confirmed",
    "false_positive": "False positive",
    "accepted_risk": "Accepted risk",
    "remediated": "Remediated",
    "counter_test_passed": "Counter-test passed",
    "counter_test_failed": "Counter-test failed",
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


def client_detail(client: Client) -> ClientDetail:
    return ClientDetail(
        id=client.id,
        name=client.name,
        reference=client.internal_reference or "",
        notes=client.notes or "",
        created_at=format_datetime(client.created_at),
    )


def mission_preparation_summary(
    mission: Mission,
    findings: list[Finding],
) -> MissionPreparationSummary:
    approved_scope_count = len(
        [item for item in mission.scope if item.approved and not item.excluded]
    )
    blocked_actions: list[str] = []
    warning_actions: list[tuple[str, str, str]] = []

    if not mission.is_authorized:
        blocked_actions.append("Add written authorization reference.")
    if approved_scope_count == 0:
        blocked_actions.append("Approve at least one scope target.")
    if not mission.selected_checks:
        blocked_actions.append("Select audit checks for planning.")

    failed_counter_test_count = len(
        [
            finding
            for finding in findings
            if finding.status == FindingStatus.COUNTER_TEST_FAILED
        ]
    )
    if failed_counter_test_count:
        warning_actions.append(
            (
                f"Review {failed_counter_test_count} failed counter-test(s).",
                "Open Counter-tests",
                "counter-test",
            )
        )

    new_finding_count = len(
        [finding for finding in findings if finding.status == FindingStatus.NEW]
    )
    if new_finding_count:
        warning_actions.append(
            (
                f"Review {new_finding_count} new finding(s).",
                "Review Findings",
                "findings",
            )
        )

    if blocked_actions:
        status = "blocked"
        next_action = blocked_actions[0]
        if not mission.is_authorized:
            next_action_label = "Open Setup"
            next_action_anchor = "mission-setup"
        elif approved_scope_count == 0:
            next_action_label = "Review Scope"
            next_action_anchor = "scope"
        else:
            next_action_label = "Select Checks"
            next_action_anchor = "check-selection"
    elif warning_actions:
        status = "warning"
        next_action, next_action_label, next_action_anchor = warning_actions[0]
    else:
        status = "ready"
        next_action = "Ready for guarded CLI execution or reporting."
        next_action_label = "Open Reports"
        next_action_anchor = "reports"

    return MissionPreparationSummary(
        status=status,
        next_action=next_action,
        next_action_label=next_action_label,
        next_action_anchor=next_action_anchor,
        authorization_status="ready" if mission.is_authorized else "missing",
        scope_status="ready" if approved_scope_count else "missing",
        check_status="ready" if mission.selected_checks else "missing",
        warning_count=len(warning_actions),
        blocked_count=len(blocked_actions),
    )


def mission_row(mission: Mission, findings: list[Finding], client_names: dict[str, str]) -> MissionRow:
    summary = build_report_summary(mission, findings)
    active_counts = summary["severity_counts"]
    status_counts = finding_status_counts(findings)
    approved_scope_count = len([item for item in mission.scope if item.approved and not item.excluded])
    audit_template = get_audit_template(mission.audit_template_id)
    preparation = mission_preparation_summary(mission, findings)

    return MissionRow(
        id=mission.id,
        name=mission.name,
        client_id=mission.client_id,
        client_name=client_names.get(mission.client_id, mission.client_id),
        audit_type=mission.audit_type.value,
        audit_template_id=mission.audit_template_id or "",
        audit_template_title=audit_template.title if audit_template else "",
        status=mission.status.value,
        preparation_status=preparation.status,
        preparation_next_action=preparation.next_action,
        preparation_action_label=preparation.next_action_label,
        preparation_action_href=f"/missions/{mission.id}#{preparation.next_action_anchor}",
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
        new_finding_count=status_counts["new"],
        accepted_risk_count=status_counts["accepted_risk"],
        false_positive_count=status_counts["false_positive"],
        counter_test_ready_count=len(counter_test_findings(findings)),
        counter_test_passed_count=status_counts["counter_test_passed"],
        counter_test_failed_count=status_counts["counter_test_failed"],
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


def finding_disposition_rows(findings: list[Finding]) -> list[FindingDispositionRow]:
    counts = finding_status_counts(findings)
    return [
        FindingDispositionRow(
            status=status,
            label=FINDING_DISPOSITION_LABELS[status],
            count=counts[status],
        )
        for status in FINDING_DISPOSITION_LABELS
    ]


def client_priority_summary_rows(
    clients: list[ClientRow],
) -> list[ClientPrioritySummaryRow]:
    counts = Counter(client.preparation_priority for client in clients)
    return [
        ClientPrioritySummaryRow(
            status=status,
            label=CLIENT_PRIORITY_LABELS[status],
            count=counts.get(status, 0),
        )
        for status in CLIENT_PRIORITY_LABELS
    ]


def client_risk_summary_rows(clients: list[ClientRow]) -> list[ClientRiskSummaryRow]:
    counts = Counter(client.risk_level for client in clients)
    return [
        ClientRiskSummaryRow(
            level=level,
            label=CLIENT_RISK_LABELS[level],
            count=counts.get(level, 0),
        )
        for level in CLIENT_RISK_LABELS
    ]


def ready_mission_rows(
    preparation_items: list[DashboardPreparationRow],
    limit: int = 5,
) -> list[DashboardPreparationRow]:
    return [item for item in preparation_items if item.status == "ready"][:limit]


def review_mission_rows(
    preparation_items: list[DashboardPreparationRow],
    limit: int = 5,
) -> list[DashboardPreparationRow]:
    return [item for item in preparation_items if item.status == "warning"][:limit]


def blocked_mission_rows(
    preparation_items: list[DashboardPreparationRow],
    limit: int = 5,
) -> list[DashboardPreparationRow]:
    return [item for item in preparation_items if item.status == "blocked"][:limit]


def no_mission_client_rows(
    clients: list[ClientRow],
    limit: int = 5,
) -> list[ClientRow]:
    no_mission_clients = [
        client for client in clients if client.preparation_priority == "none"
    ]
    return sorted(no_mission_clients, key=lambda client: client.name.lower())[:limit]


def blocked_client_rows(clients: list[ClientRow], limit: int = 5) -> list[ClientRow]:
    blocked_clients = [
        client for client in clients if client.preparation_priority == "blocked"
    ]
    return sorted(
        blocked_clients,
        key=lambda client: (
            -client.blocked_preparation_count,
            -client.risk_score,
            -client.new_finding_count,
            client.name.lower(),
        ),
    )[:limit]


def top_risk_client_rows(clients: list[ClientRow], limit: int = 5) -> list[ClientRow]:
    risky_clients = [client for client in clients if client.risk_score > 0]
    return sorted(
        risky_clients,
        key=lambda client: (
            -client.risk_score,
            -client.high_or_critical_finding_count,
            -client.active_finding_count,
            -client.new_finding_count,
            client.name.lower(),
        ),
    )[:limit]


def review_backlog_client_rows(
    clients: list[ClientRow],
    limit: int = 5,
) -> list[ClientRow]:
    review_clients = [client for client in clients if client.new_finding_count > 0]
    return sorted(
        review_clients,
        key=lambda client: (
            -client.new_finding_count,
            -client.risk_score,
            -client.high_or_critical_finding_count,
            -client.active_finding_count,
            client.name.lower(),
        ),
    )[:limit]


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
        review_note=str(finding.metadata.get("review_note", "")),
    )


def counter_test_findings(findings: list[Finding]) -> list[Finding]:
    actionable_statuses = {
        FindingStatus.CONFIRMED,
        FindingStatus.REMEDIATED,
        FindingStatus.COUNTER_TEST_FAILED,
    }
    return [finding for finding in sorted_findings(findings) if finding.status in actionable_statuses]


def counter_test_summary_rows(findings: list[Finding]) -> list[CounterTestSummaryRow]:
    status_counts = finding_status_counts(findings)
    return [
        CounterTestSummaryRow(
            status="ready",
            label="Ready",
            count=len(counter_test_findings(findings)),
            detail="Findings awaiting counter-test review.",
        ),
        CounterTestSummaryRow(
            status="passed",
            label="Passed",
            count=status_counts[FindingStatus.COUNTER_TEST_PASSED.value],
            detail="Findings validated as corrected.",
        ),
        CounterTestSummaryRow(
            status="failed",
            label="Failed",
            count=status_counts[FindingStatus.COUNTER_TEST_FAILED.value],
            detail="Findings still needing remediation.",
        ),
    ]


def failed_counter_test_mission_rows(missions: list[MissionRow]) -> list[MissionRow]:
    return sorted(
        [
            mission
            for mission in missions
            if mission.counter_test_failed_count > 0
        ],
        key=lambda mission: (
            -mission.counter_test_failed_count,
            -mission.risk_score,
            -mission.counter_test_ready_count,
            mission.client_name.lower(),
            mission.name.lower(),
        ),
    )


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


def client_export_inventory_url(client_id: str) -> str:
    return f"/exports?{urlencode({'client_id': client_id})}"


def mission_activity_log_url(mission_id: str) -> str:
    return f"/activity?{urlencode({'mission_id': mission_id})}"


def latest_mission(missions: list[Mission]) -> Mission | None:
    if not missions:
        return None
    return sorted(missions, key=lambda item: (item.created_at, item.id), reverse=True)[0]


def mission_anchor_href(mission: Mission | None, anchor: str) -> str:
    if mission is None:
        return "#new-mission"
    return f"/missions/{mission.id}#{anchor}"


def onboarding_step_status(is_ready: bool, is_enabled: bool) -> str:
    if is_ready:
        return "ready"
    return "warning" if is_enabled else "blocked"


def build_dashboard_onboarding_steps(
    clients: list[Client],
    missions: list[Mission],
    total_findings: int,
) -> list[DashboardOnboardingStep]:
    mission = latest_mission(missions)
    client_count = len(clients)
    mission_count = len(missions)
    authorized_mission_count = len([item for item in missions if item.is_authorized])
    approved_scope_count = len(
        [
            scope
            for item in missions
            for scope in item.scope
            if scope.approved and not scope.excluded
        ]
    )
    selected_check_count = sum(len(item.selected_checks) for item in missions)

    client_ready = client_count > 0
    mission_ready = mission_count > 0
    authorization_ready = authorized_mission_count > 0
    scope_ready = approved_scope_count > 0
    checks_ready = selected_check_count > 0 and scope_ready
    findings_ready = total_findings > 0 and checks_ready

    return [
        DashboardOnboardingStep(
            label="Client record",
            status=onboarding_step_status(client_ready, True),
            detail=(
                f"{client_count} client record(s) available."
                if client_ready
                else "Create the first maintenance client record."
            ),
            action_label="Review Clients" if client_ready else "Create Client",
            action_href="#clients" if client_ready else "#new-client",
        ),
        DashboardOnboardingStep(
            label="Mission setup",
            status=onboarding_step_status(mission_ready, client_ready),
            detail=(
                f"{mission_count} mission record(s) available."
                if mission_ready
                else "Create a mission attached to the pilot client."
            ),
            action_label="Review Missions" if mission_ready else "Create Mission",
            action_href="#missions" if mission_ready else "#new-mission",
        ),
        DashboardOnboardingStep(
            label="Authorization",
            status=onboarding_step_status(authorization_ready, mission_ready),
            detail=(
                f"{authorized_mission_count} authorized mission(s) available."
                if authorization_ready
                else "Record written authorization reference, contact, and dates."
            ),
            action_label="Review Setup",
            action_href=mission_anchor_href(mission, "mission-setup"),
        ),
        DashboardOnboardingStep(
            label="Approved scope",
            status=onboarding_step_status(scope_ready, authorization_ready),
            detail=(
                f"{approved_scope_count} approved target(s) available."
                if scope_ready
                else "Approve at least one in-scope target before planning checks."
            ),
            action_label="Review Scope",
            action_href=mission_anchor_href(mission, "scope"),
        ),
        DashboardOnboardingStep(
            label="Check selection",
            status=onboarding_step_status(checks_ready, scope_ready),
            detail=(
                f"{selected_check_count} selected check(s) available."
                if checks_ready
                else "Select audit checks aligned with the approved scope."
            ),
            action_label="Select Checks",
            action_href=mission_anchor_href(mission, "check-selection"),
        ),
        DashboardOnboardingStep(
            label="Finding review",
            status=onboarding_step_status(findings_ready, checks_ready),
            detail=(
                f"{total_findings} finding(s) ready for review."
                if findings_ready
                else "Add or import reviewed findings before report handoff."
            ),
            action_label="Review Findings",
            action_href=mission_anchor_href(mission, "findings"),
        ),
    ]


def onboarding_next_action(
    steps: list[DashboardOnboardingStep],
) -> tuple[str, str, str]:
    for step in steps:
        if step.status != "ready":
            return (step.detail, step.action_label, step.action_href)
    return ("Pilot workflow is ready for evidence handoff review.", "Open Pilot", "/pilot")


def client_preparation_row(mission: Mission, findings: list[Finding]) -> ClientPreparationRow:
    preparation = mission_preparation_summary(mission, findings)

    return ClientPreparationRow(
        mission_id=mission.id,
        mission_name=mission.name,
        status=preparation.status,
        next_action=preparation.next_action,
        next_action_label=preparation.next_action_label,
        next_action_href=f"/missions/{mission.id}#{preparation.next_action_anchor}",
        authorization_status=preparation.authorization_status,
        scope_status=preparation.scope_status,
        check_status=preparation.check_status,
        warning_count=preparation.warning_count,
        blocked_count=preparation.blocked_count,
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
        next_action_label=preparation.next_action_label,
        next_action_href=preparation.next_action_href,
        authorization_status=preparation.authorization_status,
        scope_status=preparation.scope_status,
        check_status=preparation.check_status,
    )


def client_priority_action(
    preparation_rows: list[tuple[int, datetime, str, DashboardPreparationRow]],
) -> tuple[str, str, str, str, str, str]:
    if not preparation_rows:
        return (
            "none",
            "Create first mission for this client.",
            "",
            "",
            "Create Mission",
            "#new-mission",
        )

    sorted_rows = sorted(preparation_rows, key=lambda item: (item[0], item[1], item[2]))
    preparation = sorted_rows[0][3]
    return (
        preparation.status,
        preparation.next_action,
        preparation.mission_id,
        preparation.mission_name,
        preparation.next_action_label,
        preparation.next_action_href,
    )


def client_priority_sort_key(
    client: ClientRow,
) -> tuple[int, int, int, int, int, int, int, int, str]:
    return (
        CLIENT_PRIORITY_RANK.get(client.preparation_priority, 99),
        -client.risk_score,
        -client.high_or_critical_finding_count,
        -client.active_finding_count,
        -client.new_finding_count,
        -client.blocked_preparation_count,
        -client.warning_preparation_count,
        -client.ready_preparation_count,
        client.name.lower(),
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


def mission_cockpit(
    mission: Mission,
    findings: list[Finding],
    readiness_items: list[ReadinessItem],
    scan_plans: list[ScanPlanPreview],
    check_selection: list[CheckSelectionRow],
    scan_runs: list[ScanRun],
    reports: list[GeneratedReportLink],
    mission_export: MissionExportLink | None,
) -> MissionCockpit:
    preparation = mission_preparation_summary(mission, findings)
    approved_scope_count = len(
        [item for item in mission.scope if item.approved and not item.excluded]
    )
    selected_check_count = len([item for item in check_selection if item.selected])
    ready_check_count = len([plan for plan in scan_plans if plan.status == "ready"])
    blocked_check_count = len([plan for plan in scan_plans if plan.status == "blocked"])
    readiness_ready_count = len([item for item in readiness_items if item.status == "ready"])
    handoff_status = (
        mission_export.handoff_status
        if mission_export is not None
        else ("warning" if reports else "missing")
    )

    return MissionCockpit(
        status=preparation.status,
        next_action=preparation.next_action,
        next_action_label=preparation.next_action_label,
        next_action_href=f"#{preparation.next_action_anchor}",
        ready_step_count=readiness_ready_count,
        total_step_count=len(readiness_items),
        approved_scope_count=approved_scope_count,
        selected_check_count=selected_check_count,
        ready_check_count=ready_check_count,
        blocked_check_count=blocked_check_count,
        report_count=len(reports),
        handoff_status=handoff_status,
        steps=mission_cockpit_steps(
            readiness_items=readiness_items,
            ready_check_count=ready_check_count,
            blocked_check_count=blocked_check_count,
            reports=reports,
            mission_export=mission_export,
        ),
        services=mission_cockpit_services(check_selection, scan_plans, scan_runs),
    )


def mission_cockpit_steps(
    readiness_items: list[ReadinessItem],
    ready_check_count: int,
    blocked_check_count: int,
    reports: list[GeneratedReportLink],
    mission_export: MissionExportLink | None,
) -> list[MissionCockpitStep]:
    readiness = {item.label: item for item in readiness_items}
    steps = [
        mission_cockpit_readiness_step(readiness["Authorization"], "Authorization"),
        mission_cockpit_readiness_step(readiness["Approved Scope"], "Périmètre"),
        mission_cockpit_readiness_step(readiness["Check Selection"], "Services"),
        MissionCockpitStep(
            label="Lancement",
            status="ready" if ready_check_count else "blocked",
            detail=(
                f"{ready_check_count} service(s) prêt(s), {blocked_check_count} bloqué(s)."
                if ready_check_count
                else "Aucun service sélectionné n’est prêt à être lancé."
            ),
            action_label="Open Scan Plan",
            action_href="#scan-plan",
        ),
        mission_cockpit_readiness_step(readiness["Finding Review"], "Constats"),
        mission_cockpit_handoff_step(reports, mission_export),
    ]
    return steps


def mission_cockpit_readiness_step(
    item: ReadinessItem,
    label: str,
) -> MissionCockpitStep:
    return MissionCockpitStep(
        label=label,
        status=item.status,
        detail=item.detail,
        action_label=item.action_label,
        action_href=item.action_href,
    )


def mission_cockpit_handoff_step(
    reports: list[GeneratedReportLink],
    mission_export: MissionExportLink | None,
) -> MissionCockpitStep:
    if mission_export is not None:
        return MissionCockpitStep(
            label="Livrables",
            status=mission_export.handoff_status,
            detail=mission_export.handoff_detail,
            action_label=mission_export.handoff_action,
            action_href="#reports",
        )
    if reports:
        return MissionCockpitStep(
            label="Livrables",
            status="warning",
            detail=f"{len(reports)} rapport(s) généré(s), package mission en attente.",
            action_label="Generate Package",
            action_href="#reports",
        )
    return MissionCockpitStep(
        label="Livrables",
        status="warning",
        detail="Rapports et package mission en attente.",
        action_label="Open Reports",
        action_href="#reports",
    )


def mission_cockpit_services(
    check_selection: list[CheckSelectionRow],
    scan_plans: list[ScanPlanPreview],
    scan_runs: list[ScanRun],
) -> list[MissionCockpitService]:
    plans_by_check = {plan.check: plan for plan in scan_plans}
    latest_runs = latest_scan_runs_by_check(scan_runs)
    services: list[MissionCockpitService] = []
    for check in check_selection:
        plan = plans_by_check.get(check.value)
        run_status, run_detail = cockpit_service_run_summary(latest_runs.get(check.value))
        if not check.selected:
            services.append(
                MissionCockpitService(
                    value=check.value,
                    label=check.label,
                    status="none",
                    selected=False,
                    detail="Non sélectionné pour cette mission.",
                    run_status=run_status,
                    run_detail=run_detail,
                    action_label="Select",
                    action_href="#check-selection",
                )
            )
            continue
        if plan is None:
            services.append(
                MissionCockpitService(
                    value=check.value,
                    label=check.label,
                    status="warning",
                    selected=True,
                    detail="Sélectionné, plan non disponible.",
                    run_status=run_status,
                    run_detail=run_detail,
                    action_label="Review",
                    action_href="#check-selection",
                )
            )
            continue
        services.append(
            MissionCockpitService(
                value=check.value,
                label=check.label,
                status=plan.status,
                selected=True,
                detail=plan.detail,
                run_status=run_status,
                run_detail=run_detail,
                action_label="Run" if plan.status == "ready" else "Resolve",
                action_href="#scan-plan" if plan.status == "ready" else "#scope",
            )
        )
    return services


def latest_scan_runs_by_check(scan_runs: list[ScanRun]) -> dict[str, ScanRun]:
    latest: dict[str, ScanRun] = {}
    for run in sorted(scan_runs, key=lambda item: item.started_at, reverse=True):
        latest.setdefault(run.check.value, run)
    return latest


def cockpit_service_run_summary(run: ScanRun | None) -> tuple[str, str]:
    if run is None:
        return "none", "Aucun lancement enregistré."
    detail = (
        f"Dernier lancement {format_datetime(run.started_at)} : "
        f"{run.command_count} commande(s), "
        f"{run.finding_count} constat(s), "
        f"{len(run.evidence_paths)} preuve(s)."
    )
    if run.error:
        detail = f"{detail} Erreur : {run.error}"
    return run.status.value, detail


def scan_launch_center(
    scan_plans: list[ScanPlanPreview],
    scan_runs: list[ScanRun],
) -> ScanLaunchCenter:
    ready_services = [plan.label for plan in scan_plans if plan.status == "ready"]
    blocked_services = [plan.label for plan in scan_plans if plan.status == "blocked"]
    if ready_services:
        status = "ready"
        detail = (
            f"{len(ready_services)} service(s) prêt(s) pour lancement contrôlé, "
            f"{len(blocked_services)} bloqué(s)."
        )
        action_label = "Open Ready Checks"
        action_href = "#scan-plan"
    elif scan_plans:
        status = "blocked"
        detail = "Tous les services sélectionnés sont bloqués par la préparation mission."
        action_label = "Review Readiness"
        action_href = "#mission-readiness"
    else:
        status = "missing"
        detail = "Aucun service n’est sélectionné pour cette mission."
        action_label = "Select Checks"
        action_href = "#check-selection"
    return ScanLaunchCenter(
        status=status,
        detail=detail,
        action_label=action_label,
        action_href=action_href,
        ready_count=len(ready_services),
        blocked_count=len(blocked_services),
        run_count=len(scan_runs),
        ready_services=ready_services,
        blocked_services=blocked_services,
    )


def mission_action_roadmap(
    mission: Mission,
    scan_plans: list[ScanPlanPreview],
    scan_runs: list[ScanRun],
    reports: list[GeneratedReportLink],
    mission_export: MissionExportLink | None,
    vulnerability: VulnerabilitySummary,
) -> list[MissionActionStep]:
    approved_scope_count = len(
        [item for item in mission.scope if item.approved and not item.excluded]
    )
    selected_check_count = len(mission.selected_checks)
    ready_check_count = len([plan for plan in scan_plans if plan.status == "ready"])
    blocked_check_count = len([plan for plan in scan_plans if plan.status == "blocked"])

    if mission.is_authorized:
        authorization_step = MissionActionStep(
            number=1,
            label="Authorization",
            status="ready",
            detail="Written authorization is recorded for this mission.",
            action_label="Review Setup",
            action_href="#mission-setup",
        )
    else:
        authorization_step = MissionActionStep(
            number=1,
            label="Authorization",
            status="blocked",
            detail="Add the authorization reference before guarded execution.",
            action_label="Open Setup",
            action_href="#mission-setup",
        )

    if approved_scope_count and selected_check_count:
        scope_step = MissionActionStep(
            number=2,
            label="Targets and services",
            status="ready",
            detail=(
                f"{approved_scope_count} approved target(s), "
                f"{selected_check_count} selected service(s)."
            ),
            action_label="Review Scope",
            action_href="#scope",
        )
    elif approved_scope_count:
        scope_step = MissionActionStep(
            number=2,
            label="Targets and services",
            status="blocked",
            detail="Approved scope is present, but no service is selected.",
            action_label="Select Services",
            action_href="#check-selection",
        )
    else:
        scope_step = MissionActionStep(
            number=2,
            label="Targets and services",
            status="blocked",
            detail="Approve at least one target and select services to test.",
            action_label="Review Scope",
            action_href="#scope",
        )

    if ready_check_count and scan_runs:
        launch_step = MissionActionStep(
            number=3,
            label="Guarded launch",
            status="ready",
            detail=(
                f"{ready_check_count} service(s) ready, "
                f"{blocked_check_count} blocked, {len(scan_runs)} run(s) recorded."
            ),
            action_label="Open Runs",
            action_href="#run-monitor",
        )
    elif ready_check_count:
        launch_step = MissionActionStep(
            number=3,
            label="Guarded launch",
            status="warning",
            detail=(
                f"{ready_check_count} service(s) ready, "
                f"{blocked_check_count} blocked, no run recorded yet."
            ),
            action_label="Open Scan Plan",
            action_href="#scan-plan",
        )
    else:
        launch_step = MissionActionStep(
            number=3,
            label="Guarded launch",
            status="blocked",
            detail="No selected service is ready for execution.",
            action_label="Open Scan Plan",
            action_href="#scan-plan",
        )

    vulnerability_step = MissionActionStep(
        number=4,
        label="CVE/KEV review",
        status=vulnerability.status,
        detail=vulnerability.detail,
        action_label=vulnerability.action_label,
        action_href=vulnerability.action_href,
    )

    if mission_export is not None:
        handoff_step = MissionActionStep(
            number=5,
            label="Reports and handoff",
            status=mission_export.handoff_status,
            detail=mission_export.handoff_detail,
            action_label=mission_export.handoff_action,
            action_href="#reports",
        )
    elif reports:
        handoff_step = MissionActionStep(
            number=5,
            label="Reports and handoff",
            status="warning",
            detail=f"{len(reports)} report file(s) generated; mission package is pending.",
            action_label="Generate Package",
            action_href="#reports",
        )
    else:
        handoff_step = MissionActionStep(
            number=5,
            label="Reports and handoff",
            status="blocked",
            detail="Generate reviewed reports before customer handoff.",
            action_label="Open Reports",
            action_href="#reports",
        )

    return [
        authorization_step,
        scope_step,
        launch_step,
        vulnerability_step,
        handoff_step,
    ]


def build_dashboard_view(store: JsonStore) -> DashboardView:
    clients = store.list_clients()
    missions = store.list_missions()
    client_names = {client.id: client.name for client in clients}
    mission_counts = {client.id: 0 for client in clients}
    preparation_counts = {
        client.id: {"blocked": 0, "warning": 0, "ready": 0}
        for client in clients
    }
    client_review_counts = {
        client.id: {"new": 0, "accepted_risk": 0, "false_positive": 0}
        for client in clients
    }
    client_findings: dict[str, list[Finding]] = {client.id: [] for client in clients}

    mission_rows: list[MissionRow] = []
    preparation_rows: list[tuple[int, datetime, str, DashboardPreparationRow]] = []
    preparation_rows_by_client: dict[
        str,
        list[tuple[int, datetime, str, DashboardPreparationRow]],
    ] = {}
    all_findings: list[Finding] = []
    total_findings = 0
    high_or_critical = 0
    for mission in missions:
        mission_counts[mission.client_id] = mission_counts.get(mission.client_id, 0) + 1
        findings = store.list_findings(mission.id)
        disposition_counts = finding_status_counts(findings)
        client_findings.setdefault(mission.client_id, []).extend(findings)
        review_counts = client_review_counts.setdefault(
            mission.client_id,
            {"new": 0, "accepted_risk": 0, "false_positive": 0},
        )
        review_counts["new"] += disposition_counts["new"]
        review_counts["accepted_risk"] += disposition_counts["accepted_risk"]
        review_counts["false_positive"] += disposition_counts["false_positive"]
        all_findings.extend(findings)
        total_findings += len(findings)
        high_or_critical += len(
            [finding for finding in findings if finding.severity.value in {"critical", "high"}]
        )
        mission_rows.append(mission_row(mission, findings, client_names))
        preparation = dashboard_preparation_row(mission, findings, client_names)
        preparation_counts.setdefault(
            mission.client_id,
            {"blocked": 0, "warning": 0, "ready": 0},
        )[preparation.status] += 1
        preparation_tuple = (
            PREPARATION_STATUS_RANK[preparation.status],
            mission.created_at,
            mission.id,
            preparation,
        )
        preparation_rows.append(preparation_tuple)
        preparation_rows_by_client.setdefault(mission.client_id, []).append(preparation_tuple)

    client_rows: list[ClientRow] = []
    for client in clients:
        (
            priority,
            next_action,
            mission_id,
            mission_name,
            next_action_label,
            next_action_href,
        ) = client_priority_action(
            preparation_rows_by_client.get(client.id, [])
        )
        findings = client_findings.get(client.id, [])
        active_client_findings = active_findings(findings)
        client_risk_score = risk_score(findings)
        client_rows.append(
            ClientRow(
                id=client.id,
                name=client.name,
                reference=client.internal_reference or "",
                mission_count=mission_counts.get(client.id, 0),
                preparation_priority=priority,
                next_action=next_action,
                next_action_label=next_action_label,
                next_action_href=next_action_href,
                export_inventory_url=client_export_inventory_url(client.id),
                next_action_mission_id=mission_id,
                next_action_mission_name=mission_name,
                blocked_preparation_count=preparation_counts.get(client.id, {}).get(
                    "blocked",
                    0,
                ),
                warning_preparation_count=preparation_counts.get(client.id, {}).get(
                    "warning",
                    0,
                ),
                ready_preparation_count=preparation_counts.get(client.id, {}).get(
                    "ready",
                    0,
                ),
                new_finding_count=client_review_counts.get(client.id, {}).get("new", 0),
                accepted_risk_count=client_review_counts.get(client.id, {}).get(
                    "accepted_risk",
                    0,
                ),
                false_positive_count=client_review_counts.get(client.id, {}).get(
                    "false_positive",
                    0,
                ),
                active_finding_count=len(active_client_findings),
                high_or_critical_finding_count=len(
                    [
                        finding
                        for finding in active_client_findings
                        if finding.severity.value in {"critical", "high"}
                    ]
                ),
                risk_score=client_risk_score,
                risk_level=risk_level(client_risk_score),
            )
        )
    client_rows.sort(key=client_priority_sort_key)

    mission_rows.sort(key=lambda item: item.created_at, reverse=True)
    preparation_rows.sort(key=lambda item: (item[0], item[1], item[2]))
    preparation_items = [row for _, _, _, row in preparation_rows]
    onboarding_steps = build_dashboard_onboarding_steps(
        clients=clients,
        missions=missions,
        total_findings=total_findings,
    )
    (
        onboarding_next_action_text,
        onboarding_next_action_label,
        onboarding_next_action_href,
    ) = onboarding_next_action(onboarding_steps)

    return DashboardView(
        clients=client_rows,
        missions=mission_rows,
        preparation_items=preparation_items,
        ready_missions=ready_mission_rows(preparation_items),
        review_missions=review_mission_rows(preparation_items),
        blocked_missions=blocked_mission_rows(preparation_items),
        client_priority_items=client_priority_summary_rows(client_rows),
        client_risk_items=client_risk_summary_rows(client_rows),
        no_mission_clients=no_mission_client_rows(client_rows),
        blocked_clients=blocked_client_rows(client_rows),
        top_risk_clients=top_risk_client_rows(client_rows),
        review_backlog_clients=review_backlog_client_rows(client_rows),
        finding_dispositions=finding_disposition_rows(all_findings),
        counter_test_summary=counter_test_summary_rows(all_findings),
        failed_counter_test_missions=failed_counter_test_mission_rows(mission_rows),
        onboarding_steps=onboarding_steps,
        onboarding_ready_count=len(
            [item for item in onboarding_steps if item.status == "ready"]
        ),
        onboarding_total_count=len(onboarding_steps),
        onboarding_next_action=onboarding_next_action_text,
        onboarding_next_action_label=onboarding_next_action_label,
        onboarding_next_action_href=onboarding_next_action_href,
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
    all_findings: list[Finding] = []

    for mission in client_missions:
        findings = store.list_findings(mission.id)
        all_findings.extend(findings)
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
        finding_dispositions=finding_disposition_rows(all_findings),
        counter_test_summary=counter_test_summary_rows(all_findings),
        failed_counter_test_missions=failed_counter_test_mission_rows(mission_rows),
        activity_log_url=client_activity_log_url(client.id),
        export_inventory_url=client_export_inventory_url(client.id),
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
    vulnerability_catalog = load_vulnerability_catalog(store.data_dir)
    vulnerability_matches = correlate_vulnerability_catalog(mission_id, store.data_dir)
    authorization_briefs = list_authorization_briefs(mission_id, reports_dir) if reports_dir else []
    reports = list_generated_reports(mission_id, reports_dir) if reports_dir else []
    mission_export = list_mission_export(mission_id, reports_dir) if reports_dir else None
    check_selection = check_selection_rows(mission)
    scan_plans = build_scan_plan_previews(mission)
    readiness_items = build_readiness_items(mission, findings, len(reports))
    vulnerability = vulnerability_summary(
        catalog_count=len(vulnerability_catalog.advisories),
        matches=vulnerability_matches,
        findings=findings,
    )

    return MissionView(
        mission=mission_row(mission, findings, client_name_by_id(store)),
        cockpit=mission_cockpit(
            mission=mission,
            findings=findings,
            readiness_items=readiness_items,
            scan_plans=scan_plans,
            check_selection=check_selection,
            scan_runs=scan_runs,
            reports=reports,
            mission_export=mission_export,
        ),
        scan_launch=scan_launch_center(scan_plans, scan_runs),
        action_roadmap=mission_action_roadmap(
            mission=mission,
            scan_plans=scan_plans,
            scan_runs=scan_runs,
            reports=reports,
            mission_export=mission_export,
            vulnerability=vulnerability,
        ),
        activity_log_url=mission_activity_log_url(mission.id),
        scope=[scope_row(item) for item in mission.scope],
        findings=[finding_row(finding) for finding in sorted_findings(findings)],
        finding_dispositions=finding_disposition_rows(findings),
        counter_test_summary=counter_test_summary_rows(findings),
        counter_test_items=[counter_test_row(finding) for finding in counter_test_findings(findings)],
        activity_events=[activity_event_row(event) for event in activity_events],
        check_selection=check_selection,
        scan_runs=[scan_run_row(run) for run in scan_runs],
        remediation_items=remediation_plan(findings),
        executive_summary=str(summary["executive_summary"]),
        authorization_briefs=authorization_briefs,
        reports=reports,
        mission_export=mission_export,
        readiness_items=readiness_items,
        scan_plans=scan_plans,
        vulnerability_summary=vulnerability,
        vulnerability_catalog_count=len(vulnerability_catalog.advisories),
        vulnerability_matches=[
            vulnerability_match_row(match) for match in vulnerability_matches
        ],
        template_guidance=template_guidance(mission),
    )


def severity_class(value: str) -> str:
    allowed = {"critical", "high", "medium", "low", "info"}
    return value if value in allowed else "info"


def vulnerability_match_row(match: VulnerabilityMatch) -> VulnerabilityMatchRow:
    return VulnerabilityMatchRow(
        cve_id=match.advisory.cve_id,
        title=match.advisory.title,
        severity=match.advisory.severity.value,
        known_exploited=match.advisory.known_exploited,
        affected_asset=match.finding.affected_asset,
        matched_finding_id=match.finding.id,
        matched_terms=", ".join(match.matched_terms),
        remediation=match.advisory.remediation,
    )


def vulnerability_summary(
    catalog_count: int,
    matches: list[VulnerabilityMatch],
    findings: list[Finding],
) -> VulnerabilitySummary:
    stored_candidate_count = len(
        [finding for finding in findings if finding.source_module == CATALOG_FINDING_SOURCE]
    )
    known_exploited_count = len([match for match in matches if match.advisory.known_exploited])
    critical_or_high_count = len(
        [
            match
            for match in matches
            if match.advisory.severity in {Severity.CRITICAL, Severity.HIGH}
        ]
    )

    if catalog_count == 0:
        return VulnerabilitySummary(
            status="missing",
            detail="Aucun catalogue CVE/KEV local n’est importé.",
            action_label="Import Catalog",
            action_href="#vulnerabilities",
            catalog_count=0,
            match_count=0,
            known_exploited_count=0,
            critical_or_high_count=0,
            stored_candidate_count=stored_candidate_count,
        )

    if not matches:
        return VulnerabilitySummary(
            status="ready",
            detail="Catalogue importé, aucune correspondance candidate pour cette mission.",
            action_label="Review Findings",
            action_href="#findings",
            catalog_count=catalog_count,
            match_count=0,
            known_exploited_count=0,
            critical_or_high_count=0,
            stored_candidate_count=stored_candidate_count,
        )

    if stored_candidate_count >= len(matches):
        status = "ready"
        detail = (
            f"{len(matches)} correspondance(s) candidate(s), "
            f"{known_exploited_count} KEV, {critical_or_high_count} critique(s)/élevée(s), "
            "déjà stockée(s) comme constats."
        )
        action_label = "Review Findings"
        action_href = "#findings"
    else:
        status = "warning"
        detail = (
            f"{len(matches)} correspondance(s) candidate(s), "
            f"{known_exploited_count} KEV, {critical_or_high_count} critique(s)/élevée(s), "
            f"{stored_candidate_count} déjà stockée(s)."
        )
        action_label = "Store Candidate Findings"
        action_href = "#vulnerabilities"

    return VulnerabilitySummary(
        status=status,
        detail=detail,
        action_label=action_label,
        action_href=action_href,
        catalog_count=catalog_count,
        match_count=len(matches),
        known_exploited_count=known_exploited_count,
        critical_or_high_count=critical_or_high_count,
        stored_candidate_count=stored_candidate_count,
    )


def html_escape(value: object) -> str:
    return escape(str(value), quote=True)
