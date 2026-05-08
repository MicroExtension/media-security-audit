"""CLI entrypoint for MEDIA Security Audit Platform."""

from __future__ import annotations

import argparse
from pathlib import Path

from media_security_audit import __version__
from media_security_audit.models import (
    AuditType,
    Client,
    ReportFormat,
    ScopeEnvironment,
    ScopeItem,
    ScopeType,
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


def generate_mission_reports(mission_id: str, data_dir: Path, output: Path | None = None) -> list[Path]:
    store = JsonStore(data_dir)
    mission = store.get_mission(mission_id)
    output_dir = output or Path("runs") / mission.id / "reports"
    findings = []
    reports = [
        write_report(mission, findings, output_dir, report_format)
        for report_format in (ReportFormat.JSON, ReportFormat.MARKDOWN, ReportFormat.HTML)
    ]
    return [Path(report.output_path or "") for report in reports]


try:
    import typer

    app = typer.Typer(help="MEDIA Security Audit Platform CLI.")
    client_app = typer.Typer(help="Manage clients.")
    mission_app = typer.Typer(help="Manage missions.")
    scope_app = typer.Typer(help="Manage mission scope.")
    report_app = typer.Typer(help="Generate reports.")
    app.add_typer(client_app, name="client")
    app.add_typer(mission_app, name="mission")
    app.add_typer(scope_app, name="scope")
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

        report_parser = subparsers.add_parser("report", help="Generate reports.")
        report_subparsers = report_parser.add_subparsers(dest="report_command")
        report_generate_parser = report_subparsers.add_parser("generate", help="Generate empty mission reports.")
        report_generate_parser.add_argument("--mission-id", required=True)
        report_generate_parser.add_argument("--data-dir", type=Path, default=Path("data"))
        report_generate_parser.add_argument("--output", type=Path)

        args = parser.parse_args(argv)

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

        if args.command == "report" and args.report_command == "generate":
            for path in generate_mission_reports(
                mission_id=args.mission_id,
                data_dir=args.data_dir,
                output=args.output,
            ):
                print(path)
            return

        parser.print_help()


if __name__ == "__main__":
    app()
