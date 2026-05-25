"""Mission readiness and safe scan plan previews for the local web UI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from media_security_audit.models import AuditCheck, Finding, FindingStatus, Mission
from media_security_audit.scanners.dns_mail import approved_dns_domains, dns_mail_query_plan
from media_security_audit.scanners.http_headers import approved_http_targets
from media_security_audit.scanners.ldap import LdapCommandBuilder, render_ldap_command
from media_security_audit.scanners.nmap import NmapCommandBuilder, render_command
from media_security_audit.scanners.smb import SmbCommandBuilder, render_smb_command
from media_security_audit.scanners.testssl import TestsslCommandBuilder, render_testssl_command


@dataclass(frozen=True)
class ReadinessItem:
    label: str
    status: str
    detail: str
    action_label: str = ""
    action_href: str = ""


@dataclass(frozen=True)
class ScanPlanPreview:
    label: str
    status: str
    detail: str
    commands: list[str]


def build_readiness_items(
    mission: Mission,
    findings: list[Finding],
    generated_report_count: int,
) -> list[ReadinessItem]:
    approved_scope_count = len([item for item in mission.scope if item.approved and not item.excluded])
    new_finding_count = len([finding for finding in findings if finding.status == FindingStatus.NEW])

    return [
        _authorization_item(mission),
        _approved_scope_item(approved_scope_count),
        _check_selection_item(mission),
        _finding_review_item(len(findings), new_finding_count),
        _report_item(generated_report_count),
    ]


def build_scan_plan_previews(mission: Mission) -> list[ScanPlanPreview]:
    plan_builders = {
        AuditCheck.NMAP: _nmap_preview,
        AuditCheck.HTTP_HEADERS: _http_preview,
        AuditCheck.DNS_MAIL: _dns_mail_preview,
        AuditCheck.TLS: _tls_preview,
        AuditCheck.SMB: _smb_preview,
        AuditCheck.LDAP: _ldap_preview,
    }
    if not mission.selected_checks:
        return [_blocked_plan("Check Selection", "No audit check is selected for this mission.")]
    return [plan_builders[check](mission) for check in mission.selected_checks]


def _authorization_item(mission: Mission) -> ReadinessItem:
    if mission.is_authorized:
        return ReadinessItem(
            label="Authorization",
            status="ready",
            detail=f"Reference: {mission.authorization_reference}",
        )
    return ReadinessItem(
        label="Authorization",
        status="blocked",
        detail="Missing written authorization reference.",
        action_label="Update Setup",
        action_href="#mission-setup",
    )


def _approved_scope_item(approved_scope_count: int) -> ReadinessItem:
    if approved_scope_count:
        return ReadinessItem(
            label="Approved Scope",
            status="ready",
            detail=f"{approved_scope_count} approved target(s).",
        )
    return ReadinessItem(
        label="Approved Scope",
        status="blocked",
        detail="No approved target is available.",
        action_label="Review Scope",
        action_href="#scope",
    )


def _check_selection_item(mission: Mission) -> ReadinessItem:
    if mission.selected_checks:
        return ReadinessItem(
            label="Check Selection",
            status="ready",
            detail=f"{len(mission.selected_checks)} audit check(s) selected.",
        )
    return ReadinessItem(
        label="Check Selection",
        status="blocked",
        detail="No audit check is selected.",
        action_label="Select Checks",
        action_href="#check-selection",
    )


def _finding_review_item(total_findings: int, new_finding_count: int) -> ReadinessItem:
    if total_findings == 0:
        return ReadinessItem(
            label="Finding Review",
            status="warning",
            detail="No stored finding yet.",
            action_label="Open Findings",
            action_href="#findings",
        )
    if new_finding_count:
        return ReadinessItem(
            label="Finding Review",
            status="warning",
            detail=f"{new_finding_count} finding(s) still have new status.",
            action_label="Review Findings",
            action_href="#findings",
        )
    return ReadinessItem(
        label="Finding Review",
        status="ready",
        detail="Stored findings have been reviewed.",
    )


def _report_item(generated_report_count: int) -> ReadinessItem:
    if generated_report_count:
        return ReadinessItem(
            label="Reports",
            status="ready",
            detail=f"{generated_report_count} generated export(s).",
        )
    return ReadinessItem(
        label="Reports",
        status="warning",
        detail="No persistent report export yet.",
        action_label="Open Reports",
        action_href="#reports",
    )


def _nmap_preview(mission: Mission) -> ScanPlanPreview:
    try:
        commands = NmapCommandBuilder().build_for_scope(
            mission.scope,
            output_dir=Path("runs") / mission.id / "evidence",
        )
    except ValueError as error:
        return _blocked_plan("Nmap", str(error))

    if not commands:
        return _blocked_plan("Nmap", "No approved Nmap-compatible target.")

    rendered = [render_command(command) for command in commands]
    return ScanPlanPreview(
        label="Nmap",
        status="ready",
        detail=f"{len(rendered)} planned command(s).",
        commands=rendered,
    )


def _http_preview(mission: Mission) -> ScanPlanPreview:
    try:
        targets = approved_http_targets(mission.scope)
    except ValueError as error:
        return _blocked_plan("HTTP Headers", str(error))

    if not targets:
        return _blocked_plan("HTTP Headers", "No approved URL target.")

    return ScanPlanPreview(
        label="HTTP Headers",
        status="ready",
        detail=f"{len(targets)} approved URL target(s).",
        commands=[f"HEAD/GET {target}" for target in targets],
    )


def _dns_mail_preview(mission: Mission) -> ScanPlanPreview:
    try:
        domains = approved_dns_domains(mission.scope)
        queries = dns_mail_query_plan(domains)
    except ValueError as error:
        return _blocked_plan("DNS/Mail", str(error))

    if not queries:
        return _blocked_plan("DNS/Mail", "No approved domain target.")

    return ScanPlanPreview(
        label="DNS/Mail",
        status="ready",
        detail=f"{len(queries)} planned TXT lookup(s).",
        commands=queries,
    )


def _tls_preview(mission: Mission) -> ScanPlanPreview:
    try:
        commands = TestsslCommandBuilder().build_for_scope(
            mission.scope,
            output_dir=Path("runs") / mission.id / "evidence",
        )
    except ValueError as error:
        return _blocked_plan("TLS", str(error))

    if not commands:
        return _blocked_plan("TLS", "No approved TLS-compatible target.")

    rendered = [render_testssl_command(command) for command in commands]
    return ScanPlanPreview(
        label="TLS",
        status="ready",
        detail=f"{len(rendered)} planned testssl.sh command(s).",
        commands=rendered,
    )


def _smb_preview(mission: Mission) -> ScanPlanPreview:
    try:
        commands = SmbCommandBuilder().build_for_scope(mission.scope)
    except ValueError as error:
        return _blocked_plan("SMB", str(error))

    if not commands:
        return _blocked_plan("SMB", "No approved SMB-compatible target.")

    rendered = [render_smb_command(command) for command in commands]
    return ScanPlanPreview(
        label="SMB",
        status="ready",
        detail=f"{len(rendered)} planned smbclient command(s).",
        commands=rendered,
    )


def _ldap_preview(mission: Mission) -> ScanPlanPreview:
    try:
        commands = LdapCommandBuilder().build_for_scope(mission.scope)
    except ValueError as error:
        return _blocked_plan("LDAP", str(error))

    if not commands:
        return _blocked_plan("LDAP", "No approved LDAP-compatible target.")

    rendered = [render_ldap_command(command) for command in commands]
    return ScanPlanPreview(
        label="LDAP",
        status="ready",
        detail=f"{len(rendered)} planned ldapsearch command(s).",
        commands=rendered,
    )


def _blocked_plan(label: str, detail: str) -> ScanPlanPreview:
    return ScanPlanPreview(label=label, status="blocked", detail=detail, commands=[])
