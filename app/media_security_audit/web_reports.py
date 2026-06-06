"""Persistent report exports for the local web interface."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from media_security_audit.models import ReportFormat
from media_security_audit.reports import MISSION_REPORT_FORMATS, write_report
from media_security_audit.storage import JsonStore


REPORT_EXTENSIONS: dict[ReportFormat, str] = {
    ReportFormat.JSON: "json",
    ReportFormat.MARKDOWN: "md",
    ReportFormat.HTML: "html",
    ReportFormat.PDF: "pdf",
}


@dataclass(frozen=True)
class GeneratedReportLink:
    format: str
    filename: str
    size_bytes: int


def mission_report_dir(reports_dir: Path, mission_id: str) -> Path:
    return reports_dir / mission_id


def mission_report_path(reports_dir: Path, mission_id: str, report_format: ReportFormat) -> Path:
    return mission_report_dir(reports_dir, mission_id) / f"{mission_id}.{REPORT_EXTENSIONS[report_format]}"


def generate_web_reports(store: JsonStore, mission_id: str, reports_dir: Path) -> list[Path]:
    mission = store.get_mission(mission_id)
    findings = store.list_findings(mission_id)
    output_dir = mission_report_dir(reports_dir, mission_id)
    reports = [
        write_report(mission, findings, output_dir, report_format)
        for report_format in MISSION_REPORT_FORMATS
    ]
    return [Path(report.output_path or "") for report in reports]


def list_generated_reports(mission_id: str, reports_dir: Path) -> list[GeneratedReportLink]:
    links = []
    for report_format in MISSION_REPORT_FORMATS:
        path = mission_report_path(reports_dir, mission_id, report_format)
        if path.exists() and path.is_file():
            links.append(
                GeneratedReportLink(
                    format=report_format.value,
                    filename=path.name,
                    size_bytes=path.stat().st_size,
                )
            )
    return links


def generated_report_file(reports_dir: Path, mission_id: str, report_format: ReportFormat) -> Path:
    path = mission_report_path(reports_dir, mission_id, report_format)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"report not found: {report_format.value}")
    return path
