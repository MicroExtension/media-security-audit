"""CLI entrypoint for MEDIA Security Audit Platform."""

from __future__ import annotations

import argparse
from pathlib import Path

from media_security_audit import __version__
from media_security_audit.reports import write_report
from media_security_audit.models import ReportFormat
from media_security_audit.sample_data import sample_findings, sample_mission


def generate_sample_reports(output: Path) -> None:
    mission = sample_mission()
    findings = sample_findings()
    for report_format in (ReportFormat.JSON, ReportFormat.MARKDOWN, ReportFormat.HTML):
        write_report(mission, findings, output, report_format)


try:
    import typer

    app = typer.Typer(help="MEDIA Security Audit Platform CLI.")

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

        args = parser.parse_args(argv)

        if args.version:
            print(__version__)
            return

        if args.command == "sample-report":
            generate_sample_reports(args.output)
            print(f"Sample reports written to {args.output}")
            return

        parser.print_help()


if __name__ == "__main__":
    app()

