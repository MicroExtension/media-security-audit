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
from media_security_audit.storage import JsonStore


def generate_sample_reports(output: Path) -> None:
    mission = sample_mission()
    findings = sample_findings()
    for report_format in (ReportFormat.JSON, ReportFormat.MARKDOWN, ReportFormat.HTML):
        write_report(mission, findings, output, report_format)


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
    report_app = typer.Typer(help="Generate reports.")
    app.add_typer(client_app, name="client")
    app.add_typer(mission_app, name="mission")
    app.add_typer(scope_app, name="scope")
    app.add_typer(finding_app, name="finding")
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

            if args.command == "report" and args.report_command == "generate":
                for path in generate_mission_reports(
                    mission_id=args.mission_id,
                    data_dir=args.data_dir,
                    output=args.output,
                ):
                    print(path)
                return
        except (FileNotFoundError, ValueError, ValidationError) as error:
            parser.exit(2, f"error: {format_cli_error(error)}\n")

        parser.print_help()


if __name__ == "__main__":
    app()
