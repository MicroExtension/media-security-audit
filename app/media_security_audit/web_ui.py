"""View models for the local web interface."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from html import escape
from pathlib import Path
from urllib.parse import urlencode

from media_security_audit.audit_templates import get_audit_template
from media_security_audit.check_requirements import (
    CHECK_SCOPE_REQUIREMENTS,
    CHECK_SCOPE_TYPES,
)
from media_security_audit.models import (
    ActivityEvent,
    AuditCheck,
    Client,
    Finding,
    FindingStatus,
    Mission,
    ReportFormat,
    ScanRun,
    ScanRunStatus,
    ScopeType,
    ScopeItem,
    Severity,
)
from media_security_audit.reports import (
    MISSION_REPORT_FORMATS,
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
class ScopeIntakeItem:
    label: str
    scope_type: str
    status: str
    detail: str
    example: str
    matching_scope_count: int
    services: list[str]
    action_label: str
    action_href: str


@dataclass(frozen=True)
class ScopeIntakeSummary:
    status: str
    detail: str
    action_label: str
    action_href: str
    approved_count: int
    draft_count: int
    excluded_count: int
    items: list[ScopeIntakeItem]


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
    target_status: str
    target_requirement: str
    target_summary: str
    matching_scope_count: int


@dataclass(frozen=True)
class ScanRunRow:
    id: str
    check: str
    label: str
    status: str
    status_title: str
    started_at: str
    command_count: int
    finding_count: int
    evidence_count: int
    evidence_summary: str
    summary: str
    action_label: str
    action_href: str
    error: str


@dataclass(frozen=True)
class ScanRunOutcomeSummary:
    status: str
    title: str
    detail: str
    action_label: str
    action_href: str
    run_count: int
    finding_count: int
    evidence_count: int


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
class AnalysisSessionStep:
    label: str
    status: str
    detail: str
    weight: int
    earned: int
    action_label: str
    action_href: str


@dataclass(frozen=True)
class AnalysisSessionWorkflowLane:
    label: str
    status: str
    detail: str
    primary_label: str
    primary_value: str
    secondary_label: str
    secondary_value: str
    action_label: str
    action_href: str


@dataclass(frozen=True)
class AnalysisSessionResultShortcut:
    label: str
    category: str
    status: str
    count: str
    detail: str
    action_label: str
    action_href: str


@dataclass(frozen=True)
class AnalysisSessionTimelineItem:
    label: str
    status: str
    timestamp: str
    detail: str
    action_label: str
    action_href: str


@dataclass(frozen=True)
class AnalysisSessionRemediationPriority:
    title: str
    severity: str
    status: str
    asset: str
    risk: str
    remediation: str
    counter_test: str
    action_label: str
    action_href: str


@dataclass(frozen=True)
class AnalysisSessionClientBrief:
    status: str
    title: str
    decision: str
    priority_focus: str
    immediate_action: str
    validation: str
    delivery_status: str
    action_label: str
    action_href: str


@dataclass(frozen=True)
class AnalysisSessionFindingExplainer:
    title: str
    severity: str
    status: str
    asset: str
    plain_explanation: str
    why_it_matters: str
    remediation: str
    validation: str
    action_label: str
    action_href: str


@dataclass(frozen=True)
class AnalysisSessionExecutionQueueItem:
    check: str
    label: str
    status: str
    readiness_detail: str
    planned_command_count: int
    last_run_status: str
    last_run_summary: str
    finding_count: int
    evidence_count: int
    action_label: str
    action_href: str


@dataclass(frozen=True)
class AnalysisSessionDashboard:
    status: str
    title: str
    detail: str
    mode: str
    progress_percent: int
    current_phase: str
    ready_step_count: int
    needs_attention_step_count: int
    blocked_step_count: int
    total_step_count: int
    next_action_label: str
    next_action_href: str
    next_action_detail: str
    internal_target_count: int
    external_target_count: int
    ad_target_count: int
    domain_target_count: int
    selected_service_count: int
    ready_service_count: int
    blocked_service_count: int
    completed_service_count: int
    failed_service_count: int
    run_count: int
    finding_count: int
    vulnerability_match_count: int
    report_count: int
    package_ready: bool
    selected_services: tuple[str, ...]
    target_summary: tuple[str, ...]
    steps: list[AnalysisSessionStep]
    workflow_lanes: list[AnalysisSessionWorkflowLane]
    result_shortcuts: list[AnalysisSessionResultShortcut]
    timeline_items: list[AnalysisSessionTimelineItem]
    remediation_priorities: list[AnalysisSessionRemediationPriority]
    client_brief: AnalysisSessionClientBrief
    finding_explainers: list[AnalysisSessionFindingExplainer]
    execution_queue: list[AnalysisSessionExecutionQueueItem]


@dataclass(frozen=True)
class ScanLaunchChecklistItem:
    label: str
    status: str
    command_count: int
    detail: str
    action_label: str
    action_href: str


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
    checklist: list[ScanLaunchChecklistItem]


@dataclass(frozen=True)
class ReportDeliveryItem:
    label: str
    status: str
    detail: str
    action_label: str
    action_href: str


@dataclass(frozen=True)
class ReportDeliverySummary:
    status: str
    detail: str
    action_label: str
    action_href: str
    ready_count: int
    total_count: int
    items: list[ReportDeliveryItem]


@dataclass(frozen=True)
class CustomerHandoffItem:
    label: str
    status: str
    detail: str


@dataclass(frozen=True)
class CustomerHandoffSummary:
    status: str
    title: str
    detail: str
    action_label: str
    action_href: str
    ready_count: int
    total_count: int
    items: list[CustomerHandoffItem]


@dataclass(frozen=True)
class MissionGoNoGoItem:
    label: str
    status: str
    detail: str
    action_label: str
    action_href: str


@dataclass(frozen=True)
class MissionGoNoGoSummary:
    status: str
    decision: str
    detail: str
    action_label: str
    action_href: str
    ready_count: int
    total_count: int
    items: list[MissionGoNoGoItem]


@dataclass(frozen=True)
class MissionActionStep:
    number: int
    label: str
    status: str
    detail: str
    action_label: str
    action_href: str


@dataclass(frozen=True)
class MissionQuickRead:
    status: str
    decision: str
    immediate_action: str
    priority_focus: str
    next_counter_test: str
    audience_note: str
    action_label: str
    action_href: str


@dataclass(frozen=True)
class DashboardView:
    clients: list[ClientRow]
    missions: list[MissionRow]
    preparation_items: list[DashboardPreparationRow]
    technician_workflow_steps: list[DashboardOnboardingStep]
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
    session_dashboard: AnalysisSessionDashboard
    go_no_go: MissionGoNoGoSummary
    cockpit: MissionCockpit
    scan_launch: ScanLaunchCenter
    action_roadmap: list[MissionActionStep]
    quick_read: MissionQuickRead
    activity_log_url: str
    scope: list[ScopeRow]
    scope_intake: ScopeIntakeSummary
    findings: list[FindingRow]
    finding_dispositions: list[FindingDispositionRow]
    counter_test_summary: list[CounterTestSummaryRow]
    counter_test_items: list[CounterTestRow]
    activity_events: list[ActivityEventRow]
    check_selection: list[CheckSelectionRow]
    scan_runs: list[ScanRunRow]
    scan_run_outcome: ScanRunOutcomeSummary
    remediation_items: list[dict[str, str]]
    executive_summary: str
    authorization_briefs: list[AuthorizationBriefLink]
    reports: list[GeneratedReportLink]
    report_delivery: ReportDeliverySummary
    customer_handoff: CustomerHandoffSummary
    mission_export: MissionExportLink | None
    readiness_items: list[ReadinessItem]
    scan_plans: list[ScanPlanPreview]
    vulnerability_summary: VulnerabilitySummary
    vulnerability_review_items: list[VulnerabilityReviewItem]
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
class VulnerabilityReviewItem:
    label: str
    status: str
    detail: str
    action_label: str
    action_href: str


@dataclass(frozen=True)
class VulnerabilityMatchRow:
    cve_id: str
    title: str
    severity: str
    known_exploited: bool
    priority_label: str
    priority_reason: str
    affected_asset: str
    matched_finding_id: str
    matched_terms: str
    risk: str
    remediation: str
    counter_test: str
    validation_steps: tuple[str, ...]
    references: tuple[str, ...]


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

CHECK_USE_CASES: dict[AuditCheck, str] = {
    AuditCheck.NMAP: "Map exposed services on internal or public network targets.",
    AuditCheck.HTTP_HEADERS: "Review web application browser protection headers.",
    AuditCheck.DNS_MAIL: "Validate public DNS and mail hygiene for a domain.",
    AuditCheck.TLS: "Review certificate, protocol, and cipher posture on HTTPS endpoints.",
    AuditCheck.SMB: "Check whether file sharing exposes anonymous listing paths.",
    AuditCheck.LDAP: "Check whether directory metadata is anonymously visible.",
}

SCOPE_INTAKE_LABELS: dict[ScopeType, str] = {
    ScopeType.URL: "Web application URL",
    ScopeType.DOMAIN: "Domain",
    ScopeType.HOST: "Server or AD hostname",
    ScopeType.IP: "Server IP",
    ScopeType.CIDR: "Internal network CIDR",
}

SCOPE_INTAKE_EXAMPLES: dict[ScopeType, str] = {
    ScopeType.URL: "https://portal.client.example",
    ScopeType.DOMAIN: "client.example",
    ScopeType.HOST: "dc01.client.local",
    ScopeType.IP: "192.168.1.10",
    ScopeType.CIDR: "192.168.1.0/24",
}

SCOPE_INTAKE_ORDER: tuple[ScopeType, ...] = (
    ScopeType.URL,
    ScopeType.DOMAIN,
    ScopeType.HOST,
    ScopeType.IP,
    ScopeType.CIDR,
)

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


def mission_quick_read(summary: dict[str, object]) -> MissionQuickRead:
    raw_quick_read = summary["quick_read"]
    if not isinstance(raw_quick_read, dict):
        raise TypeError("report summary quick_read must be a mapping")

    decision = str(raw_quick_read.get("decision", "Suivi d’hygiène"))
    if decision == "Aucun constat actif":
        status = "ready"
        action_label = "Open Reports"
        action_href = "#reports"
    elif decision == "Action prioritaire requise":
        status = "warning"
        action_label = "Review Findings"
        action_href = "#findings"
    else:
        status = "warning"
        action_label = "Review Findings"
        action_href = "#findings"

    return MissionQuickRead(
        status=status,
        decision=decision,
        immediate_action=str(raw_quick_read.get("immediate_action", "")),
        priority_focus=str(raw_quick_read.get("priority_focus", "")),
        next_counter_test=str(raw_quick_read.get("next_counter_test", "")),
        audience_note=str(raw_quick_read.get("audience_note", "")),
        action_label=action_label,
        action_href=action_href,
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


def dashboard_workflow_status(statuses: list[str]) -> str:
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if any(status == "warning" for status in statuses):
        return "warning"
    return "ready"


def build_dashboard_technician_workflow_steps(
    onboarding_steps: list[DashboardOnboardingStep],
    ready_preparation_count: int,
    warning_preparation_count: int,
    blocked_preparation_count: int,
    total_findings: int,
    high_or_critical_findings: int,
) -> list[DashboardOnboardingStep]:
    onboarding = {item.label: item for item in onboarding_steps}
    authorization = onboarding["Authorization"]
    approved_scope = onboarding["Approved scope"]
    check_selection = onboarding["Check selection"]
    finding_review = onboarding["Finding review"]
    ready_for_scans = ready_preparation_count > 0
    preparation_status = (
        "ready"
        if ready_for_scans
        else "warning"
        if warning_preparation_count
        else "blocked"
    )
    handoff_status = (
        "ready"
        if all(item.status == "ready" for item in onboarding_steps)
        else "warning"
        if total_findings
        else "blocked"
    )

    return [
        DashboardOnboardingStep(
            label="1. Create audit",
            status=dashboard_workflow_status(
                [
                    onboarding["Client record"].status,
                    onboarding["Mission setup"].status,
                ]
            ),
            detail="Create or continue a guided client audit from the wizard.",
            action_label="Open Wizard",
            action_href="/wizard",
        ),
        DashboardOnboardingStep(
            label="2. Authorize scope",
            status=dashboard_workflow_status([authorization.status, approved_scope.status]),
            detail="Record written authorization and approve only validated targets.",
            action_label=(
                authorization.action_label
                if authorization.status != "ready"
                else approved_scope.action_label
            ),
            action_href=(
                authorization.action_href
                if authorization.status != "ready"
                else approved_scope.action_href
            ),
        ),
        DashboardOnboardingStep(
            label="3. Select services",
            status=check_selection.status,
            detail="Choose safe audit services that match the approved scope.",
            action_label=check_selection.action_label,
            action_href=check_selection.action_href,
        ),
        DashboardOnboardingStep(
            label="4. Launch guarded checks",
            status=preparation_status,
            detail=(
                f"{ready_preparation_count} ready, {warning_preparation_count} review, "
                f"{blocked_preparation_count} blocked mission(s)."
            ),
            action_label="Open Ready Missions" if ready_for_scans else "Review Preparation",
            action_href="#ready-missions" if ready_for_scans else "#preparation",
        ),
        DashboardOnboardingStep(
            label="5. Review findings",
            status=finding_review.status,
            detail=f"{total_findings} finding(s), {high_or_critical_findings} high/critical.",
            action_label=finding_review.action_label,
            action_href=finding_review.action_href,
        ),
        DashboardOnboardingStep(
            label="6. Reports and handoff",
            status=handoff_status,
            detail="Generate reports, export the mission package, and review the Pilot bundle.",
            action_label="Open Pilot" if handoff_status == "ready" else "Review Pilot",
            action_href="/pilot",
        ),
    ]


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
            target_status=check_target_status(mission, check),
            target_requirement=f"Needs {CHECK_SCOPE_REQUIREMENTS[check]}.",
            target_summary=check_target_summary(mission, check),
            matching_scope_count=len(compatible_scope_items(mission, check)),
        )
        for check in AuditCheck
    ]


def approved_scope_items(mission: Mission) -> list[ScopeItem]:
    return [item for item in mission.scope if item.approved and not item.excluded]


def draft_scope_items(mission: Mission) -> list[ScopeItem]:
    return [item for item in mission.scope if not item.approved and not item.excluded]


def excluded_scope_items(mission: Mission) -> list[ScopeItem]:
    return [item for item in mission.scope if item.excluded]


def compatible_scope_items(mission: Mission, check: AuditCheck) -> list[ScopeItem]:
    allowed_types = CHECK_SCOPE_TYPES[check]
    return [item for item in approved_scope_items(mission) if item.type in allowed_types]


def check_target_status(mission: Mission, check: AuditCheck) -> str:
    if compatible_scope_items(mission, check):
        return "ready"
    if check in mission.selected_checks:
        return "blocked"
    return "missing"


def check_target_summary(mission: Mission, check: AuditCheck) -> str:
    matches = compatible_scope_items(mission, check)
    if not matches:
        return f"Add {CHECK_SCOPE_REQUIREMENTS[check]} before launch."

    preview_values = [item.value for item in matches[:3]]
    preview = ", ".join(preview_values)
    if len(matches) > len(preview_values):
        preview = f"{preview}, +{len(matches) - len(preview_values)} more"
    return f"{len(matches)} compatible approved target(s): {preview}."


def scope_intake_summary(mission: Mission) -> ScopeIntakeSummary:
    selected_checks = list(mission.selected_checks)
    approved_items = approved_scope_items(mission)
    draft_items = draft_scope_items(mission)
    excluded_items = excluded_scope_items(mission)
    ready_checks = [
        check
        for check in selected_checks
        if compatible_scope_items(mission, check)
    ]

    if not selected_checks:
        status = "missing"
        detail = "Select audit services before completing the target intake."
        action_label = "Select Checks"
        action_href = "#check-selection"
    elif len(ready_checks) == len(selected_checks):
        status = "ready"
        detail = "Selected services have compatible approved scope."
        action_label = "Review Scan Plan"
        action_href = "#scan-plan"
    elif ready_checks:
        status = "warning"
        detail = (
            f"{len(ready_checks)}/{len(selected_checks)} selected service(s) "
            "have compatible approved scope."
        )
        action_label = "Complete Scope"
        action_href = "#scope"
    else:
        status = "blocked"
        detail = "Selected services do not yet have compatible approved scope."
        action_label = "Add Scope"
        action_href = "#scope"

    return ScopeIntakeSummary(
        status=status,
        detail=detail,
        action_label=action_label,
        action_href=action_href,
        approved_count=len(approved_items),
        draft_count=len(draft_items),
        excluded_count=len(excluded_items),
        items=[scope_intake_item(mission, scope_type) for scope_type in SCOPE_INTAKE_ORDER],
    )


def scope_intake_item(mission: Mission, scope_type: ScopeType) -> ScopeIntakeItem:
    matching_items = [
        item for item in approved_scope_items(mission) if item.type == scope_type
    ]
    draft_items = [item for item in draft_scope_items(mission) if item.type == scope_type]
    services = selected_services_for_scope_type(mission, scope_type)
    if matching_items:
        status = "ready"
        detail = f"{len(matching_items)} approved target(s) match this intake type."
    elif services:
        status = "blocked"
        detail = "Required by selected service(s); add and approve this target type."
    elif draft_items:
        status = "warning"
        detail = f"{len(draft_items)} draft target(s) need approval before launch."
    else:
        status = "missing"
        detail = "Not required by the current service selection."

    return ScopeIntakeItem(
        label=SCOPE_INTAKE_LABELS[scope_type],
        scope_type=scope_type.value,
        status=status,
        detail=detail,
        example=SCOPE_INTAKE_EXAMPLES[scope_type],
        matching_scope_count=len(matching_items),
        services=services,
        action_label="Add Scope" if status in {"blocked", "missing"} else "Review Scope",
        action_href="#scope",
    )


def selected_services_for_scope_type(mission: Mission, scope_type: ScopeType) -> list[str]:
    return [
        CHECK_LABELS[check]
        for check in mission.selected_checks
        if scope_type in CHECK_SCOPE_TYPES[check]
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
    check_label = CHECK_LABELS.get(run.check, run.check.value)
    evidence_count = len(run.evidence_paths)
    if run.status is ScanRunStatus.FAILED:
        status_title = "Run failed"
        summary = (
            f"{check_label} failed after {run.command_count} command(s). "
            "Review the error before rerunning the check."
        )
        action_label = "Review Error"
        action_href = "#run-monitor"
    elif run.finding_count:
        status_title = "Findings imported"
        summary = (
            f"{check_label} completed with {run.finding_count} finding(s) "
            "ready for review."
        )
        action_label = "Review Findings"
        action_href = "#findings"
    elif evidence_count:
        status_title = "Evidence captured"
        summary = (
            f"{check_label} completed with {evidence_count} evidence file(s) "
            "and no imported findings."
        )
        action_label = "Generate Reports"
        action_href = "#reports"
    else:
        status_title = "Completed without findings"
        summary = (
            f"{check_label} completed without imported findings or evidence files."
        )
        action_label = "Generate Reports"
        action_href = "#reports"
    return ScanRunRow(
        id=run.id,
        check=run.check.value,
        label=check_label,
        status=run.status.value,
        status_title=status_title,
        started_at=format_datetime(run.started_at),
        command_count=run.command_count,
        finding_count=run.finding_count,
        evidence_count=evidence_count,
        evidence_summary=f"{evidence_count} evidence file(s)",
        summary=summary,
        action_label=action_label,
        action_href=action_href,
        error=run.error or "",
    )


def scan_run_outcome_summary(
    scan_runs: list[ScanRun],
    findings: list[Finding],
) -> ScanRunOutcomeSummary:
    active_finding_count = len(active_findings(findings))
    total_evidence_count = sum(len(run.evidence_paths) for run in scan_runs)
    if not scan_runs:
        return ScanRunOutcomeSummary(
            status="missing",
            title="No run recorded yet",
            detail=(
                "Launch a ready check after authorization and approved scope are confirmed."
            ),
            action_label="Open Scan Plan",
            action_href="#scan-plan",
            run_count=0,
            finding_count=active_finding_count,
            evidence_count=0,
        )

    latest_run = max(scan_runs, key=lambda run: run.started_at)
    check_label = CHECK_LABELS.get(latest_run.check, latest_run.check.value)
    latest_evidence_count = len(latest_run.evidence_paths)
    detail = (
        f"Latest {check_label} run started {format_datetime(latest_run.started_at)} "
        f"with {latest_run.command_count} command(s), "
        f"{latest_run.finding_count} finding(s), "
        f"{latest_evidence_count} evidence file(s)."
    )
    if latest_run.error:
        detail = f"{detail} Error: {latest_run.error}"
    if latest_run.status is ScanRunStatus.FAILED:
        action_label = "Review Error"
        action_href = "#run-monitor"
    elif active_finding_count:
        action_label = "Review Findings"
        action_href = "#findings"
    else:
        action_label = "Generate Reports"
        action_href = "#reports"
    return ScanRunOutcomeSummary(
        status=latest_run.status.value,
        title=f"Latest run: {check_label}",
        detail=detail,
        action_label=action_label,
        action_href=action_href,
        run_count=len(scan_runs),
        finding_count=active_finding_count,
        evidence_count=total_evidence_count,
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
        checklist=scan_launch_checklist(scan_plans),
    )


def analysis_session_dashboard(
    mission: Mission,
    findings: list[Finding],
    scan_plans: list[ScanPlanPreview],
    scan_runs: list[ScanRun],
    reports: list[GeneratedReportLink],
    mission_export: MissionExportLink | None,
    vulnerability: VulnerabilitySummary,
) -> AnalysisSessionDashboard:
    latest_runs = latest_scan_runs_by_check(scan_runs)
    selected_checks = [plan.check for plan in scan_plans]
    selected_count = len(selected_checks)
    completed_count = len(
        [
            check
            for check in selected_checks
            if latest_runs.get(check) is not None
            and latest_runs[check].status is ScanRunStatus.COMPLETED
        ]
    )
    failed_count = len(
        [
            check
            for check in selected_checks
            if latest_runs.get(check) is not None
            and latest_runs[check].status is ScanRunStatus.FAILED
        ]
    )
    ready_count = len([plan for plan in scan_plans if plan.status == "ready"])
    blocked_count = len([plan for plan in scan_plans if plan.status == "blocked"])
    approved_scope = [
        item for item in mission.scope if item.approved and not item.excluded
    ]
    internal_targets = [
        item for item in approved_scope if item.environment.value == "internal"
    ]
    external_targets = [
        item for item in approved_scope if item.environment.value == "external"
    ]
    ad_targets = [item for item in approved_scope if item.type == ScopeType.HOST]
    domain_targets = [item for item in approved_scope if item.type == ScopeType.DOMAIN]
    reports_ready = bool(reports)
    package_ready = mission_export is not None and mission_export.handoff_status == "ready"

    steps = [
        analysis_session_step(
            label="Authorization",
            ready=mission.is_authorized,
            warning=False,
            detail=(
                "Written authorization is recorded."
                if mission.is_authorized
                else "Record written authorization before live checks."
            ),
            weight=15,
            action_label="Review Authorization",
            action_href="#mission-setup",
        ),
        analysis_session_step(
            label="Approved Scope",
            ready=bool(approved_scope),
            warning=False,
            detail=(
                f"{len(approved_scope)} approved target(s)."
                if approved_scope
                else "Add and approve internal or external targets."
            ),
            weight=15,
            action_label="Review Scope",
            action_href="#scope",
        ),
        analysis_session_step(
            label="Service Selection",
            ready=selected_count > 0 and ready_count > 0,
            warning=blocked_count > 0,
            detail=(
                f"{ready_count} ready service(s), {blocked_count} blocked."
                if selected_count
                else "Select protocols/services to test."
            ),
            weight=20,
            action_label="Review Services",
            action_href="#check-selection",
        ),
        analysis_session_run_step(
            completed_count=completed_count,
            failed_count=failed_count,
            selected_count=selected_count,
        ),
        analysis_session_step(
            label="CVE/KEV Review",
            ready=vulnerability.status == "ready",
            warning=vulnerability.status == "warning",
            detail=vulnerability.detail,
            weight=10,
            action_label=vulnerability.action_label,
            action_href=vulnerability.action_href,
        ),
        analysis_session_step(
            label="Reports",
            ready=reports_ready,
            warning=bool(findings) and not reports_ready,
            detail=(
                f"{len(reports)} report file(s) generated."
                if reports_ready
                else "Generate PDF, JSON, Markdown, and HTML reports after review."
            ),
            weight=10,
            action_label="Generate Reports",
            action_href="#reports",
        ),
        analysis_session_step(
            label="Handoff Package",
            ready=package_ready,
            warning=reports_ready and not package_ready,
            detail=(
                "Mission export package is ready for handoff."
                if package_ready
                else "Generate and verify the mission export package before delivery."
            ),
            weight=5,
            action_label="Review Exports",
            action_href="#mission-export",
        ),
    ]
    earned = sum(step.earned for step in steps)
    weight = sum(step.weight for step in steps) or 1
    progress_percent = min(100, round((earned / weight) * 100))
    status = analysis_session_status(steps)
    current_phase = analysis_current_phase(steps)
    ready_step_count = len([step for step in steps if step.status == "ready"])
    needs_attention_step_count = len(
        [step for step in steps if step.status in {"blocked", "missing", "warning"}]
    )
    blocked_step_count = len([step for step in steps if step.status == "blocked"])
    total_step_count = len(steps)
    next_step = next(
        (step for step in steps if step.status in {"blocked", "missing", "warning"}),
        steps[-1],
    )
    title = analysis_session_title(status, progress_percent)
    detail = (
        f"{completed_count}/{selected_count} selected service(s) completed, "
        f"{len(findings)} finding(s), {vulnerability.match_count} CVE/KEV candidate(s)."
    )
    active_finding_count = len(active_findings(findings))
    workflow_lanes = analysis_session_workflow_lanes(
        approved_scope_count=len(approved_scope),
        selected_count=selected_count,
        ready_count=ready_count,
        blocked_count=blocked_count,
        completed_count=completed_count,
        failed_count=failed_count,
        run_count=len(scan_runs),
        finding_count=active_finding_count,
        vulnerability_match_count=vulnerability.match_count,
        reports_ready=reports_ready,
        report_count=len(reports),
        package_ready=package_ready,
    )
    result_shortcuts = analysis_session_result_shortcuts(
        approved_scope_count=len(approved_scope),
        selected_count=selected_count,
        ready_count=ready_count,
        blocked_count=blocked_count,
        completed_count=completed_count,
        failed_count=failed_count,
        run_count=len(scan_runs),
        finding_count=active_finding_count,
        vulnerability_match_count=vulnerability.match_count,
        reports_ready=reports_ready,
        report_count=len(reports),
        package_ready=package_ready,
    )
    timeline_items = analysis_session_timeline_items(
        mission=mission,
        findings=findings,
        scan_runs=scan_runs,
        reports=reports,
        mission_export=mission_export,
        vulnerability=vulnerability,
    )
    remediation_priorities = analysis_session_remediation_priorities(findings)
    client_brief = analysis_session_client_brief(
        findings=findings,
        reports_ready=reports_ready,
        package_ready=package_ready,
        run_count=len(scan_runs),
        vulnerability_match_count=vulnerability.match_count,
    )
    finding_explainers = analysis_session_finding_explainers(findings)
    execution_queue = analysis_session_execution_queue(scan_plans, latest_runs)
    return AnalysisSessionDashboard(
        status=status,
        title=title,
        detail=detail,
        mode=mission.audit_type.value,
        progress_percent=progress_percent,
        current_phase=current_phase,
        ready_step_count=ready_step_count,
        needs_attention_step_count=needs_attention_step_count,
        blocked_step_count=blocked_step_count,
        total_step_count=total_step_count,
        next_action_label=next_step.action_label,
        next_action_href=next_step.action_href,
        next_action_detail=next_step.detail,
        internal_target_count=len(internal_targets),
        external_target_count=len(external_targets),
        ad_target_count=len(ad_targets),
        domain_target_count=len(domain_targets),
        selected_service_count=selected_count,
        ready_service_count=ready_count,
        blocked_service_count=blocked_count,
        completed_service_count=completed_count,
        failed_service_count=failed_count,
        run_count=len(scan_runs),
        finding_count=active_finding_count,
        vulnerability_match_count=vulnerability.match_count,
        report_count=len(reports),
        package_ready=package_ready,
        selected_services=tuple(plan.label for plan in scan_plans),
        target_summary=tuple(session_target_summary_item(item) for item in approved_scope[:8]),
        steps=steps,
        workflow_lanes=workflow_lanes,
        result_shortcuts=result_shortcuts,
        timeline_items=timeline_items,
        remediation_priorities=remediation_priorities,
        client_brief=client_brief,
        finding_explainers=finding_explainers,
        execution_queue=execution_queue,
    )


def analysis_session_workflow_lanes(
    approved_scope_count: int,
    selected_count: int,
    ready_count: int,
    blocked_count: int,
    completed_count: int,
    failed_count: int,
    run_count: int,
    finding_count: int,
    vulnerability_match_count: int,
    reports_ready: bool,
    report_count: int,
    package_ready: bool,
) -> list[AnalysisSessionWorkflowLane]:
    discovery_status = "ready" if approved_scope_count and ready_count else "missing"
    if blocked_count:
        discovery_status = "warning"
    discovery_detail = (
        "Perimetre et services compatibles sont prets pour une execution controlee."
        if discovery_status == "ready"
        else "Valide le perimetre et les services compatibles avant de lancer."
    )

    if failed_count:
        execution_status = "blocked"
        execution_detail = "Une execution a echoue et doit etre revue avant restitution."
    elif selected_count and completed_count == selected_count:
        execution_status = "ready"
        execution_detail = "Tous les controles selectionnes ont une execution terminee."
    elif run_count:
        execution_status = "warning"
        execution_detail = "Des executions existent mais la session n'est pas complete."
    else:
        execution_status = "missing"
        execution_detail = "Aucun controle n'a encore ete execute pour cette session."

    if finding_count or vulnerability_match_count:
        analysis_status = "ready"
        analysis_detail = "Des constats ou candidats CVE/KEV sont disponibles a qualifier."
    elif run_count:
        analysis_status = "warning"
        analysis_detail = "Les executions sont enregistrees; verifie les preuves et resultats."
    else:
        analysis_status = "missing"
        analysis_detail = "L'analyse demarre apres les premiers controles enregistres."

    if reports_ready and package_ready:
        delivery_status = "ready"
        delivery_detail = "Rapports et package de remise sont disponibles."
    elif reports_ready:
        delivery_status = "warning"
        delivery_detail = "Les rapports existent; prepare le package de remise client."
    else:
        delivery_status = "missing"
        delivery_detail = "Genere les rapports apres qualification des constats."

    return [
        AnalysisSessionWorkflowLane(
            label="Decouverte",
            status=discovery_status,
            detail=discovery_detail,
            primary_label="Cibles",
            primary_value=str(approved_scope_count),
            secondary_label="Services prets",
            secondary_value=f"{ready_count}/{selected_count}",
            action_label="Voir cibles",
            action_href="#session-targets",
        ),
        AnalysisSessionWorkflowLane(
            label="Execution",
            status=execution_status,
            detail=execution_detail,
            primary_label="Runs",
            primary_value=str(run_count),
            secondary_label="Termines",
            secondary_value=f"{completed_count}/{selected_count}",
            action_label="Voir executions",
            action_href="#session-runs",
        ),
        AnalysisSessionWorkflowLane(
            label="Analyse",
            status=analysis_status,
            detail=analysis_detail,
            primary_label="Constats",
            primary_value=str(finding_count),
            secondary_label="CVE/KEV",
            secondary_value=str(vulnerability_match_count),
            action_label="Voir constats",
            action_href="#session-findings",
        ),
        AnalysisSessionWorkflowLane(
            label="Restitution",
            status=delivery_status,
            detail=delivery_detail,
            primary_label="Rapports",
            primary_value=str(report_count),
            secondary_label="Package",
            secondary_value="pret" if package_ready else "a faire",
            action_label="Voir livrables",
            action_href="#session-findings",
        ),
    ]


def analysis_session_result_shortcuts(
    approved_scope_count: int,
    selected_count: int,
    ready_count: int,
    blocked_count: int,
    completed_count: int,
    failed_count: int,
    run_count: int,
    finding_count: int,
    vulnerability_match_count: int,
    reports_ready: bool,
    report_count: int,
    package_ready: bool,
) -> list[AnalysisSessionResultShortcut]:
    service_status = "ready" if ready_count and not blocked_count else "missing"
    if blocked_count:
        service_status = "warning"

    if failed_count:
        execution_status = "blocked"
        execution_detail = f"{failed_count} execution(s) a revoir avant livraison."
    elif run_count:
        execution_status = "ready" if selected_count and completed_count == selected_count else "warning"
        execution_detail = f"{completed_count}/{selected_count} controle(s) termines."
    else:
        execution_status = "missing"
        execution_detail = "Aucune execution enregistree."

    finding_status = "ready" if finding_count else "missing"
    if run_count and not finding_count:
        finding_status = "warning"

    cve_status = "ready" if vulnerability_match_count else "missing"
    if finding_count and not vulnerability_match_count:
        cve_status = "warning"

    delivery_status = "ready" if reports_ready and package_ready else "missing"
    if reports_ready and not package_ready:
        delivery_status = "warning"

    return [
        AnalysisSessionResultShortcut(
            label="Cibles",
            category="Decouverte",
            status="ready" if approved_scope_count else "missing",
            count=str(approved_scope_count),
            detail="Perimetre approuve et exploitable par les controles selectionnes.",
            action_label="Voir cibles",
            action_href="#session-targets",
        ),
        AnalysisSessionResultShortcut(
            label="Services",
            category="Decouverte",
            status=service_status,
            count=str(selected_count),
            detail=f"{ready_count} pret(s), {blocked_count} bloque(s).",
            action_label="Voir services",
            action_href="#session-services",
        ),
        AnalysisSessionResultShortcut(
            label="Executions",
            category="Execution",
            status=execution_status,
            count=str(run_count),
            detail=execution_detail,
            action_label="Voir runs",
            action_href="#session-runs",
        ),
        AnalysisSessionResultShortcut(
            label="CVE/KEV",
            category="Analyse",
            status=cve_status,
            count=str(vulnerability_match_count),
            detail="Candidats a valider avant stockage en constats client.",
            action_label="Verifier CVE",
            action_href="#session-findings",
        ),
        AnalysisSessionResultShortcut(
            label="Constats",
            category="Analyse",
            status=finding_status,
            count=str(finding_count),
            detail="Constats actifs a expliquer, corriger et contre-tester.",
            action_label="Voir constats",
            action_href="#session-findings",
        ),
        AnalysisSessionResultShortcut(
            label="Livrables",
            category="Restitution",
            status=delivery_status,
            count=str(report_count),
            detail="Rapports et package a verifier avant remise client.",
            action_label="Voir livrables",
            action_href="#session-findings",
        ),
    ]


def analysis_session_timeline_items(
    mission: Mission,
    findings: list[Finding],
    scan_runs: list[ScanRun],
    reports: list[GeneratedReportLink],
    mission_export: MissionExportLink | None,
    vulnerability: VulnerabilitySummary,
) -> list[AnalysisSessionTimelineItem]:
    items = [
        AnalysisSessionTimelineItem(
            label="Mission creee",
            status="ready" if mission.is_authorized else "missing",
            timestamp=format_datetime(mission.created_at),
            detail=(
                "Autorisation renseignee; la session peut suivre les controles approuves."
                if mission.is_authorized
                else "Ajoute la reference d'autorisation avant tout controle live."
            ),
            action_label="Preparation",
            action_href="#session-steps",
        )
    ]

    for run in sorted(scan_runs, key=lambda item: item.started_at, reverse=True)[:3]:
        check_label = CHECK_LABELS.get(run.check, run.check.value)
        evidence_count = len(run.evidence_paths)
        detail = (
            f"{run.command_count} commande(s), {run.finding_count} constat(s), "
            f"{evidence_count} preuve(s)."
        )
        if run.error:
            detail = f"{detail} Erreur : {run.error}"
        items.append(
            AnalysisSessionTimelineItem(
                label=f"Controle {check_label}",
                status=run.status.value,
                timestamp=format_datetime(run.started_at),
                detail=detail,
                action_label="Voir execution",
                action_href="#session-runs",
            )
        )

    active = active_findings(findings)
    if active:
        latest_finding = max(active, key=lambda finding: finding.last_seen)
        critical_or_high = any(
            finding.severity in {Severity.CRITICAL, Severity.HIGH} for finding in active
        )
        items.append(
            AnalysisSessionTimelineItem(
                label="Revue constats",
                status="warning" if critical_or_high else "ready",
                timestamp=format_datetime(latest_finding.last_seen),
                detail=f"{len(active)} constat(s) actif(s) a expliquer et prioriser.",
                action_label="Voir constats",
                action_href="#session-findings",
            )
        )
    else:
        items.append(
            AnalysisSessionTimelineItem(
                label="Revue constats",
                status="missing",
                timestamp="A venir",
                detail="Aucun constat actif n'est encore disponible pour cette session.",
                action_label="Voir constats",
                action_href="#session-findings",
            )
        )

    if vulnerability.match_count:
        items.append(
            AnalysisSessionTimelineItem(
                label="CVE/KEV a valider",
                status="warning",
                timestamp="A valider",
                detail=(
                    f"{vulnerability.match_count} candidat(s), "
                    f"{vulnerability.known_exploited_count} connu(s) exploite(s)."
                ),
                action_label="Verifier CVE",
                action_href="#session-findings",
            )
        )

    if reports:
        items.append(
            AnalysisSessionTimelineItem(
                label="Rapports generes",
                status="ready",
                timestamp="Disponible",
                detail=f"{len(reports)} livrable(s) rapport sont disponibles.",
                action_label="Voir livrables",
                action_href="#session-findings",
            )
        )

    if mission_export is not None:
        items.append(
            AnalysisSessionTimelineItem(
                label="Package remise",
                status=mission_export.handoff_status,
                timestamp="Package",
                detail=mission_export.handoff_detail,
                action_label="Verifier package",
                action_href="#session-findings",
            )
        )

    return items[:8]


def analysis_session_remediation_priorities(
    findings: list[Finding],
) -> list[AnalysisSessionRemediationPriority]:
    priorities = []
    for finding in sorted_findings(active_findings(findings))[:4]:
        priorities.append(
            AnalysisSessionRemediationPriority(
                title=finding.title,
                severity=finding.severity.value,
                status=finding.status.value,
                asset=finding.affected_asset,
                risk=finding.risk,
                remediation=finding.remediation,
                counter_test=finding.counter_test,
                action_label="Qualifier",
                action_href="#session-findings",
            )
        )
    return priorities


def analysis_session_client_brief(
    findings: list[Finding],
    reports_ready: bool,
    package_ready: bool,
    run_count: int,
    vulnerability_match_count: int,
) -> AnalysisSessionClientBrief:
    active = sorted_findings(active_findings(findings))
    priority = active[0] if active else None

    if package_ready:
        delivery_status = "Package de remise pret pour validation client."
    elif reports_ready:
        delivery_status = "Rapports generes ; package de remise a finaliser."
    elif priority:
        delivery_status = "Rapports a generer apres qualification des constats."
    else:
        delivery_status = "Rapports a generer apres execution ou validation."

    if priority is not None:
        is_urgent = priority.severity in {Severity.CRITICAL, Severity.HIGH}
        status = "warning" if is_urgent else "ready"
        title = (
            "Brief Client : Action Prioritaire"
            if is_urgent
            else "Brief Client : Ameliorations A Planifier"
        )
        decision = (
            "Prioriser une correction avant cloture"
            if is_urgent
            else "Planifier les corrections dans le suivi de maintenance"
        )
        priority_focus = f"{priority.title} sur {priority.affected_asset}"
        if vulnerability_match_count:
            priority_focus = (
                f"{priority_focus} ; {vulnerability_match_count} candidat(s) CVE/KEV a verifier"
            )
        return AnalysisSessionClientBrief(
            status=status,
            title=title,
            decision=decision,
            priority_focus=priority_focus,
            immediate_action=priority.remediation,
            validation=priority.counter_test,
            delivery_status=delivery_status,
            action_label="Voir priorites",
            action_href="#session-findings",
        )

    if run_count:
        return AnalysisSessionClientBrief(
            status="ready",
            title="Brief Client : Aucun Constat Actif",
            decision="Restitution possible apres verification des preuves",
            priority_focus="Aucun constat actif stocke pour cette session.",
            immediate_action=(
                "Verifier que les executions attendues sont terminees puis generer les livrables."
            ),
            validation="Conserver le rapport JSON pour le suivi et le contre-test.",
            delivery_status=delivery_status,
            action_label="Voir rapports",
            action_href="#reports",
        )

    return AnalysisSessionClientBrief(
        status="missing",
        title="Brief Client : En Attente D'Execution",
        decision="Executer les controles autorises",
        priority_focus="Aucun resultat exploitable pour le moment.",
        immediate_action=(
            "Valider le perimetre, les services selectionnes et lancer les controles prets."
        ),
        validation="Revenir sur ce dashboard quand les executions auront produit des preuves.",
        delivery_status=delivery_status,
        action_label="Preparer controles",
        action_href="#check-selection",
    )


def analysis_session_finding_explainers(
    findings: list[Finding],
) -> list[AnalysisSessionFindingExplainer]:
    explainers = []
    for finding in sorted_findings(active_findings(findings))[:3]:
        explainers.append(
            AnalysisSessionFindingExplainer(
                title=finding.title,
                severity=finding.severity.value,
                status=finding.status.value,
                asset=finding.affected_asset,
                plain_explanation=plain_finding_explanation(finding),
                why_it_matters=plain_finding_impact(finding),
                remediation=finding.remediation,
                validation=finding.counter_test,
                action_label="Ouvrir constat",
                action_href="#session-findings",
            )
        )
    return explainers


def analysis_session_execution_queue(
    scan_plans: list[ScanPlanPreview],
    latest_runs: dict[str, ScanRun],
) -> list[AnalysisSessionExecutionQueueItem]:
    queue = []
    for plan in scan_plans:
        latest_run = latest_runs.get(plan.check)
        planned_command_count = len(plan.commands)
        if latest_run is not None:
            evidence_count = len(latest_run.evidence_paths)
            status = latest_run.status.value
            if latest_run.status is ScanRunStatus.FAILED:
                action_label = "Revoir erreur"
                action_href = "#session-runs"
                last_run_summary = (
                    f"Dernier lancement echoue : {latest_run.command_count} commande(s), "
                    f"{latest_run.finding_count} constat(s), {evidence_count} preuve(s)."
                )
            else:
                action_label = "Voir resultats"
                action_href = "#session-runs"
                last_run_summary = (
                    f"Dernier lancement termine : {latest_run.command_count} commande(s), "
                    f"{latest_run.finding_count} constat(s), {evidence_count} preuve(s)."
                )
            if latest_run.error:
                last_run_summary = f"{last_run_summary} Erreur : {latest_run.error}"
            queue.append(
                AnalysisSessionExecutionQueueItem(
                    check=plan.check,
                    label=plan.label,
                    status=status,
                    readiness_detail=plan.detail,
                    planned_command_count=planned_command_count,
                    last_run_status=latest_run.status.value,
                    last_run_summary=last_run_summary,
                    finding_count=latest_run.finding_count,
                    evidence_count=evidence_count,
                    action_label=action_label,
                    action_href=action_href,
                )
            )
            continue

        if plan.status == "ready":
            status = "ready"
            action_label = "Lancer controle"
            action_href = "#session-services"
            last_run_status = "missing"
            last_run_summary = "Aucun lancement enregistre pour ce controle."
        elif plan.status == "blocked":
            status = "blocked"
            action_label = "Corriger preparation"
            action_href = "#session-services"
            last_run_status = "blocked"
            last_run_summary = "Controle bloque tant que la preparation n'est pas corrigee."
        else:
            status = "warning"
            action_label = "Verifier controle"
            action_href = "#session-services"
            last_run_status = "missing"
            last_run_summary = "Controle a verifier avant lancement."

        queue.append(
            AnalysisSessionExecutionQueueItem(
                check=plan.check,
                label=plan.label,
                status=status,
                readiness_detail=plan.detail,
                planned_command_count=planned_command_count,
                last_run_status=last_run_status,
                last_run_summary=last_run_summary,
                finding_count=0,
                evidence_count=0,
                action_label=action_label,
                action_href=action_href,
            )
        )
    return queue


def plain_finding_explanation(finding: Finding) -> str:
    text = " ".join(
        [
            finding.title,
            finding.category,
            finding.source_module,
            finding.proof,
            finding.risk,
        ]
    ).lower()

    if any(marker in text for marker in ["rdp", "3389", "administr"]):
        return (
            "Un service d'administration distant semble accessible sur la cible. "
            "Il doit etre limite aux sources autorisees et surveille."
        )
    if any(marker in text for marker in ["smb", "445", "share"]):
        return (
            "Un service de partage de fichiers est visible. Une mauvaise "
            "configuration peut exposer des fichiers ou des informations internes."
        )
    if any(marker in text for marker in ["ldap", "389", "active directory"]):
        return (
            "Le service d'annuaire repond aux controles. Il faut verifier que les "
            "informations exposees et les signatures LDAP respectent la politique client."
        )
    if any(marker in text for marker in ["tls", "ssl", "certificate", "certificat"]):
        return (
            "La configuration TLS ou certificat presente un point a corriger pour "
            "eviter les protocoles faibles ou les erreurs de confiance."
        )
    if any(marker in text for marker in ["http", "header", "web"]):
        return (
            "Le service web expose une configuration de securite incomplete. "
            "Des en-tetes ou restrictions peuvent reduire le risque cote navigateur."
        )
    if any(marker in text for marker in ["cve", "kev", "vulnerab"]):
        return (
            "Une vulnerabilite connue est candidate sur cet actif. Le produit et "
            "la version doivent etre confirmes avant restitution client."
        )
    if any(marker in text for marker in ["dns", "spf", "dmarc", "dkim", "mail"]):
        return (
            "La configuration DNS ou mail doit etre renforcee pour limiter "
            "l'usurpation, les erreurs de routage ou les faiblesses de domaine."
        )
    return (
        "Ce constat signale un point de configuration ou d'exposition a verifier "
        "sur la cible avant restitution."
    )


def plain_finding_impact(finding: Finding) -> str:
    if finding.severity in {Severity.CRITICAL, Severity.HIGH}:
        return (
            "Impact prioritaire : une exploitation ou une exposition non maitrisee "
            "peut avoir un effet direct sur la securite du client."
        )
    if finding.severity is Severity.MEDIUM:
        return (
            "Impact modere : le risque doit etre corrige ou planifie, surtout si "
            "l'actif est expose ou sensible."
        )
    if finding.severity is Severity.LOW:
        return (
            "Impact faible : le point contribue a l'hygiene globale et doit etre "
            "traite dans le suivi de maintenance."
        )
    return (
        "Information : ce point aide a documenter l'etat de securite et les "
        "controles de suivi."
    )


def analysis_session_step(
    label: str,
    ready: bool,
    warning: bool,
    detail: str,
    weight: int,
    action_label: str,
    action_href: str,
) -> AnalysisSessionStep:
    if ready:
        status = "ready"
        earned = weight
    elif warning:
        status = "warning"
        earned = max(weight // 2, 1)
    else:
        status = "missing"
        earned = 0
    return AnalysisSessionStep(
        label=label,
        status=status,
        detail=detail,
        weight=weight,
        earned=earned,
        action_label=action_label,
        action_href=action_href,
    )


def analysis_session_run_step(
    completed_count: int,
    failed_count: int,
    selected_count: int,
) -> AnalysisSessionStep:
    weight = 25
    if selected_count == 0:
        return AnalysisSessionStep(
            label="Execution",
            status="missing",
            detail="No selected service can be executed yet.",
            weight=weight,
            earned=0,
            action_label="Select Services",
            action_href="#check-selection",
        )
    earned = round(weight * (completed_count / selected_count))
    if failed_count:
        status = "blocked"
        detail = f"{failed_count} failed service(s) need review before delivery."
    elif completed_count == selected_count:
        status = "ready"
        detail = f"All {selected_count} selected service(s) completed."
    elif completed_count:
        status = "warning"
        detail = f"{completed_count}/{selected_count} selected service(s) completed."
    else:
        status = "missing"
        detail = "No selected service has been launched yet."
    return AnalysisSessionStep(
        label="Execution",
        status=status,
        detail=detail,
        weight=weight,
        earned=earned,
        action_label="Open Launch Center",
        action_href="#scan-plan",
    )


def analysis_session_status(steps: list[AnalysisSessionStep]) -> str:
    if any(step.status == "blocked" for step in steps):
        return "blocked"
    if any(step.status in {"missing", "warning"} for step in steps):
        return "warning"
    return "ready"


def analysis_current_phase(steps: list[AnalysisSessionStep]) -> str:
    for step in steps:
        if step.status in {"blocked", "missing", "warning"}:
            return step.label
    return "Handoff"


def analysis_session_title(status: str, progress_percent: int) -> str:
    if status == "ready":
        return "Session ready for customer handoff"
    if status == "blocked":
        return "Session blocked before delivery"
    if progress_percent >= 70:
        return "Session mostly complete"
    if progress_percent >= 35:
        return "Session in progress"
    return "Session preparation started"


def session_target_summary_item(item: ScopeItem) -> str:
    return f"{item.environment.value}:{item.type.value}:{item.value}"


def scan_launch_checklist(scan_plans: list[ScanPlanPreview]) -> list[ScanLaunchChecklistItem]:
    return [scan_launch_checklist_item(plan) for plan in scan_plans]


def scan_launch_checklist_item(plan: ScanPlanPreview) -> ScanLaunchChecklistItem:
    if plan.status == "ready":
        return ScanLaunchChecklistItem(
            label=plan.label,
            status="ready",
            command_count=len(plan.commands),
            detail="Commands are visible and explicit confirmation remains required.",
            action_label="Review Commands",
            action_href="#scan-plan",
        )
    return ScanLaunchChecklistItem(
        label=plan.label,
        status=plan.status,
        command_count=len(plan.commands),
        detail=plan.detail,
        action_label="Resolve Readiness",
        action_href="#mission-readiness",
    )


def report_delivery_summary(
    authorization_briefs: list[AuthorizationBriefLink],
    reports: list[GeneratedReportLink],
    mission_export: MissionExportLink | None,
) -> ReportDeliverySummary:
    report_formats = {report.format for report in reports}
    items = [
        ReportDeliveryItem(
            label="Authorization brief",
            status="ready" if authorization_briefs else "missing",
            detail=(
                f"{len(authorization_briefs)} file(s) generated."
                if authorization_briefs
                else "Generate the authorization brief before handoff."
            ),
            action_label="Generate Brief",
            action_href="#reports",
        )
    ]
    items.extend(report_delivery_report_items(report_formats))
    items.append(report_delivery_package_item(mission_export))

    ready_count = len([item for item in items if item.status == "ready"])
    if ready_count == len(items):
        status = "ready"
        detail = "All expected handoff deliverables are available."
        action_label = "Download Package"
    elif report_formats:
        status = "warning"
        detail = f"{ready_count}/{len(items)} deliverable item(s) are ready."
        action_label = "Complete Handoff"
    else:
        status = "missing"
        detail = "Generate reviewed reports before building the customer package."
        action_label = "Generate Reports"

    return ReportDeliverySummary(
        status=status,
        detail=detail,
        action_label=action_label,
        action_href="#reports",
        ready_count=ready_count,
        total_count=len(items),
        items=items,
    )


def report_delivery_report_items(report_formats: set[str]) -> list[ReportDeliveryItem]:
    labels = {
        ReportFormat.JSON: "JSON tracking report",
        ReportFormat.MARKDOWN: "Markdown technical report",
        ReportFormat.HTML: "HTML review report",
        ReportFormat.PDF: "PDF customer report",
    }
    return [
        ReportDeliveryItem(
            label=labels[report_format],
            status="ready" if report_format.value in report_formats else "missing",
            detail=(
                f"{report_format.value} file is available."
                if report_format.value in report_formats
                else f"{report_format.value} file is missing."
            ),
            action_label="Generate Reports",
            action_href="#reports",
        )
        for report_format in MISSION_REPORT_FORMATS
    ]


def report_delivery_package_item(
    mission_export: MissionExportLink | None,
) -> ReportDeliveryItem:
    if mission_export is None:
        return ReportDeliveryItem(
            label="Mission ZIP package",
            status="missing",
            detail="Generate the package after reports are reviewed.",
            action_label="Generate Package",
            action_href="#reports",
        )
    if mission_export.has_integrity_issues:
        return ReportDeliveryItem(
            label="Mission ZIP package",
            status="warning",
            detail=mission_export.integrity_detail,
            action_label="Review Package",
            action_href="#reports",
        )
    return ReportDeliveryItem(
        label="Mission ZIP package",
        status="ready",
        detail=mission_export.integrity_detail,
        action_label="Download Package",
        action_href="#reports",
    )


def customer_handoff_summary(
    mission: Mission,
    reports: list[GeneratedReportLink],
    mission_export: MissionExportLink | None,
) -> CustomerHandoffSummary:
    report_formats = {report.format for report in reports}
    items = [
        CustomerHandoffItem(
            label="Customer PDF",
            status="ready" if ReportFormat.PDF.value in report_formats else "missing",
            detail=(
                "PDF report is ready for client review."
                if ReportFormat.PDF.value in report_formats
                else "Generate the PDF report before customer delivery."
            ),
        ),
        CustomerHandoffItem(
            label="JSON tracking",
            status="ready" if ReportFormat.JSON.value in report_formats else "missing",
            detail=(
                "JSON tracking report is ready for remediation follow-up."
                if ReportFormat.JSON.value in report_formats
                else "Generate the JSON report for remediation tracking."
            ),
        ),
        customer_handoff_package_item(mission_export),
        CustomerHandoffItem(
            label="Recipients",
            status="ready" if mission.report_recipients else "missing",
            detail=(
                mission.report_recipients
                if mission.report_recipients
                else "Add report recipients in mission setup."
            ),
        ),
        CustomerHandoffItem(
            label="Evidence retention",
            status="ready" if mission.evidence_retention_days is not None else "missing",
            detail=(
                f"{mission.evidence_retention_days} day(s) recorded."
                if mission.evidence_retention_days is not None
                else "Record the evidence retention period before handoff."
            ),
        ),
    ]
    ready_count = len([item for item in items if item.status == "ready"])
    if ready_count == len(items):
        status = "ready"
        title = "Customer handoff ready"
        detail = (
            "PDF, JSON tracking, package, recipients, and evidence retention "
            "are ready for controlled delivery."
        )
        action_label = "Download Package"
    elif any(item.status in {"ready", "warning"} for item in items):
        status = "warning"
        title = "Customer handoff needs review"
        detail = (
            f"{ready_count}/{len(items)} handoff item(s) are ready. "
            "Complete the missing items before customer delivery."
        )
        action_label = "Complete Handoff"
    else:
        status = "missing"
        title = "Customer handoff not ready"
        detail = "Generate reviewed reports and record delivery details before handoff."
        action_label = "Generate Reports"

    return CustomerHandoffSummary(
        status=status,
        title=title,
        detail=detail,
        action_label=action_label,
        action_href="#reports",
        ready_count=ready_count,
        total_count=len(items),
        items=items,
    )


def customer_handoff_package_item(
    mission_export: MissionExportLink | None,
) -> CustomerHandoffItem:
    if mission_export is None:
        return CustomerHandoffItem(
            label="Mission package",
            status="missing",
            detail="Generate the ZIP package after reports are reviewed.",
        )
    if mission_export.has_integrity_issues:
        return CustomerHandoffItem(
            label="Mission package",
            status="warning",
            detail=mission_export.integrity_detail,
        )
    return CustomerHandoffItem(
        label="Mission package",
        status="ready",
        detail=mission_export.integrity_detail,
    )


def mission_go_no_go_summary(
    mission: Mission,
    scope_intake: ScopeIntakeSummary,
    scan_run_outcome: ScanRunOutcomeSummary,
    vulnerability: VulnerabilitySummary,
    report_delivery: ReportDeliverySummary,
    readiness_items: list[ReadinessItem],
) -> MissionGoNoGoSummary:
    readiness = {item.label: item for item in readiness_items}
    items = [
        go_no_go_authorization_item(mission),
        go_no_go_scope_item(scope_intake),
        go_no_go_scan_evidence_item(scan_run_outcome),
        go_no_go_vulnerability_item(vulnerability),
        go_no_go_finding_review_item(readiness["Finding Review"]),
        go_no_go_delivery_item(report_delivery),
    ]
    ready_count = len([item for item in items if item.status == "ready"])
    first_attention = next(
        (item for item in items if item.status in {"blocked", "missing", "warning"}),
        None,
    )
    if any(item.status == "blocked" for item in items):
        status = "blocked"
        decision = "No-Go"
        detail = "Hard blockers remain before this mission can be handed off."
    elif first_attention is not None:
        status = "warning"
        decision = "Review"
        detail = "Mission is usable, but attention items remain before customer handoff."
    else:
        status = "ready"
        decision = "Go"
        detail = "Mission is ready for pilot handoff."

    return MissionGoNoGoSummary(
        status=status,
        decision=decision,
        detail=detail,
        action_label=first_attention.action_label if first_attention else "Open Reports",
        action_href=first_attention.action_href if first_attention else "#reports",
        ready_count=ready_count,
        total_count=len(items),
        items=items,
    )


def go_no_go_authorization_item(mission: Mission) -> MissionGoNoGoItem:
    if mission.is_authorized:
        return MissionGoNoGoItem(
            label="Authorization",
            status="ready",
            detail="Written authorization is recorded.",
            action_label="Review Setup",
            action_href="#mission-setup",
        )
    return MissionGoNoGoItem(
        label="Authorization",
        status="blocked",
        detail="Written authorization is required before handoff.",
        action_label="Update Setup",
        action_href="#mission-setup",
    )


def go_no_go_scope_item(scope_intake: ScopeIntakeSummary) -> MissionGoNoGoItem:
    status = "blocked" if scope_intake.status in {"blocked", "missing"} else scope_intake.status
    return MissionGoNoGoItem(
        label="Scope and services",
        status=status,
        detail=scope_intake.detail,
        action_label=scope_intake.action_label,
        action_href=scope_intake.action_href,
    )


def go_no_go_scan_evidence_item(scan_run_outcome: ScanRunOutcomeSummary) -> MissionGoNoGoItem:
    if scan_run_outcome.run_count == 0:
        return MissionGoNoGoItem(
            label="Scan evidence",
            status="warning",
            detail="No guarded scan run is recorded yet.",
            action_label="Open Scan Plan",
            action_href="#scan-plan",
        )
    if scan_run_outcome.status == "failed":
        return MissionGoNoGoItem(
            label="Scan evidence",
            status="blocked",
            detail=scan_run_outcome.detail,
            action_label="Review Error",
            action_href="#run-monitor",
        )
    return MissionGoNoGoItem(
        label="Scan evidence",
        status="ready",
        detail=scan_run_outcome.detail,
        action_label=scan_run_outcome.action_label,
        action_href=scan_run_outcome.action_href,
    )


def go_no_go_vulnerability_item(vulnerability: VulnerabilitySummary) -> MissionGoNoGoItem:
    if vulnerability.status == "missing":
        return MissionGoNoGoItem(
            label="CVE/KEV review",
            status="warning",
            detail="No reviewed local CVE/KEV catalog is imported.",
            action_label="Import Catalog",
            action_href="#vulnerabilities",
        )
    return MissionGoNoGoItem(
        label="CVE/KEV review",
        status=vulnerability.status,
        detail=vulnerability.detail,
        action_label=vulnerability.action_label,
        action_href=vulnerability.action_href,
    )


def go_no_go_finding_review_item(item: ReadinessItem) -> MissionGoNoGoItem:
    return MissionGoNoGoItem(
        label="Finding review",
        status=item.status,
        detail=item.detail,
        action_label=item.action_label or "Review Findings",
        action_href=item.action_href or "#findings",
    )


def go_no_go_delivery_item(report_delivery: ReportDeliverySummary) -> MissionGoNoGoItem:
    status = "blocked" if report_delivery.status == "missing" else report_delivery.status
    return MissionGoNoGoItem(
        label="Report delivery",
        status=status,
        detail=report_delivery.detail,
        action_label=report_delivery.action_label,
        action_href=report_delivery.action_href,
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
    blocked_preparation_count = len(
        [item for item in preparation_items if item.status == "blocked"]
    )
    warning_preparation_count = len(
        [item for item in preparation_items if item.status == "warning"]
    )
    ready_preparation_count = len(
        [item for item in preparation_items if item.status == "ready"]
    )
    technician_workflow_steps = build_dashboard_technician_workflow_steps(
        onboarding_steps=onboarding_steps,
        ready_preparation_count=ready_preparation_count,
        warning_preparation_count=warning_preparation_count,
        blocked_preparation_count=blocked_preparation_count,
        total_findings=total_findings,
        high_or_critical_findings=high_or_critical,
    )

    return DashboardView(
        clients=client_rows,
        missions=mission_rows,
        preparation_items=preparation_items,
        technician_workflow_steps=technician_workflow_steps,
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
        blocked_preparation_count=blocked_preparation_count,
        warning_preparation_count=warning_preparation_count,
        ready_preparation_count=ready_preparation_count,
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
    scope_intake = scope_intake_summary(mission)
    scan_run_outcome = scan_run_outcome_summary(scan_runs, findings)
    report_delivery = report_delivery_summary(
        authorization_briefs=authorization_briefs,
        reports=reports,
        mission_export=mission_export,
    )
    customer_handoff = customer_handoff_summary(
        mission=mission,
        reports=reports,
        mission_export=mission_export,
    )
    session_dashboard = analysis_session_dashboard(
        mission=mission,
        findings=findings,
        scan_plans=scan_plans,
        scan_runs=scan_runs,
        reports=reports,
        mission_export=mission_export,
        vulnerability=vulnerability,
    )

    return MissionView(
        mission=mission_row(mission, findings, client_name_by_id(store)),
        session_dashboard=session_dashboard,
        go_no_go=mission_go_no_go_summary(
            mission=mission,
            scope_intake=scope_intake,
            scan_run_outcome=scan_run_outcome,
            vulnerability=vulnerability,
            report_delivery=report_delivery,
            readiness_items=readiness_items,
        ),
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
        quick_read=mission_quick_read(summary),
        activity_log_url=mission_activity_log_url(mission.id),
        scope=[scope_row(item) for item in mission.scope],
        scope_intake=scope_intake,
        findings=[finding_row(finding) for finding in sorted_findings(findings)],
        finding_dispositions=finding_disposition_rows(findings),
        counter_test_summary=counter_test_summary_rows(findings),
        counter_test_items=[counter_test_row(finding) for finding in counter_test_findings(findings)],
        activity_events=[activity_event_row(event) for event in activity_events],
        check_selection=check_selection,
        scan_runs=[scan_run_row(run) for run in scan_runs],
        scan_run_outcome=scan_run_outcome,
        remediation_items=remediation_plan(findings),
        executive_summary=str(summary["executive_summary"]),
        authorization_briefs=authorization_briefs,
        reports=reports,
        report_delivery=report_delivery,
        customer_handoff=customer_handoff,
        mission_export=mission_export,
        readiness_items=readiness_items,
        scan_plans=scan_plans,
        vulnerability_summary=vulnerability,
        vulnerability_review_items=vulnerability_review_items(
            catalog_count=len(vulnerability_catalog.advisories),
            matches=vulnerability_matches,
            findings=findings,
        ),
        vulnerability_catalog_count=len(vulnerability_catalog.advisories),
        vulnerability_matches=[
            vulnerability_match_row(match) for match in vulnerability_matches
        ],
        template_guidance=template_guidance(mission),
    )


def severity_class(value: str) -> str:
    allowed = {"critical", "high", "medium", "low", "info"}
    return value if value in allowed else "info"


def vulnerability_review_items(
    catalog_count: int,
    matches: list[VulnerabilityMatch],
    findings: list[Finding],
) -> list[VulnerabilityReviewItem]:
    source_finding_count = len(
        [finding for finding in findings if finding.source_module != CATALOG_FINDING_SOURCE]
    )
    stored_candidate_count = len(
        [finding for finding in findings if finding.source_module == CATALOG_FINDING_SOURCE]
    )
    known_exploited_count = len([match for match in matches if match.advisory.known_exploited])
    return [
        vulnerability_catalog_review_item(catalog_count),
        vulnerability_evidence_review_item(source_finding_count),
        vulnerability_candidate_review_item(
            catalog_count=catalog_count,
            source_finding_count=source_finding_count,
            match_count=len(matches),
            stored_candidate_count=stored_candidate_count,
        ),
        vulnerability_kev_review_item(known_exploited_count),
    ]


def vulnerability_catalog_review_item(catalog_count: int) -> VulnerabilityReviewItem:
    if catalog_count:
        return VulnerabilityReviewItem(
            label="Reviewed catalog",
            status="ready",
            detail=f"{catalog_count} advisory item(s) are available locally.",
            action_label="Review Catalog",
            action_href="#vulnerabilities",
        )
    return VulnerabilityReviewItem(
        label="Reviewed catalog",
        status="missing",
        detail="Import a reviewed local CVE/KEV JSON catalog before correlation.",
        action_label="Import Catalog",
        action_href="#vulnerabilities",
    )


def vulnerability_evidence_review_item(source_finding_count: int) -> VulnerabilityReviewItem:
    if source_finding_count:
        return VulnerabilityReviewItem(
            label="Source evidence",
            status="ready",
            detail=f"{source_finding_count} source finding(s) can be correlated.",
            action_label="Review Findings",
            action_href="#findings",
        )
    return VulnerabilityReviewItem(
        label="Source evidence",
        status="missing",
        detail="Run or add service/version findings before CVE correlation.",
        action_label="Open Scan Plan",
        action_href="#scan-plan",
    )


def vulnerability_candidate_review_item(
    catalog_count: int,
    source_finding_count: int,
    match_count: int,
    stored_candidate_count: int,
) -> VulnerabilityReviewItem:
    if catalog_count == 0 or source_finding_count == 0:
        return VulnerabilityReviewItem(
            label="Candidate findings",
            status="missing",
            detail="Catalog and source findings are required before candidates can be stored.",
            action_label="Review Prerequisites",
            action_href="#vulnerabilities",
        )
    if match_count == 0:
        return VulnerabilityReviewItem(
            label="Candidate findings",
            status="ready",
            detail="No candidate CVE/KEV match was detected for the current evidence.",
            action_label="Review Findings",
            action_href="#findings",
        )
    if stored_candidate_count >= match_count:
        return VulnerabilityReviewItem(
            label="Candidate findings",
            status="ready",
            detail=f"{stored_candidate_count}/{match_count} candidate finding(s) are stored.",
            action_label="Review Findings",
            action_href="#findings",
        )
    return VulnerabilityReviewItem(
        label="Candidate findings",
        status="warning",
        detail=f"{stored_candidate_count}/{match_count} candidate finding(s) are stored.",
        action_label="Store Candidate Findings",
        action_href="#vulnerabilities",
    )


def vulnerability_kev_review_item(known_exploited_count: int) -> VulnerabilityReviewItem:
    if known_exploited_count:
        return VulnerabilityReviewItem(
            label="Known exploited attention",
            status="warning",
            detail=f"{known_exploited_count} KEV candidate(s) need priority review.",
            action_label="Review KEV",
            action_href="#vulnerabilities",
        )
    return VulnerabilityReviewItem(
        label="Known exploited attention",
        status="ready",
        detail="No KEV candidate is currently matched.",
        action_label="Review Summary",
        action_href="#vulnerabilities",
    )


def vulnerability_match_row(match: VulnerabilityMatch) -> VulnerabilityMatchRow:
    priority_label, priority_reason = vulnerability_priority(match)
    return VulnerabilityMatchRow(
        cve_id=match.advisory.cve_id,
        title=match.advisory.title,
        severity=match.advisory.severity.value,
        known_exploited=match.advisory.known_exploited,
        priority_label=priority_label,
        priority_reason=priority_reason,
        affected_asset=match.finding.affected_asset,
        matched_finding_id=match.finding.id,
        matched_terms=", ".join(match.matched_terms),
        risk=match.advisory.risk,
        remediation=match.advisory.remediation,
        counter_test=match.advisory.counter_test,
        validation_steps=vulnerability_validation_steps(match),
        references=tuple(match.advisory.references),
    )


def vulnerability_priority(match: VulnerabilityMatch) -> tuple[str, str]:
    if match.advisory.known_exploited:
        return (
            "Priority 1",
            "Known exploited advisory: validate this candidate first and plan "
            "urgent remediation if confirmed.",
        )
    if match.advisory.severity in {Severity.CRITICAL, Severity.HIGH}:
        return (
            "Priority 2",
            "Critical or high severity advisory: validate the exposed version before standard findings.",
        )
    return (
        "Priority 3",
        "Candidate advisory: validate during the normal remediation review.",
    )


def vulnerability_validation_steps(match: VulnerabilityMatch) -> tuple[str, ...]:
    return (
        f"Confirm that {match.finding.affected_asset} is still in the approved scope.",
        "Confirm the service or version evidence before treating this as exploitable.",
        "Review the advisory reference and vendor remediation before customer communication.",
        "If confirmed, store the candidate finding and track remediation.",
        f"After remediation, run this counter-test: {match.advisory.counter_test}",
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
