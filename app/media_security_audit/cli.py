"""CLI entrypoint for MEDIA Security Audit Platform."""

from __future__ import annotations

import argparse
from pathlib import Path

from pydantic import ValidationError

from media_security_audit import __version__
from media_security_audit.models import (
    AuditType,
    Client,
    Finding,
    ReportFormat,
    ScopeEnvironment,
    ScopeItem,
    ScopeType,
    Severity,
)
from media_security_audit.reports import write_report
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
from media_security_audit.scanners.nmap import (
    NmapCommandBuilder,
    NmapExecutionResult,
    NmapExecutor,
    findings_from_hosts,
    parse_nmap_xml_file,
    render_command,
)
from media_security_audit.storage import JsonStore


def generate_sample_reports(output: Path) -> None:
    mission = sample_mission()
    findings = sample_findings()
    for report_format in (ReportFormat.JSON, ReportFormat.MARKDOWN, ReportFormat.HTML):
        write_report(mission, findings, output, report_format)


def run_web_interface(data_dir: Path, host: str = "127.0.0.1", port: int = 8080) -> None:
    from media_security_audit.web import run_web_server

    run_web_server(data_dir=data_dir, host=host, port=port)


def create_client(name: str, data_dir: Path, reference: str | None = None, notes: str | None = None) -> Client:
    store = JsonStore(data_dir)
    return store.create_client(Client(name=name, internal_reference=reference, notes=notes))


def create_mission(
    client_id: str,
    name: str,
    data_dir: Path,
    audit_type: AuditType = AuditType.MIXED,
    authorization_reference: str | None = None,
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

    return "\n".join(
        [
            f"Mission: {mission.name}",
            f"ID: {mission.id}",
            f"Client ID: {mission.client_id}",
            f"Audit type: {mission.audit_type.value}",
            f"Status: {mission.status.value}",
            f"Authorization: {mission.authorization_reference or 'missing'}",
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
        for report_format in (ReportFormat.JSON, ReportFormat.MARKDOWN, ReportFormat.HTML)
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
    results = [nmap_executor.run(command) for command in commands]
    failed = [result for result in results if result.exit_code != 0]
    if failed:
        first = failed[0]
        raise RuntimeError(f"Nmap command failed with exit code {first.exit_code}: {first.stderr}")

    findings: list[Finding] = []
    for result in results:
        if result.output_path is not None and result.output_path.exists():
            findings.extend(findings_from_hosts(parse_nmap_xml_file(result.output_path)))

    stored_findings = store.add_findings(mission_id, findings)
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
    for target in targets:
        findings.extend(audit_http_headers(http_fetcher(target)))

    return store.add_findings(mission_id, findings)


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
    for domain in domains:
        findings.extend(audit_dns_mail_domain(domain, txt_resolver, dkim_selectors))

    return store.add_findings(mission_id, findings)


def format_cli_error(error: Exception) -> str:
    if isinstance(error, ValidationError):
        messages = [item["msg"] for item in error.errors()]
        return "validation failed: " + "; ".join(messages)
    return str(error)


try:
    import typer

    app = typer.Typer(help="MEDIA Security Audit Platform CLI.")
    client_app = typer.Typer(help="Manage clients.")
    mission_app = typer.Typer(help="Manage missions.")
    scope_app = typer.Typer(help="Manage mission scope.")
    finding_app = typer.Typer(help="Manage findings.")
    scan_app = typer.Typer(help="Plan safe scanner commands.")
    report_app = typer.Typer(help="Generate reports.")
    app.add_typer(client_app, name="client")
    app.add_typer(mission_app, name="mission")
    app.add_typer(scope_app, name="scope")
    app.add_typer(finding_app, name="finding")
    app.add_typer(scan_app, name="scan")
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
        host: str = typer.Option("127.0.0.1", "--host"),
        port: int = typer.Option(8080, "--port"),
    ) -> None:
        """Start the local read-only web interface."""
        try:
            run_web_interface(data_dir=data_dir, host=host, port=port)
        except RuntimeError as error:
            typer.echo(f"error: {error}", err=True)
            raise typer.Exit(code=2) from error

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
        notes: str | None = typer.Option(None, "--notes"),
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
    ) -> None:
        mission = create_mission(
            client_id=client_id,
            name=name,
            audit_type=audit_type,
            authorization_reference=authorization_reference,
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
            help="Start the local read-only web interface.",
        )
        web_parser.add_argument("--data-dir", type=Path, default=Path("data"))
        web_parser.add_argument("--host", default="127.0.0.1")
        web_parser.add_argument("--port", type=int, default=8080)

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
        mission_create_parser.add_argument("--notes")
        mission_create_parser.add_argument("--data-dir", type=Path, default=Path("data"))
        mission_list_parser = mission_subparsers.add_parser("list", help="List missions.")
        mission_list_parser.add_argument("--data-dir", type=Path, default=Path("data"))
        mission_show_parser = mission_subparsers.add_parser("show", help="Show mission details.")
        mission_show_parser.add_argument("--mission-id", required=True)
        mission_show_parser.add_argument("--data-dir", type=Path, default=Path("data"))

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
                run_web_interface(data_dir=args.data_dir, host=args.host, port=args.port)
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
