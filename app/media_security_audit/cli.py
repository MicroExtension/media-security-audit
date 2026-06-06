"""CLI entrypoint for MEDIA Security Audit Platform."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from pydantic import ValidationError

from media_security_audit import __version__
from media_security_audit.deployment_preflight import (
    build_deployment_preflight,
    format_deployment_preflight,
    format_deployment_preflight_json,
    preflight_exit_code,
)
from media_security_audit.mission_readiness import (
    build_mission_readiness_payload,
    format_mission_readiness_json,
    format_mission_readiness_text,
    mission_readiness_exit_code,
)
from media_security_audit.models import (
    AuditCheck,
    AuditType,
    Client,
    Finding,
    ReportFormat,
    ScanRun,
    ScanRunStatus,
    ScopeEnvironment,
    ScopeItem,
    ScopeType,
    Severity,
    utc_now,
)
from media_security_audit.reports import MISSION_REPORT_FORMATS, write_report
from media_security_audit.sample_data import sample_findings, sample_mission
from media_security_audit.scanners.dns_mail import (
    DnsPythonTxtResolver,
    DnsTxtResolver,
    approved_dns_domains,
    audit_dns_mail_domain,
    dns_mail_query_plan,
)
from media_security_audit.scanners.http_headers import (
    HttpFetcher,
    HttpHeaderFetcher,
    approved_http_targets,
    audit_http_headers,
)
from media_security_audit.scanners.ldap import (
    LdapCommandBuilder,
    LdapExecutionResult,
    LdapExecutor,
    findings_from_root_dse,
    parse_ldap_root_dse,
    render_ldap_command,
)
from media_security_audit.scanners.nmap import (
    NmapCommandBuilder,
    NmapExecutionResult,
    NmapExecutor,
    findings_from_hosts,
    parse_nmap_xml_file,
    render_command,
)
from media_security_audit.scanners.smb import (
    SmbCommandBuilder,
    SmbExecutionResult,
    SmbExecutor,
    findings_from_smb_shares,
    parse_smbclient_listing,
    render_smb_command,
)
from media_security_audit.scanners.testssl import (
    TestsslCommandBuilder,
    TestsslExecutionResult,
    TestsslExecutor,
    parse_testssl_json_file,
    render_testssl_command,
)
from media_security_audit.scan_plan_exports import (
    format_scan_plan_json as render_scan_plan_json,
    format_scan_plan_text as render_scan_plan_text,
    scan_plan_payload as build_scan_plan_payload,
)
from media_security_audit.storage import JsonStore
from media_security_audit.vulnerability_catalog import (
    correlate_vulnerability_catalog,
    format_vulnerability_catalog_json,
    format_vulnerability_catalog_text,
    format_vulnerability_correlation_json,
    format_vulnerability_correlation_text,
    import_vulnerability_catalog,
    load_vulnerability_catalog,
    store_vulnerability_findings_for_mission,
)
from media_security_audit.web_exports import (
    build_mission_export_inventory,
    format_mission_export_inventory_json,
    format_mission_export_inventory_text,
    format_mission_export_manifest_json,
    format_mission_export_manifest_markdown,
    format_mission_export_verification_json,
    format_mission_export_verification_text,
    mission_export_verification_exit_code,
    mission_export_path,
    read_mission_export_manifest,
    verify_mission_export,
)
from media_security_audit.web_readiness import ScanPlanPreview, build_scan_plan_previews


def generate_sample_reports(output: Path) -> None:
    mission = sample_mission()
    findings = sample_findings()
    for report_format in MISSION_REPORT_FORMATS:
        write_report(mission, findings, output, report_format)


def run_web_interface(
    data_dir: Path,
    reports_dir: Path,
    runs_dir: Path = Path("runs"),
    host: str = "127.0.0.1",
    port: int = 8080,
) -> None:
    from media_security_audit.web import run_web_server

    run_web_server(
        data_dir=data_dir,
        reports_dir=reports_dir,
        runs_dir=runs_dir,
        host=host,
        port=port,
    )


def create_client(name: str, data_dir: Path, reference: str | None = None, notes: str | None = None) -> Client:
    store = JsonStore(data_dir)
    return store.create_client(Client(name=name, internal_reference=reference, notes=notes))


def create_mission(
    client_id: str,
    name: str,
    data_dir: Path,
    audit_type: AuditType = AuditType.MIXED,
    authorization_reference: str | None = None,
    authorization_contact: str | None = None,
    authorization_date: date | None = None,
    authorization_expires_at: date | None = None,
    emergency_contact: str | None = None,
    report_recipients: str | None = None,
    evidence_retention_days: int | None = None,
    notes: str | None = None,
):
    from media_security_audit.models import Mission

    store = JsonStore(data_dir)
    return store.create_mission(
        Mission(
            client_id=client_id,
            name=name,
            audit_type=audit_type,
            authorization_reference=authorization_reference,
            authorization_contact=authorization_contact,
            authorization_date=authorization_date,
            authorization_expires_at=authorization_expires_at,
            emergency_contact=emergency_contact,
            report_recipients=report_recipients,
            evidence_retention_days=evidence_retention_days,
            notes=notes,
        )
    )


def add_scope(
    mission_id: str,
    scope_type: ScopeType,
    value: str,
    data_dir: Path,
    environment: ScopeEnvironment = ScopeEnvironment.UNKNOWN,
    approved: bool = False,
    excluded: bool = False,
    notes: str | None = None,
):
    store = JsonStore(data_dir)
    return store.add_scope_item(
        mission_id,
        ScopeItem(
            type=scope_type,
            value=value,
            environment=environment,
            approved=approved,
            excluded=excluded,
            notes=notes,
        ),
    )


def list_scope(mission_id: str, data_dir: Path) -> list[ScopeItem]:
    store = JsonStore(data_dir)
    return store.get_mission(mission_id).scope


def show_mission(mission_id: str, data_dir: Path) -> str:
    store = JsonStore(data_dir)
    mission = store.get_mission(mission_id)
    findings = store.list_findings(mission_id)
    approved_scope = [item for item in mission.scope if item.approved and not item.excluded]
    excluded_scope = [item for item in mission.scope if item.excluded]
    evidence_retention = (
        str(mission.evidence_retention_days)
        if mission.evidence_retention_days is not None
        else "missing"
    )

    return "\n".join(
        [
            f"Mission: {mission.name}",
            f"ID: {mission.id}",
            f"Client ID: {mission.client_id}",
            f"Audit type: {mission.audit_type.value}",
            f"Status: {mission.status.value}",
            f"Authorization: {mission.authorization_reference or 'missing'}",
            f"Authorization contact: {mission.authorization_contact or 'missing'}",
            f"Authorization date: {mission.authorization_date or 'missing'}",
            f"Authorization expires: {mission.authorization_expires_at or 'missing'}",
            f"Emergency contact: {mission.emergency_contact or 'missing'}",
            f"Report recipients: {mission.report_recipients or 'missing'}",
            f"Evidence retention days: {evidence_retention}",
            f"Scope items: {len(mission.scope)}",
            f"Approved scope: {len(approved_scope)}",
            f"Excluded scope: {len(excluded_scope)}",
            f"Findings: {len(findings)}",
        ]
    )


def generate_mission_reports(mission_id: str, data_dir: Path, output: Path | None = None) -> list[Path]:
    store = JsonStore(data_dir)
    mission = store.get_mission(mission_id)
    output_dir = output or Path("runs") / mission.id / "reports"
    findings = store.list_findings(mission_id)
    reports = [
        write_report(mission, findings, output_dir, report_format)
        for report_format in MISSION_REPORT_FORMATS
    ]
    return [Path(report.output_path or "") for report in reports]


def add_finding(
    mission_id: str,
    title: str,
    severity: Severity,
    affected_asset: str,
    category: str,
    proof: str,
    risk: str,
    remediation: str,
    counter_test: str,
    data_dir: Path,
    source_module: str = "manual",
    confidence: float = 0.8,
) -> Finding:
    store = JsonStore(data_dir)
    return store.add_finding(
        mission_id,
        Finding(
            title=title,
            severity=severity,
            affected_asset=affected_asset,
            category=category,
            source_module=source_module,
            proof=proof,
            risk=risk,
            remediation=remediation,
            counter_test=counter_test,
            confidence=confidence,
        ),
    )


def add_sample_findings(mission_id: str, data_dir: Path) -> list[Finding]:
    store = JsonStore(data_dir)
    return store.add_findings(mission_id, sample_findings())


def record_scan_run(
    store: JsonStore,
    mission_id: str,
    check: AuditCheck,
    status: ScanRunStatus,
    command_count: int = 0,
    finding_count: int = 0,
    evidence_paths: list[str] | None = None,
    error: str | None = None,
    metadata: dict[str, str] | None = None,
) -> ScanRun:
    return store.add_scan_run(
        ScanRun(
            mission_id=mission_id,
            check=check,
            status=status,
            completed_at=utc_now(),
            command_count=command_count,
            finding_count=finding_count,
            evidence_paths=evidence_paths or [],
            error=error,
            metadata=metadata or {},
        )
    )


def plan_nmap_scan(
    mission_id: str,
    data_dir: Path,
    output_dir: Path | None = None,
) -> list[list[str]]:
    store = JsonStore(data_dir)
    mission = store.get_mission(mission_id)
    evidence_dir = output_dir or Path("runs") / mission.id / "evidence"
    commands = NmapCommandBuilder().build_for_scope(mission.scope, output_dir=evidence_dir)
    if not commands:
        raise ValueError("no approved Nmap-compatible scope items found")
    return commands


def run_nmap_scan(
    mission_id: str,
    data_dir: Path,
    output_dir: Path | None = None,
    execute: bool = False,
    executor: NmapExecutor | None = None,
) -> tuple[list[NmapExecutionResult], list[Finding]]:
    if not execute:
        raise ValueError("refusing to execute Nmap without --execute; use scan nmap-plan first")

    store = JsonStore(data_dir)
    mission = store.get_mission(mission_id)
    if not mission.is_authorized:
        raise ValueError("mission authorization is required before Nmap execution")
    if not mission.has_approved_scope:
        raise ValueError("approved mission scope is required before Nmap execution")

    evidence_dir = output_dir or Path("runs") / mission.id / "evidence"
    commands = NmapCommandBuilder().build_for_scope(mission.scope, output_dir=evidence_dir)
    if not commands:
        raise ValueError("no approved Nmap-compatible scope items found")

    nmap_executor = executor or NmapExecutor()
    try:
        results = [nmap_executor.run(command) for command in commands]
    except Exception as error:
        record_scan_run(
            store,
            mission_id,
            AuditCheck.NMAP,
            ScanRunStatus.FAILED,
            command_count=len(commands),
            error=str(error),
            metadata={"stage": "execution"},
        )
        raise

    evidence_paths = [
        str(result.output_path)
        for result in results
        if result.output_path is not None
    ]
    failed = [result for result in results if result.exit_code != 0]
    if failed:
        first = failed[0]
        record_scan_run(
            store,
            mission_id,
            AuditCheck.NMAP,
            ScanRunStatus.FAILED,
            command_count=len(commands),
            evidence_paths=evidence_paths,
            error=first.stderr,
            metadata={"exit_code": str(first.exit_code)},
        )
        raise RuntimeError(f"Nmap command failed with exit code {first.exit_code}: {first.stderr}")

    findings: list[Finding] = []
    for result in results:
        if result.output_path is not None and result.output_path.exists():
            findings.extend(findings_from_hosts(parse_nmap_xml_file(result.output_path)))

    stored_findings = store.add_findings(mission_id, findings)
    record_scan_run(
        store,
        mission_id,
        AuditCheck.NMAP,
        ScanRunStatus.COMPLETED,
        command_count=len(commands),
        finding_count=len(stored_findings),
        evidence_paths=evidence_paths,
    )
    return results, stored_findings


def plan_http_headers_audit(mission_id: str, data_dir: Path) -> list[str]:
    store = JsonStore(data_dir)
    mission = store.get_mission(mission_id)
    targets = approved_http_targets(mission.scope)
    if not targets:
        raise ValueError("no approved URL scope items found for HTTP header audit")
    return targets


def run_http_headers_audit(
    mission_id: str,
    data_dir: Path,
    execute: bool = False,
    fetcher: HttpFetcher | None = None,
) -> list[Finding]:
    if not execute:
        raise ValueError("refusing to audit HTTP headers without --execute; use scan http-plan first")

    store = JsonStore(data_dir)
    mission = store.get_mission(mission_id)
    if not mission.is_authorized:
        raise ValueError("mission authorization is required before HTTP header audit")
    if not mission.has_approved_scope:
        raise ValueError("approved mission scope is required before HTTP header audit")

    targets = approved_http_targets(mission.scope)
    if not targets:
        raise ValueError("no approved URL scope items found for HTTP header audit")

    http_fetcher = fetcher or HttpHeaderFetcher().fetch
    findings: list[Finding] = []
    try:
        for target in targets:
            findings.extend(audit_http_headers(http_fetcher(target)))
    except Exception as error:
        record_scan_run(
            store,
            mission_id,
            AuditCheck.HTTP_HEADERS,
            ScanRunStatus.FAILED,
            command_count=len(targets),
            error=str(error),
            metadata={"target_count": str(len(targets))},
        )
        raise

    stored_findings = store.add_findings(mission_id, findings)
    record_scan_run(
        store,
        mission_id,
        AuditCheck.HTTP_HEADERS,
        ScanRunStatus.COMPLETED,
        command_count=len(targets),
        finding_count=len(stored_findings),
        metadata={"target_count": str(len(targets))},
    )
    return stored_findings


def plan_dns_mail_audit(
    mission_id: str,
    data_dir: Path,
    dkim_selectors: list[str] | None = None,
) -> list[str]:
    store = JsonStore(data_dir)
    mission = store.get_mission(mission_id)
    domains = approved_dns_domains(mission.scope)
    if not domains:
        raise ValueError("no approved domain scope items found for DNS/Mail audit")
    return dns_mail_query_plan(domains, dkim_selectors)


def run_dns_mail_audit(
    mission_id: str,
    data_dir: Path,
    execute: bool = False,
    dkim_selectors: list[str] | None = None,
    resolver: DnsTxtResolver | None = None,
) -> list[Finding]:
    if not execute:
        raise ValueError("refusing to audit DNS/Mail without --execute; use scan dns-plan first")

    store = JsonStore(data_dir)
    mission = store.get_mission(mission_id)
    if not mission.is_authorized:
        raise ValueError("mission authorization is required before DNS/Mail audit")

    domains = approved_dns_domains(mission.scope)
    if not domains:
        raise ValueError("no approved domain scope items found for DNS/Mail audit")

    txt_resolver = resolver or DnsPythonTxtResolver()
    findings: list[Finding] = []
    try:
        for domain in domains:
            findings.extend(audit_dns_mail_domain(domain, txt_resolver, dkim_selectors))
    except Exception as error:
        record_scan_run(
            store,
            mission_id,
            AuditCheck.DNS_MAIL,
            ScanRunStatus.FAILED,
            command_count=len(domains),
            error=str(error),
            metadata={
                "domain_count": str(len(domains)),
                "dkim_selector_count": str(len(dkim_selectors or [])),
            },
        )
        raise

    stored_findings = store.add_findings(mission_id, findings)
    record_scan_run(
        store,
        mission_id,
        AuditCheck.DNS_MAIL,
        ScanRunStatus.COMPLETED,
        command_count=len(domains),
        finding_count=len(stored_findings),
        metadata={
            "domain_count": str(len(domains)),
            "dkim_selector_count": str(len(dkim_selectors or [])),
        },
    )
    return stored_findings


def plan_tls_audit(
    mission_id: str,
    data_dir: Path,
    output_dir: Path | None = None,
) -> list[list[str]]:
    store = JsonStore(data_dir)
    mission = store.get_mission(mission_id)
    evidence_dir = output_dir or Path("runs") / mission.id / "evidence"
    commands = TestsslCommandBuilder().build_for_scope(mission.scope, output_dir=evidence_dir)
    if not commands:
        raise ValueError("no approved TLS-compatible scope items found")
    return commands


def run_tls_audit(
    mission_id: str,
    data_dir: Path,
    output_dir: Path | None = None,
    execute: bool = False,
    executor: TestsslExecutor | None = None,
) -> tuple[list[TestsslExecutionResult], list[Finding]]:
    if not execute:
        raise ValueError("refusing to audit TLS without --execute; use scan tls-plan first")

    store = JsonStore(data_dir)
    mission = store.get_mission(mission_id)
    if not mission.is_authorized:
        raise ValueError("mission authorization is required before TLS audit")
    if not mission.has_approved_scope:
        raise ValueError("approved mission scope is required before TLS audit")

    evidence_dir = output_dir or Path("runs") / mission.id / "evidence"
    commands = TestsslCommandBuilder().build_for_scope(mission.scope, output_dir=evidence_dir)
    if not commands:
        raise ValueError("no approved TLS-compatible scope items found")

    tls_executor = executor or TestsslExecutor()
    try:
        results = [tls_executor.run(command) for command in commands]
    except Exception as error:
        record_scan_run(
            store,
            mission_id,
            AuditCheck.TLS,
            ScanRunStatus.FAILED,
            command_count=len(commands),
            error=str(error),
            metadata={"stage": "execution"},
        )
        raise

    evidence_paths = [
        str(result.output_path)
        for result in results
        if result.output_path is not None
    ]
    failed = [result for result in results if result.exit_code != 0]
    if failed:
        first = failed[0]
        record_scan_run(
            store,
            mission_id,
            AuditCheck.TLS,
            ScanRunStatus.FAILED,
            command_count=len(commands),
            evidence_paths=evidence_paths,
            error=first.stderr,
            metadata={"exit_code": str(first.exit_code)},
        )
        raise RuntimeError(
            f"testssl.sh command failed with exit code {first.exit_code}: {first.stderr}"
        )

    findings: list[Finding] = []
    for result in results:
        if result.output_path is not None and result.output_path.exists():
            findings.extend(parse_testssl_json_file(result.output_path, result.target))

    stored_findings = store.add_findings(mission_id, findings)
    record_scan_run(
        store,
        mission_id,
        AuditCheck.TLS,
        ScanRunStatus.COMPLETED,
        command_count=len(commands),
        finding_count=len(stored_findings),
        evidence_paths=evidence_paths,
        metadata={"target_count": str(len(commands))},
    )
    return results, stored_findings


def plan_smb_audit(
    mission_id: str,
    data_dir: Path,
) -> list[list[str]]:
    store = JsonStore(data_dir)
    mission = store.get_mission(mission_id)
    commands = SmbCommandBuilder().build_for_scope(mission.scope)
    if not commands:
        raise ValueError("no approved SMB-compatible scope items found")
    return commands


def run_smb_audit(
    mission_id: str,
    data_dir: Path,
    output_dir: Path | None = None,
    execute: bool = False,
    executor: SmbExecutor | None = None,
) -> tuple[list[SmbExecutionResult], list[Finding]]:
    if not execute:
        raise ValueError("refusing to audit SMB without --execute; use scan smb-plan first")

    store = JsonStore(data_dir)
    mission = store.get_mission(mission_id)
    if not mission.is_authorized:
        raise ValueError("mission authorization is required before SMB audit")
    if not mission.has_approved_scope:
        raise ValueError("approved mission scope is required before SMB audit")

    commands = SmbCommandBuilder().build_for_scope(mission.scope)
    if not commands:
        raise ValueError("no approved SMB-compatible scope items found")

    smb_executor = executor or SmbExecutor()
    try:
        results = [smb_executor.run(command) for command in commands]
    except Exception as error:
        record_scan_run(
            store,
            mission_id,
            AuditCheck.SMB,
            ScanRunStatus.FAILED,
            command_count=len(commands),
            error=str(error),
            metadata={"stage": "execution"},
        )
        raise

    evidence_dir = output_dir or Path("runs") / mission.id / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_paths = []
    for index, result in enumerate(results, start=1):
        evidence_path = evidence_dir / f"smbclient-{index}.txt"
        evidence_path.write_text(
            f"$ {render_smb_command(list(result.command))}\n\n"
            f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}\n",
            encoding="utf-8",
        )
        evidence_paths.append(str(evidence_path))

    failed = [result for result in results if result.exit_code != 0]
    if failed:
        first = failed[0]
        record_scan_run(
            store,
            mission_id,
            AuditCheck.SMB,
            ScanRunStatus.FAILED,
            command_count=len(commands),
            evidence_paths=evidence_paths,
            error=first.stderr,
            metadata={"exit_code": str(first.exit_code)},
        )
        raise RuntimeError(
            f"smbclient command failed with exit code {first.exit_code}: {first.stderr}"
        )

    shares = [
        share
        for result in results
        for share in parse_smbclient_listing(result.stdout, result.target)
    ]
    findings = findings_from_smb_shares(shares)
    stored_findings = store.add_findings(mission_id, findings)
    record_scan_run(
        store,
        mission_id,
        AuditCheck.SMB,
        ScanRunStatus.COMPLETED,
        command_count=len(commands),
        finding_count=len(stored_findings),
        evidence_paths=evidence_paths,
        metadata={"target_count": str(len(commands))},
    )
    return results, stored_findings


def plan_ldap_audit(
    mission_id: str,
    data_dir: Path,
) -> list[list[str]]:
    store = JsonStore(data_dir)
    mission = store.get_mission(mission_id)
    commands = LdapCommandBuilder().build_for_scope(mission.scope)
    if not commands:
        raise ValueError("no approved LDAP-compatible scope items found")
    return commands


def load_scan_plan(mission_id: str, data_dir: Path) -> tuple[Mission, list[ScanPlanPreview]]:
    store = JsonStore(data_dir)
    mission = store.get_mission(mission_id)
    return mission, build_scan_plan_previews(mission)


def plan_all_scans(mission_id: str, data_dir: Path) -> list[ScanPlanPreview]:
    return load_scan_plan(mission_id, data_dir)[1]


def scan_plan_payload(mission_id: str, data_dir: Path) -> dict[str, object]:
    mission, plans = load_scan_plan(mission_id, data_dir)
    return build_scan_plan_payload(mission, plans)


def format_scan_plan_json(mission_id: str, data_dir: Path) -> str:
    mission, plans = load_scan_plan(mission_id, data_dir)
    return render_scan_plan_json(mission, plans)


def format_scan_plan_text(mission_id: str, data_dir: Path) -> str:
    mission, plans = load_scan_plan(mission_id, data_dir)
    return render_scan_plan_text(mission, plans)


def run_ldap_audit(
    mission_id: str,
    data_dir: Path,
    output_dir: Path | None = None,
    execute: bool = False,
    executor: LdapExecutor | None = None,
) -> tuple[list[LdapExecutionResult], list[Finding]]:
    if not execute:
        raise ValueError("refusing to audit LDAP without --execute; use scan ldap-plan first")

    store = JsonStore(data_dir)
    mission = store.get_mission(mission_id)
    if not mission.is_authorized:
        raise ValueError("mission authorization is required before LDAP audit")
    if not mission.has_approved_scope:
        raise ValueError("approved mission scope is required before LDAP audit")

    commands = LdapCommandBuilder().build_for_scope(mission.scope)
    if not commands:
        raise ValueError("no approved LDAP-compatible scope items found")

    ldap_executor = executor or LdapExecutor()
    try:
        results = [ldap_executor.run(command) for command in commands]
    except Exception as error:
        record_scan_run(
            store,
            mission_id,
            AuditCheck.LDAP,
            ScanRunStatus.FAILED,
            command_count=len(commands),
            error=str(error),
            metadata={"stage": "execution"},
        )
        raise

    evidence_dir = output_dir or Path("runs") / mission.id / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_paths = []
    for index, result in enumerate(results, start=1):
        evidence_path = evidence_dir / f"ldapsearch-{index}.ldif"
        evidence_path.write_text(
            f"$ {render_ldap_command(list(result.command))}\n\n"
            f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}\n",
            encoding="utf-8",
        )
        evidence_paths.append(str(evidence_path))

    failed = [result for result in results if result.exit_code != 0]
    if failed:
        first = failed[0]
        record_scan_run(
            store,
            mission_id,
            AuditCheck.LDAP,
            ScanRunStatus.FAILED,
            command_count=len(commands),
            evidence_paths=evidence_paths,
            error=first.stderr,
            metadata={"exit_code": str(first.exit_code)},
        )
        raise RuntimeError(
            f"ldapsearch command failed with exit code {first.exit_code}: {first.stderr}"
        )

    root_dse_items = [
        parse_ldap_root_dse(result.stdout, result.target)
        for result in results
    ]
    findings = [
        finding
        for root_dse in root_dse_items
        for finding in findings_from_root_dse(root_dse)
    ]
    stored_findings = store.add_findings(mission_id, findings)
    record_scan_run(
        store,
        mission_id,
        AuditCheck.LDAP,
        ScanRunStatus.COMPLETED,
        command_count=len(commands),
        finding_count=len(stored_findings),
        evidence_paths=evidence_paths,
        metadata={"target_count": str(len(commands))},
    )
    return results, stored_findings


def format_cli_error(error: Exception) -> str:
    if isinstance(error, ValidationError):
        messages = [item["msg"] for item in error.errors()]
        return "validation failed: " + "; ".join(messages)
    return str(error)


def mission_export_verification_package_path(
    mission_id: str | None,
    reports_dir: Path,
    package_path: Path | None,
) -> Path:
    if package_path is not None:
        return package_path
    if mission_id:
        return mission_export_path(reports_dir, mission_id)
    raise ValueError("either --mission-id or --package is required")


def parse_cli_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("date must use YYYY-MM-DD format") from error


def parse_optional_cli_date(value: str | None) -> date | None:
    if value is None:
        return None
    return parse_cli_date(value)


try:
    import typer

    app = typer.Typer(help="MEDIA Security Audit Platform CLI.")
    client_app = typer.Typer(help="Manage clients.")
    mission_app = typer.Typer(help="Manage missions.")
    scope_app = typer.Typer(help="Manage mission scope.")
    finding_app = typer.Typer(help="Manage findings.")
    scan_app = typer.Typer(help="Plan safe scanner commands.")
    vuln_app = typer.Typer(help="Manage vulnerability catalog correlation.")
    report_app = typer.Typer(help="Generate reports.")
    app.add_typer(client_app, name="client")
    app.add_typer(mission_app, name="mission")
    app.add_typer(scope_app, name="scope")
    app.add_typer(finding_app, name="finding")
    app.add_typer(scan_app, name="scan")
    app.add_typer(vuln_app, name="vuln")
    app.add_typer(report_app, name="report")

    @app.callback()
    def main_callback(
        version: bool = typer.Option(False, "--version", help="Show the application version."),
    ) -> None:
        if version:
            typer.echo(__version__)
            raise typer.Exit()

    @app.command("sample-report")
    def sample_report(
        output: Path = typer.Option(Path("reports/sample"), "--output", "-o"),
    ) -> None:
        """Generate safe sample reports without network activity."""
        generate_sample_reports(output)
        typer.echo(f"Sample reports written to {output}")

    @app.command("web")
    def web(
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
        reports_dir: Path = typer.Option(Path("reports"), "--reports-dir"),
        runs_dir: Path = typer.Option(Path("runs"), "--runs-dir"),
        host: str = typer.Option("127.0.0.1", "--host"),
        port: int = typer.Option(8080, "--port"),
    ) -> None:
        """Start the local web interface."""
        try:
            run_web_interface(
                data_dir=data_dir,
                reports_dir=reports_dir,
                runs_dir=runs_dir,
                host=host,
                port=port,
            )
        except RuntimeError as error:
            typer.echo(f"error: {error}", err=True)
            raise typer.Exit(code=2) from error

    @app.command("preflight")
    def preflight(
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
        reports_dir: Path = typer.Option(Path("reports"), "--reports-dir"),
        output_format: str = typer.Option("text", "--format"),
        strict: bool = typer.Option(False, "--strict"),
    ) -> None:
        """Check local deployment readiness without running scans."""
        if output_format not in {"text", "json"}:
            raise typer.BadParameter("--format must be text or json")
        result = build_deployment_preflight(data_dir=data_dir, reports_dir=reports_dir)
        if output_format == "json":
            typer.echo(format_deployment_preflight_json(result))
        else:
            typer.echo(format_deployment_preflight(result))
        exit_code = preflight_exit_code(result, strict=strict)
        if exit_code:
            raise typer.Exit(code=exit_code)

    @client_app.command("create")
    def client_create(
        name: str = typer.Option(..., "--name"),
        reference: str | None = typer.Option(None, "--reference"),
        notes: str | None = typer.Option(None, "--notes"),
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
    ) -> None:
        client = create_client(name=name, reference=reference, notes=notes, data_dir=data_dir)
        typer.echo(client.id)

    @client_app.command("list")
    def client_list(data_dir: Path = typer.Option(Path("data"), "--data-dir")) -> None:
        for client in JsonStore(data_dir).list_clients():
            typer.echo(f"{client.id}\t{client.name}")

    @mission_app.command("create")
    def mission_create(
        client_id: str = typer.Option(..., "--client-id"),
        name: str = typer.Option(..., "--name"),
        audit_type: AuditType = typer.Option(AuditType.MIXED, "--audit-type"),
        authorization_reference: str | None = typer.Option(None, "--authorization-reference"),
        authorization_contact: str | None = typer.Option(None, "--authorization-contact"),
        authorization_date: str | None = typer.Option(None, "--authorization-date"),
        authorization_expires_at: str | None = typer.Option(None, "--authorization-expires-at"),
        emergency_contact: str | None = typer.Option(None, "--emergency-contact"),
        report_recipients: str | None = typer.Option(None, "--report-recipients"),
        evidence_retention_days: int | None = typer.Option(None, "--evidence-retention-days"),
        notes: str | None = typer.Option(None, "--notes"),
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
    ) -> None:
        try:
            parsed_authorization_date = parse_optional_cli_date(authorization_date)
            parsed_authorization_expires_at = parse_optional_cli_date(authorization_expires_at)
        except argparse.ArgumentTypeError as error:
            raise typer.BadParameter(str(error)) from error
        mission = create_mission(
            client_id=client_id,
            name=name,
            audit_type=audit_type,
            authorization_reference=authorization_reference,
            authorization_contact=authorization_contact,
            authorization_date=parsed_authorization_date,
            authorization_expires_at=parsed_authorization_expires_at,
            emergency_contact=emergency_contact,
            report_recipients=report_recipients,
            evidence_retention_days=evidence_retention_days,
            notes=notes,
            data_dir=data_dir,
        )
        typer.echo(f"{mission.id}\t{mission.status.value}")

    @mission_app.command("list")
    def mission_list(data_dir: Path = typer.Option(Path("data"), "--data-dir")) -> None:
        for mission in JsonStore(data_dir).list_missions():
            typer.echo(f"{mission.id}\t{mission.client_id}\t{mission.status.value}\t{mission.name}")

    @mission_app.command("show")
    def mission_show(
        mission_id: str = typer.Option(..., "--mission-id"),
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
    ) -> None:
        typer.echo(show_mission(mission_id=mission_id, data_dir=data_dir))

    @mission_app.command("readiness")
    def mission_readiness(
        mission_id: str = typer.Option(..., "--mission-id"),
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
        reports_dir: Path = typer.Option(Path("reports"), "--reports-dir"),
        output_format: str = typer.Option("text", "--format"),
        strict: bool = typer.Option(False, "--strict"),
    ) -> None:
        """Check mission readiness without running scans."""
        if output_format not in {"text", "json"}:
            raise typer.BadParameter("--format must be text or json")
        store = JsonStore(data_dir)
        payload = build_mission_readiness_payload(store, mission_id, reports_dir)
        if output_format == "json":
            typer.echo(format_mission_readiness_json(store, mission_id, reports_dir))
        else:
            typer.echo(format_mission_readiness_text(store, mission_id, reports_dir))
        exit_code = mission_readiness_exit_code(payload, strict=strict)
        if exit_code:
            raise typer.Exit(code=exit_code)

    @mission_app.command("export-verify")
    def mission_export_verify(
        mission_id: str | None = typer.Option(None, "--mission-id"),
        reports_dir: Path = typer.Option(Path("reports"), "--reports-dir"),
        package_path: Path | None = typer.Option(None, "--package"),
        output_format: str = typer.Option("text", "--format"),
        strict: bool = typer.Option(False, "--strict"),
    ) -> None:
        """Verify a mission export ZIP package without running scans."""
        if output_format not in {"text", "json"}:
            raise typer.BadParameter("--format must be text or json")
        try:
            path = mission_export_verification_package_path(mission_id, reports_dir, package_path)
        except ValueError as error:
            raise typer.BadParameter(str(error)) from error
        verification = verify_mission_export(path)
        if output_format == "json":
            typer.echo(format_mission_export_verification_json(path, verification))
        else:
            typer.echo(format_mission_export_verification_text(path, verification))
        exit_code = mission_export_verification_exit_code(verification, strict=strict)
        if exit_code:
            raise typer.Exit(code=exit_code)

    @mission_app.command("export-manifest")
    def mission_export_manifest(
        mission_id: str | None = typer.Option(None, "--mission-id"),
        reports_dir: Path = typer.Option(Path("reports"), "--reports-dir"),
        package_path: Path | None = typer.Option(None, "--package"),
        output_format: str = typer.Option("json", "--format"),
    ) -> None:
        """Print a mission export ZIP manifest without extracting the package."""
        if output_format not in {"json", "markdown"}:
            raise typer.BadParameter("--format must be json or markdown")
        try:
            path = mission_export_verification_package_path(mission_id, reports_dir, package_path)
        except ValueError as error:
            raise typer.BadParameter(str(error)) from error
        manifest = read_mission_export_manifest(path)
        if output_format == "json":
            typer.echo(format_mission_export_manifest_json(manifest))
        else:
            typer.echo(format_mission_export_manifest_markdown(manifest))

    @mission_app.command("export-inventory")
    def mission_export_inventory(
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
        reports_dir: Path = typer.Option(Path("reports"), "--reports-dir"),
        output_format: str = typer.Option("text", "--format"),
        include_missing: bool = typer.Option(False, "--include-missing"),
    ) -> None:
        """List mission export ZIP packages without opening the web interface."""
        if output_format not in {"text", "json"}:
            raise typer.BadParameter("--format must be text or json")
        store = JsonStore(data_dir)
        items = build_mission_export_inventory(store, reports_dir, include_missing=include_missing)
        if output_format == "json":
            typer.echo(format_mission_export_inventory_json(items))
        else:
            typer.echo(format_mission_export_inventory_text(items))

    @scope_app.command("add")
    def scope_add(
        mission_id: str = typer.Option(..., "--mission-id"),
        scope_type: ScopeType = typer.Option(..., "--type"),
        value: str = typer.Option(..., "--value"),
        environment: ScopeEnvironment = typer.Option(ScopeEnvironment.UNKNOWN, "--environment"),
        approved: bool = typer.Option(False, "--approved"),
        excluded: bool = typer.Option(False, "--excluded"),
        notes: str | None = typer.Option(None, "--notes"),
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
    ) -> None:
        mission = add_scope(
            mission_id=mission_id,
            scope_type=scope_type,
            value=value,
            environment=environment,
            approved=approved,
            excluded=excluded,
            notes=notes,
            data_dir=data_dir,
        )
        typer.echo(f"{mission.id}\t{mission.status.value}\t{len(mission.scope)} scope item(s)")

    @scope_app.command("list")
    def scope_list(
        mission_id: str = typer.Option(..., "--mission-id"),
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
    ) -> None:
        for item in list_scope(mission_id=mission_id, data_dir=data_dir):
            status = "excluded" if item.excluded else "approved" if item.approved else "draft"
            typer.echo(f"{item.id}\t{item.type.value}\t{status}\t{item.environment.value}\t{item.value}")

    @finding_app.command("add")
    def finding_add(
        mission_id: str = typer.Option(..., "--mission-id"),
        title: str = typer.Option(..., "--title"),
        severity: Severity = typer.Option(..., "--severity"),
        affected_asset: str = typer.Option(..., "--asset"),
        category: str = typer.Option("manual", "--category"),
        proof: str = typer.Option(..., "--proof"),
        risk: str = typer.Option(..., "--risk"),
        remediation: str = typer.Option(..., "--remediation"),
        counter_test: str = typer.Option(..., "--counter-test"),
        source_module: str = typer.Option("manual", "--source-module"),
        confidence: float = typer.Option(0.8, "--confidence"),
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
    ) -> None:
        finding = add_finding(
            mission_id=mission_id,
            title=title,
            severity=severity,
            affected_asset=affected_asset,
            category=category,
            proof=proof,
            risk=risk,
            remediation=remediation,
            counter_test=counter_test,
            source_module=source_module,
            confidence=confidence,
            data_dir=data_dir,
        )
        typer.echo(f"{finding.id}\t{finding.severity.value}\t{finding.title}")

    @finding_app.command("add-sample")
    def finding_add_sample(
        mission_id: str = typer.Option(..., "--mission-id"),
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
    ) -> None:
        findings = add_sample_findings(mission_id=mission_id, data_dir=data_dir)
        typer.echo(f"{len(findings)} finding(s) stored")

    @finding_app.command("list")
    def finding_list(
        mission_id: str = typer.Option(..., "--mission-id"),
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
    ) -> None:
        for finding in JsonStore(data_dir).list_findings(mission_id):
            typer.echo(
                f"{finding.id}\t{finding.severity.value}\t"
                f"{finding.status.value}\t{finding.affected_asset}\t{finding.title}"
            )

    @report_app.command("generate")
    def report_generate(
        mission_id: str = typer.Option(..., "--mission-id"),
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
        output: Path | None = typer.Option(None, "--output"),
    ) -> None:
        for path in generate_mission_reports(mission_id=mission_id, data_dir=data_dir, output=output):
            typer.echo(path)

    @scan_app.command("plan-all")
    def scan_plan_all(
        mission_id: str = typer.Option(..., "--mission-id"),
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
        output_format: str = typer.Option("text", "--format"),
    ) -> None:
        """Print all selected safe scan plans without executing anything."""
        if output_format not in {"text", "json"}:
            raise typer.BadParameter("--format must be text or json")
        if output_format == "json":
            typer.echo(format_scan_plan_json(mission_id=mission_id, data_dir=data_dir))
        else:
            typer.echo(format_scan_plan_text(mission_id=mission_id, data_dir=data_dir))

    @scan_app.command("nmap-plan")
    def scan_nmap_plan(
        mission_id: str = typer.Option(..., "--mission-id"),
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
        output_dir: Path | None = typer.Option(None, "--output-dir"),
    ) -> None:
        """Print safe Nmap commands without executing them."""
        for command in plan_nmap_scan(
            mission_id=mission_id,
            data_dir=data_dir,
            output_dir=output_dir,
        ):
            typer.echo(render_command(command))

    @scan_app.command("nmap-run")
    def scan_nmap_run(
        mission_id: str = typer.Option(..., "--mission-id"),
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
        output_dir: Path | None = typer.Option(None, "--output-dir"),
        execute: bool = typer.Option(False, "--execute", help="Required to execute Nmap."),
    ) -> None:
        """Execute safe Nmap commands only when --execute is explicitly provided."""
        results, findings = run_nmap_scan(
            mission_id=mission_id,
            data_dir=data_dir,
            output_dir=output_dir,
            execute=execute,
        )
        typer.echo(f"Executed {len(results)} Nmap command(s); stored {len(findings)} finding(s).")

    @scan_app.command("http-plan")
    def scan_http_plan(
        mission_id: str = typer.Option(..., "--mission-id"),
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
    ) -> None:
        """Print approved URL targets for HTTP header audit without making requests."""
        for target in plan_http_headers_audit(mission_id=mission_id, data_dir=data_dir):
            typer.echo(target)

    @scan_app.command("http-run")
    def scan_http_run(
        mission_id: str = typer.Option(..., "--mission-id"),
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
        execute: bool = typer.Option(False, "--execute", help="Required to make HTTP requests."),
    ) -> None:
        """Audit HTTP headers only when --execute is explicitly provided."""
        findings = run_http_headers_audit(
            mission_id=mission_id,
            data_dir=data_dir,
            execute=execute,
        )
        typer.echo(f"Stored {len(findings)} HTTP header finding(s).")

    @scan_app.command("dns-plan")
    def scan_dns_plan(
        mission_id: str = typer.Option(..., "--mission-id"),
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
        dkim_selectors: list[str] | None = typer.Option(None, "--dkim-selector"),
    ) -> None:
        """Print DNS TXT queries for approved domains without making requests."""
        for query in plan_dns_mail_audit(
            mission_id=mission_id,
            data_dir=data_dir,
            dkim_selectors=dkim_selectors,
        ):
            typer.echo(query)

    @scan_app.command("dns-run")
    def scan_dns_run(
        mission_id: str = typer.Option(..., "--mission-id"),
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
        execute: bool = typer.Option(False, "--execute", help="Required to make DNS requests."),
        dkim_selectors: list[str] | None = typer.Option(None, "--dkim-selector"),
    ) -> None:
        """Audit DNS/Mail records only when --execute is explicitly provided."""
        findings = run_dns_mail_audit(
            mission_id=mission_id,
            data_dir=data_dir,
            execute=execute,
            dkim_selectors=dkim_selectors,
        )
        typer.echo(f"Stored {len(findings)} DNS/Mail finding(s).")

    @scan_app.command("tls-plan")
    def scan_tls_plan(
        mission_id: str = typer.Option(..., "--mission-id"),
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
        output_dir: Path | None = typer.Option(None, "--output-dir"),
    ) -> None:
        """Print safe testssl.sh commands without executing them."""
        for command in plan_tls_audit(
            mission_id=mission_id,
            data_dir=data_dir,
            output_dir=output_dir,
        ):
            typer.echo(render_testssl_command(command))

    @scan_app.command("tls-run")
    def scan_tls_run(
        mission_id: str = typer.Option(..., "--mission-id"),
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
        output_dir: Path | None = typer.Option(None, "--output-dir"),
        execute: bool = typer.Option(False, "--execute", help="Required to run testssl.sh."),
    ) -> None:
        """Audit TLS with testssl.sh only when --execute is explicitly provided."""
        results, findings = run_tls_audit(
            mission_id=mission_id,
            data_dir=data_dir,
            output_dir=output_dir,
            execute=execute,
        )
        typer.echo(f"Executed {len(results)} TLS command(s); stored {len(findings)} finding(s).")

    @scan_app.command("smb-plan")
    def scan_smb_plan(
        mission_id: str = typer.Option(..., "--mission-id"),
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
    ) -> None:
        """Print safe smbclient commands without executing them."""
        for command in plan_smb_audit(mission_id=mission_id, data_dir=data_dir):
            typer.echo(render_smb_command(command))

    @scan_app.command("smb-run")
    def scan_smb_run(
        mission_id: str = typer.Option(..., "--mission-id"),
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
        output_dir: Path | None = typer.Option(None, "--output-dir"),
        execute: bool = typer.Option(False, "--execute", help="Required to run smbclient."),
    ) -> None:
        """Audit SMB anonymous listing only when --execute is explicitly provided."""
        results, findings = run_smb_audit(
            mission_id=mission_id,
            data_dir=data_dir,
            output_dir=output_dir,
            execute=execute,
        )
        typer.echo(f"Executed {len(results)} SMB command(s); stored {len(findings)} finding(s).")

    @scan_app.command("ldap-plan")
    def scan_ldap_plan(
        mission_id: str = typer.Option(..., "--mission-id"),
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
    ) -> None:
        """Print safe ldapsearch commands without executing them."""
        for command in plan_ldap_audit(mission_id=mission_id, data_dir=data_dir):
            typer.echo(render_ldap_command(command))

    @scan_app.command("ldap-run")
    def scan_ldap_run(
        mission_id: str = typer.Option(..., "--mission-id"),
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
        output_dir: Path | None = typer.Option(None, "--output-dir"),
        execute: bool = typer.Option(False, "--execute", help="Required to run ldapsearch."),
    ) -> None:
        """Audit LDAP RootDSE only when --execute is explicitly provided."""
        results, findings = run_ldap_audit(
            mission_id=mission_id,
            data_dir=data_dir,
            output_dir=output_dir,
            execute=execute,
        )
        typer.echo(f"Executed {len(results)} LDAP command(s); stored {len(findings)} finding(s).")

    @vuln_app.command("import")
    def vuln_import(
        input_path: Path = typer.Option(..., "--input"),
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
    ) -> None:
        """Import a reviewed local CVE/KEV catalog without network activity."""
        catalog = import_vulnerability_catalog(input_path, data_dir)
        typer.echo(f"Imported {len(catalog.advisories)} vulnerability advisory item(s).")

    @vuln_app.command("list")
    def vuln_list(
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
        output_format: str = typer.Option("text", "--format"),
    ) -> None:
        """List the local vulnerability catalog."""
        if output_format not in {"text", "json"}:
            raise typer.BadParameter("--format must be text or json")
        catalog = load_vulnerability_catalog(data_dir)
        if output_format == "json":
            typer.echo(format_vulnerability_catalog_json(catalog))
        else:
            typer.echo(format_vulnerability_catalog_text(catalog))

    @vuln_app.command("correlate")
    def vuln_correlate(
        mission_id: str = typer.Option(..., "--mission-id"),
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
        output_format: str = typer.Option("text", "--format"),
        store_findings: bool = typer.Option(False, "--store-findings"),
    ) -> None:
        """Correlate stored findings with the local vulnerability catalog."""
        if output_format not in {"text", "json"}:
            raise typer.BadParameter("--format must be text or json")
        matches = correlate_vulnerability_catalog(mission_id, data_dir)
        if store_findings:
            stored = store_vulnerability_findings_for_mission(mission_id, data_dir)
            typer.echo(f"Stored {len(stored)} vulnerability finding(s).")
        if output_format == "json":
            typer.echo(format_vulnerability_correlation_json(matches))
        else:
            typer.echo(format_vulnerability_correlation_text(matches))

except ModuleNotFoundError:

    def app(argv: list[str] | None = None) -> None:
        """Fallback CLI for bootstrap environments without Typer installed."""
        parser = argparse.ArgumentParser(description="MEDIA Security Audit Platform CLI.")
        parser.add_argument("--version", action="store_true", help="Show the application version.")
        subparsers = parser.add_subparsers(dest="command")

        sample_parser = subparsers.add_parser(
            "sample-report",
            help="Generate safe sample reports without network activity.",
        )
        sample_parser.add_argument("--output", "-o", type=Path, default=Path("reports/sample"))

        web_parser = subparsers.add_parser(
            "web",
            help="Start the local web interface.",
        )
        web_parser.add_argument("--data-dir", type=Path, default=Path("data"))
        web_parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
        web_parser.add_argument("--runs-dir", type=Path, default=Path("runs"))
        web_parser.add_argument("--host", default="127.0.0.1")
        web_parser.add_argument("--port", type=int, default=8080)

        preflight_parser = subparsers.add_parser(
            "preflight",
            help="Check local deployment readiness without running scans.",
        )
        preflight_parser.add_argument("--data-dir", type=Path, default=Path("data"))
        preflight_parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
        preflight_parser.add_argument("--format", choices=["text", "json"], default="text")
        preflight_parser.add_argument("--strict", action="store_true")

        client_parser = subparsers.add_parser("client", help="Manage clients.")
        client_subparsers = client_parser.add_subparsers(dest="client_command")
        client_create_parser = client_subparsers.add_parser("create", help="Create a client.")
        client_create_parser.add_argument("--name", required=True)
        client_create_parser.add_argument("--reference")
        client_create_parser.add_argument("--notes")
        client_create_parser.add_argument("--data-dir", type=Path, default=Path("data"))
        client_list_parser = client_subparsers.add_parser("list", help="List clients.")
        client_list_parser.add_argument("--data-dir", type=Path, default=Path("data"))

        mission_parser = subparsers.add_parser("mission", help="Manage missions.")
        mission_subparsers = mission_parser.add_subparsers(dest="mission_command")
        mission_create_parser = mission_subparsers.add_parser("create", help="Create a mission.")
        mission_create_parser.add_argument("--client-id", required=True)
        mission_create_parser.add_argument("--name", required=True)
        mission_create_parser.add_argument("--audit-type", choices=[item.value for item in AuditType], default=AuditType.MIXED.value)
        mission_create_parser.add_argument("--authorization-reference")
        mission_create_parser.add_argument("--authorization-contact")
        mission_create_parser.add_argument("--authorization-date", type=parse_cli_date)
        mission_create_parser.add_argument("--authorization-expires-at", type=parse_cli_date)
        mission_create_parser.add_argument("--emergency-contact")
        mission_create_parser.add_argument("--report-recipients")
        mission_create_parser.add_argument("--evidence-retention-days", type=int)
        mission_create_parser.add_argument("--notes")
        mission_create_parser.add_argument("--data-dir", type=Path, default=Path("data"))
        mission_list_parser = mission_subparsers.add_parser("list", help="List missions.")
        mission_list_parser.add_argument("--data-dir", type=Path, default=Path("data"))
        mission_show_parser = mission_subparsers.add_parser("show", help="Show mission details.")
        mission_show_parser.add_argument("--mission-id", required=True)
        mission_show_parser.add_argument("--data-dir", type=Path, default=Path("data"))
        mission_readiness_parser = mission_subparsers.add_parser(
            "readiness",
            help="Check mission readiness without running scans.",
        )
        mission_readiness_parser.add_argument("--mission-id", required=True)
        mission_readiness_parser.add_argument("--data-dir", type=Path, default=Path("data"))
        mission_readiness_parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
        mission_readiness_parser.add_argument("--format", choices=["text", "json"], default="text")
        mission_readiness_parser.add_argument("--strict", action="store_true")
        mission_export_verify_parser = mission_subparsers.add_parser(
            "export-verify",
            help="Verify a mission export ZIP package without running scans.",
        )
        mission_export_verify_parser.add_argument("--mission-id")
        mission_export_verify_parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
        mission_export_verify_parser.add_argument("--package", type=Path)
        mission_export_verify_parser.add_argument("--format", choices=["text", "json"], default="text")
        mission_export_verify_parser.add_argument("--strict", action="store_true")
        mission_export_manifest_parser = mission_subparsers.add_parser(
            "export-manifest",
            help="Print a mission export ZIP manifest without extracting the package.",
        )
        mission_export_manifest_parser.add_argument("--mission-id")
        mission_export_manifest_parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
        mission_export_manifest_parser.add_argument("--package", type=Path)
        mission_export_manifest_parser.add_argument("--format", choices=["json", "markdown"], default="json")
        mission_export_inventory_parser = mission_subparsers.add_parser(
            "export-inventory",
            help="List mission export ZIP packages without opening the web interface.",
        )
        mission_export_inventory_parser.add_argument("--data-dir", type=Path, default=Path("data"))
        mission_export_inventory_parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
        mission_export_inventory_parser.add_argument("--format", choices=["text", "json"], default="text")
        mission_export_inventory_parser.add_argument("--include-missing", action="store_true")

        scope_parser = subparsers.add_parser("scope", help="Manage mission scope.")
        scope_subparsers = scope_parser.add_subparsers(dest="scope_command")
        scope_add_parser = scope_subparsers.add_parser("add", help="Add a scope item.")
        scope_add_parser.add_argument("--mission-id", required=True)
        scope_add_parser.add_argument("--type", required=True, choices=[item.value for item in ScopeType])
        scope_add_parser.add_argument("--value", required=True)
        scope_add_parser.add_argument("--environment", choices=[item.value for item in ScopeEnvironment], default=ScopeEnvironment.UNKNOWN.value)
        scope_add_parser.add_argument("--approved", action="store_true")
        scope_add_parser.add_argument("--excluded", action="store_true")
        scope_add_parser.add_argument("--notes")
        scope_add_parser.add_argument("--data-dir", type=Path, default=Path("data"))
        scope_list_parser = scope_subparsers.add_parser("list", help="List mission scope.")
        scope_list_parser.add_argument("--mission-id", required=True)
        scope_list_parser.add_argument("--data-dir", type=Path, default=Path("data"))

        finding_parser = subparsers.add_parser("finding", help="Manage findings.")
        finding_subparsers = finding_parser.add_subparsers(dest="finding_command")
        finding_add_parser = finding_subparsers.add_parser("add", help="Add a manual finding.")
        finding_add_parser.add_argument("--mission-id", required=True)
        finding_add_parser.add_argument("--title", required=True)
        finding_add_parser.add_argument("--severity", required=True, choices=[item.value for item in Severity])
        finding_add_parser.add_argument("--asset", required=True)
        finding_add_parser.add_argument("--category", default="manual")
        finding_add_parser.add_argument("--proof", required=True)
        finding_add_parser.add_argument("--risk", required=True)
        finding_add_parser.add_argument("--remediation", required=True)
        finding_add_parser.add_argument("--counter-test", required=True)
        finding_add_parser.add_argument("--source-module", default="manual")
        finding_add_parser.add_argument("--confidence", type=float, default=0.8)
        finding_add_parser.add_argument("--data-dir", type=Path, default=Path("data"))
        finding_sample_parser = finding_subparsers.add_parser(
            "add-sample",
            help="Attach safe sample findings to a mission.",
        )
        finding_sample_parser.add_argument("--mission-id", required=True)
        finding_sample_parser.add_argument("--data-dir", type=Path, default=Path("data"))
        finding_list_parser = finding_subparsers.add_parser("list", help="List mission findings.")
        finding_list_parser.add_argument("--mission-id", required=True)
        finding_list_parser.add_argument("--data-dir", type=Path, default=Path("data"))

        scan_parser = subparsers.add_parser("scan", help="Plan safe scanner commands.")
        scan_subparsers = scan_parser.add_subparsers(dest="scan_command")
        plan_all_parser = scan_subparsers.add_parser(
            "plan-all",
            help="Print all selected safe scan plans without executing anything.",
        )
        plan_all_parser.add_argument("--mission-id", required=True)
        plan_all_parser.add_argument("--data-dir", type=Path, default=Path("data"))
        plan_all_parser.add_argument("--format", choices=["text", "json"], default="text")
        nmap_plan_parser = scan_subparsers.add_parser(
            "nmap-plan",
            help="Print safe Nmap commands without executing them.",
        )
        nmap_plan_parser.add_argument("--mission-id", required=True)
        nmap_plan_parser.add_argument("--data-dir", type=Path, default=Path("data"))
        nmap_plan_parser.add_argument("--output-dir", type=Path)
        nmap_run_parser = scan_subparsers.add_parser(
            "nmap-run",
            help="Execute safe Nmap commands only when --execute is explicitly provided.",
        )
        nmap_run_parser.add_argument("--mission-id", required=True)
        nmap_run_parser.add_argument("--data-dir", type=Path, default=Path("data"))
        nmap_run_parser.add_argument("--output-dir", type=Path)
        nmap_run_parser.add_argument("--execute", action="store_true")
        http_plan_parser = scan_subparsers.add_parser(
            "http-plan",
            help="Print approved URL targets for HTTP header audit without making requests.",
        )
        http_plan_parser.add_argument("--mission-id", required=True)
        http_plan_parser.add_argument("--data-dir", type=Path, default=Path("data"))
        http_run_parser = scan_subparsers.add_parser(
            "http-run",
            help="Audit HTTP headers only when --execute is explicitly provided.",
        )
        http_run_parser.add_argument("--mission-id", required=True)
        http_run_parser.add_argument("--data-dir", type=Path, default=Path("data"))
        http_run_parser.add_argument("--execute", action="store_true")
        dns_plan_parser = scan_subparsers.add_parser(
            "dns-plan",
            help="Print DNS TXT queries for approved domains without making requests.",
        )
        dns_plan_parser.add_argument("--mission-id", required=True)
        dns_plan_parser.add_argument("--data-dir", type=Path, default=Path("data"))
        dns_plan_parser.add_argument("--dkim-selector", action="append", default=[])
        dns_run_parser = scan_subparsers.add_parser(
            "dns-run",
            help="Audit DNS/Mail records only when --execute is explicitly provided.",
        )
        dns_run_parser.add_argument("--mission-id", required=True)
        dns_run_parser.add_argument("--data-dir", type=Path, default=Path("data"))
        dns_run_parser.add_argument("--execute", action="store_true")
        dns_run_parser.add_argument("--dkim-selector", action="append", default=[])
        tls_plan_parser = scan_subparsers.add_parser(
            "tls-plan",
            help="Print safe testssl.sh commands without executing them.",
        )
        tls_plan_parser.add_argument("--mission-id", required=True)
        tls_plan_parser.add_argument("--data-dir", type=Path, default=Path("data"))
        tls_plan_parser.add_argument("--output-dir", type=Path)
        tls_run_parser = scan_subparsers.add_parser(
            "tls-run",
            help="Audit TLS with testssl.sh only when --execute is explicitly provided.",
        )
        tls_run_parser.add_argument("--mission-id", required=True)
        tls_run_parser.add_argument("--data-dir", type=Path, default=Path("data"))
        tls_run_parser.add_argument("--output-dir", type=Path)
        tls_run_parser.add_argument("--execute", action="store_true")
        smb_plan_parser = scan_subparsers.add_parser(
            "smb-plan",
            help="Print safe smbclient commands without executing them.",
        )
        smb_plan_parser.add_argument("--mission-id", required=True)
        smb_plan_parser.add_argument("--data-dir", type=Path, default=Path("data"))
        smb_run_parser = scan_subparsers.add_parser(
            "smb-run",
            help="Audit SMB anonymous listing only when --execute is explicitly provided.",
        )
        smb_run_parser.add_argument("--mission-id", required=True)
        smb_run_parser.add_argument("--data-dir", type=Path, default=Path("data"))
        smb_run_parser.add_argument("--output-dir", type=Path)
        smb_run_parser.add_argument("--execute", action="store_true")
        ldap_plan_parser = scan_subparsers.add_parser(
            "ldap-plan",
            help="Print safe ldapsearch commands without executing them.",
        )
        ldap_plan_parser.add_argument("--mission-id", required=True)
        ldap_plan_parser.add_argument("--data-dir", type=Path, default=Path("data"))
        ldap_run_parser = scan_subparsers.add_parser(
            "ldap-run",
            help="Audit LDAP RootDSE only when --execute is explicitly provided.",
        )
        ldap_run_parser.add_argument("--mission-id", required=True)
        ldap_run_parser.add_argument("--data-dir", type=Path, default=Path("data"))
        ldap_run_parser.add_argument("--output-dir", type=Path)
        ldap_run_parser.add_argument("--execute", action="store_true")

        vuln_parser = subparsers.add_parser(
            "vuln",
            help="Manage vulnerability catalog correlation.",
        )
        vuln_subparsers = vuln_parser.add_subparsers(dest="vuln_command")
        vuln_import_parser = vuln_subparsers.add_parser(
            "import",
            help="Import a reviewed local CVE/KEV catalog without network activity.",
        )
        vuln_import_parser.add_argument("--input", required=True, type=Path)
        vuln_import_parser.add_argument("--data-dir", type=Path, default=Path("data"))
        vuln_list_parser = vuln_subparsers.add_parser(
            "list",
            help="List the local vulnerability catalog.",
        )
        vuln_list_parser.add_argument("--data-dir", type=Path, default=Path("data"))
        vuln_list_parser.add_argument("--format", choices=["text", "json"], default="text")
        vuln_correlate_parser = vuln_subparsers.add_parser(
            "correlate",
            help="Correlate stored findings with the local vulnerability catalog.",
        )
        vuln_correlate_parser.add_argument("--mission-id", required=True)
        vuln_correlate_parser.add_argument("--data-dir", type=Path, default=Path("data"))
        vuln_correlate_parser.add_argument("--format", choices=["text", "json"], default="text")
        vuln_correlate_parser.add_argument("--store-findings", action="store_true")

        report_parser = subparsers.add_parser("report", help="Generate reports.")
        report_subparsers = report_parser.add_subparsers(dest="report_command")
        report_generate_parser = report_subparsers.add_parser("generate", help="Generate mission reports.")
        report_generate_parser.add_argument("--mission-id", required=True)
        report_generate_parser.add_argument("--data-dir", type=Path, default=Path("data"))
        report_generate_parser.add_argument("--output", type=Path)

        args = parser.parse_args(argv)

        try:
            if args.version:
                print(__version__)
                return

            if args.command == "sample-report":
                generate_sample_reports(args.output)
                print(f"Sample reports written to {args.output}")
                return

            if args.command == "web":
                run_web_interface(
                    data_dir=args.data_dir,
                    reports_dir=args.reports_dir,
                    runs_dir=args.runs_dir,
                    host=args.host,
                    port=args.port,
                )
                return

            if args.command == "preflight":
                result = build_deployment_preflight(
                    data_dir=args.data_dir,
                    reports_dir=args.reports_dir,
                )
                if args.format == "json":
                    print(format_deployment_preflight_json(result))
                else:
                    print(format_deployment_preflight(result))
                exit_code = preflight_exit_code(result, strict=args.strict)
                if exit_code:
                    raise SystemExit(exit_code)
                return

            if args.command == "client" and args.client_command == "create":
                client = create_client(
                    name=args.name,
                    reference=args.reference,
                    notes=args.notes,
                    data_dir=args.data_dir,
                )
                print(client.id)
                return

            if args.command == "client" and args.client_command == "list":
                for client in JsonStore(args.data_dir).list_clients():
                    print(f"{client.id}\t{client.name}")
                return

            if args.command == "mission" and args.mission_command == "create":
                mission = create_mission(
                    client_id=args.client_id,
                    name=args.name,
                    audit_type=AuditType(args.audit_type),
                    authorization_reference=args.authorization_reference,
                    authorization_contact=args.authorization_contact,
                    authorization_date=args.authorization_date,
                    authorization_expires_at=args.authorization_expires_at,
                    emergency_contact=args.emergency_contact,
                    report_recipients=args.report_recipients,
                    evidence_retention_days=args.evidence_retention_days,
                    notes=args.notes,
                    data_dir=args.data_dir,
                )
                print(f"{mission.id}\t{mission.status.value}")
                return

            if args.command == "mission" and args.mission_command == "list":
                for mission in JsonStore(args.data_dir).list_missions():
                    print(f"{mission.id}\t{mission.client_id}\t{mission.status.value}\t{mission.name}")
                return

            if args.command == "mission" and args.mission_command == "show":
                print(show_mission(mission_id=args.mission_id, data_dir=args.data_dir))
                return

            if args.command == "mission" and args.mission_command == "readiness":
                store = JsonStore(args.data_dir)
                payload = build_mission_readiness_payload(store, args.mission_id, args.reports_dir)
                if args.format == "json":
                    print(format_mission_readiness_json(store, args.mission_id, args.reports_dir))
                else:
                    print(format_mission_readiness_text(store, args.mission_id, args.reports_dir))
                exit_code = mission_readiness_exit_code(payload, strict=args.strict)
                if exit_code:
                    raise SystemExit(exit_code)
                return

            if args.command == "mission" and args.mission_command == "export-verify":
                path = mission_export_verification_package_path(args.mission_id, args.reports_dir, args.package)
                verification = verify_mission_export(path)
                if args.format == "json":
                    print(format_mission_export_verification_json(path, verification))
                else:
                    print(format_mission_export_verification_text(path, verification))
                exit_code = mission_export_verification_exit_code(verification, strict=args.strict)
                if exit_code:
                    raise SystemExit(exit_code)
                return

            if args.command == "mission" and args.mission_command == "export-manifest":
                path = mission_export_verification_package_path(args.mission_id, args.reports_dir, args.package)
                manifest = read_mission_export_manifest(path)
                if args.format == "json":
                    print(format_mission_export_manifest_json(manifest))
                else:
                    print(format_mission_export_manifest_markdown(manifest))
                return

            if args.command == "mission" and args.mission_command == "export-inventory":
                items = build_mission_export_inventory(
                    JsonStore(args.data_dir),
                    args.reports_dir,
                    include_missing=args.include_missing,
                )
                if args.format == "json":
                    print(format_mission_export_inventory_json(items))
                else:
                    print(format_mission_export_inventory_text(items))
                return

            if args.command == "scope" and args.scope_command == "add":
                mission = add_scope(
                    mission_id=args.mission_id,
                    scope_type=ScopeType(args.type),
                    value=args.value,
                    environment=ScopeEnvironment(args.environment),
                    approved=args.approved,
                    excluded=args.excluded,
                    notes=args.notes,
                    data_dir=args.data_dir,
                )
                print(f"{mission.id}\t{mission.status.value}\t{len(mission.scope)} scope item(s)")
                return

            if args.command == "scope" and args.scope_command == "list":
                for item in list_scope(mission_id=args.mission_id, data_dir=args.data_dir):
                    status = "excluded" if item.excluded else "approved" if item.approved else "draft"
                    print(f"{item.id}\t{item.type.value}\t{status}\t{item.environment.value}\t{item.value}")
                return

            if args.command == "finding" and args.finding_command == "add":
                finding = add_finding(
                    mission_id=args.mission_id,
                    title=args.title,
                    severity=Severity(args.severity),
                    affected_asset=args.asset,
                    category=args.category,
                    proof=args.proof,
                    risk=args.risk,
                    remediation=args.remediation,
                    counter_test=args.counter_test,
                    source_module=args.source_module,
                    confidence=args.confidence,
                    data_dir=args.data_dir,
                )
                print(f"{finding.id}\t{finding.severity.value}\t{finding.title}")
                return

            if args.command == "finding" and args.finding_command == "add-sample":
                findings = add_sample_findings(mission_id=args.mission_id, data_dir=args.data_dir)
                print(f"{len(findings)} finding(s) stored")
                return

            if args.command == "finding" and args.finding_command == "list":
                for finding in JsonStore(args.data_dir).list_findings(args.mission_id):
                    print(
                        f"{finding.id}\t{finding.severity.value}\t"
                        f"{finding.status.value}\t{finding.affected_asset}\t{finding.title}"
                    )
                return

            if args.command == "scan" and args.scan_command == "plan-all":
                if args.format == "json":
                    print(format_scan_plan_json(mission_id=args.mission_id, data_dir=args.data_dir))
                else:
                    print(format_scan_plan_text(mission_id=args.mission_id, data_dir=args.data_dir))
                return

            if args.command == "scan" and args.scan_command == "nmap-plan":
                for command in plan_nmap_scan(
                    mission_id=args.mission_id,
                    data_dir=args.data_dir,
                    output_dir=args.output_dir,
                ):
                    print(render_command(command))
                return

            if args.command == "scan" and args.scan_command == "nmap-run":
                results, findings = run_nmap_scan(
                    mission_id=args.mission_id,
                    data_dir=args.data_dir,
                    output_dir=args.output_dir,
                    execute=args.execute,
                )
                print(f"Executed {len(results)} Nmap command(s); stored {len(findings)} finding(s).")
                return

            if args.command == "scan" and args.scan_command == "http-plan":
                for target in plan_http_headers_audit(mission_id=args.mission_id, data_dir=args.data_dir):
                    print(target)
                return

            if args.command == "scan" and args.scan_command == "http-run":
                findings = run_http_headers_audit(
                    mission_id=args.mission_id,
                    data_dir=args.data_dir,
                    execute=args.execute,
                )
                print(f"Stored {len(findings)} HTTP header finding(s).")
                return

            if args.command == "scan" and args.scan_command == "dns-plan":
                for query in plan_dns_mail_audit(
                    mission_id=args.mission_id,
                    data_dir=args.data_dir,
                    dkim_selectors=args.dkim_selector,
                ):
                    print(query)
                return

            if args.command == "scan" and args.scan_command == "dns-run":
                findings = run_dns_mail_audit(
                    mission_id=args.mission_id,
                    data_dir=args.data_dir,
                    execute=args.execute,
                    dkim_selectors=args.dkim_selector,
                )
                print(f"Stored {len(findings)} DNS/Mail finding(s).")
                return

            if args.command == "scan" and args.scan_command == "tls-plan":
                for command in plan_tls_audit(
                    mission_id=args.mission_id,
                    data_dir=args.data_dir,
                    output_dir=args.output_dir,
                ):
                    print(render_testssl_command(command))
                return

            if args.command == "scan" and args.scan_command == "tls-run":
                results, findings = run_tls_audit(
                    mission_id=args.mission_id,
                    data_dir=args.data_dir,
                    output_dir=args.output_dir,
                    execute=args.execute,
                )
                print(f"Executed {len(results)} TLS command(s); stored {len(findings)} finding(s).")
                return

            if args.command == "scan" and args.scan_command == "smb-plan":
                for command in plan_smb_audit(mission_id=args.mission_id, data_dir=args.data_dir):
                    print(render_smb_command(command))
                return

            if args.command == "scan" and args.scan_command == "smb-run":
                results, findings = run_smb_audit(
                    mission_id=args.mission_id,
                    data_dir=args.data_dir,
                    output_dir=args.output_dir,
                    execute=args.execute,
                )
                print(f"Executed {len(results)} SMB command(s); stored {len(findings)} finding(s).")
                return

            if args.command == "scan" and args.scan_command == "ldap-plan":
                for command in plan_ldap_audit(mission_id=args.mission_id, data_dir=args.data_dir):
                    print(render_ldap_command(command))
                return

            if args.command == "scan" and args.scan_command == "ldap-run":
                results, findings = run_ldap_audit(
                    mission_id=args.mission_id,
                    data_dir=args.data_dir,
                    output_dir=args.output_dir,
                    execute=args.execute,
                )
                print(f"Executed {len(results)} LDAP command(s); stored {len(findings)} finding(s).")
                return

            if args.command == "vuln" and args.vuln_command == "import":
                catalog = import_vulnerability_catalog(args.input, args.data_dir)
                print(f"Imported {len(catalog.advisories)} vulnerability advisory item(s).")
                return

            if args.command == "vuln" and args.vuln_command == "list":
                catalog = load_vulnerability_catalog(args.data_dir)
                if args.format == "json":
                    print(format_vulnerability_catalog_json(catalog))
                else:
                    print(format_vulnerability_catalog_text(catalog))
                return

            if args.command == "vuln" and args.vuln_command == "correlate":
                matches = correlate_vulnerability_catalog(args.mission_id, args.data_dir)
                if args.store_findings:
                    stored = store_vulnerability_findings_for_mission(
                        args.mission_id,
                        args.data_dir,
                    )
                    print(f"Stored {len(stored)} vulnerability finding(s).")
                if args.format == "json":
                    print(format_vulnerability_correlation_json(matches))
                else:
                    print(format_vulnerability_correlation_text(matches))
                return

            if args.command == "report" and args.report_command == "generate":
                for path in generate_mission_reports(
                    mission_id=args.mission_id,
                    data_dir=args.data_dir,
                    output=args.output,
                ):
                    print(path)
                return
        except (FileNotFoundError, RuntimeError, ValueError, ValidationError) as error:
            parser.exit(2, f"error: {format_cli_error(error)}\n")

        parser.print_help()


if __name__ == "__main__":
    app()
