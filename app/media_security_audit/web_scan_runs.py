"""Guarded scan execution helpers for the local web UI."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from media_security_audit.cli import (
    run_dns_mail_audit,
    run_http_headers_audit,
    run_ldap_audit,
    run_nmap_scan,
    run_smb_audit,
    run_tls_audit,
)
from media_security_audit.models import AuditCheck
from media_security_audit.storage import JsonStore
from media_security_audit.web_forms import parse_checkbox
from media_security_audit.web_readiness import ScanPlanPreview, build_scan_plan_previews


WebScanRunner = Callable[[str, Path, Path], None]


@dataclass(frozen=True)
class WebScanRunResult:
    check: AuditCheck
    label: str
    run_status: str
    command_count: int
    finding_count: int


def run_web_scan_check_from_form(
    mission_id: str,
    data_dir: Path,
    runs_dir: Path,
    form: dict[str, str],
    runners: Mapping[AuditCheck, WebScanRunner] | None = None,
) -> WebScanRunResult:
    return run_web_scan_check(
        mission_id=mission_id,
        data_dir=data_dir,
        runs_dir=runs_dir,
        check=parse_web_scan_check(form.get("check", "")),
        confirmed=parse_checkbox(form, "execute_confirm"),
        runners=runners,
    )


def run_web_scan_check(
    mission_id: str,
    data_dir: Path,
    runs_dir: Path,
    check: AuditCheck,
    confirmed: bool,
    runners: Mapping[AuditCheck, WebScanRunner] | None = None,
) -> WebScanRunResult:
    if not confirmed:
        raise ValueError("explicit scan execution confirmation is required")

    store = JsonStore(data_dir)
    mission = store.get_mission(mission_id)
    if check not in mission.selected_checks:
        raise ValueError(f"{check.value} is not selected for this mission")

    preview = scan_plan_preview_for_check(mission_id, data_dir, check)
    if preview.status != "ready":
        raise ValueError(f"{preview.label} is not ready: {preview.detail}")

    runner = (runners or DEFAULT_WEB_SCAN_RUNNERS).get(check)
    if runner is None:
        raise ValueError(f"{check.value} cannot be executed from the web UI yet")

    before_finding_count = len(store.list_findings(mission_id))
    runner(mission_id, data_dir, runs_dir / mission_id / "evidence")

    updated_store = JsonStore(data_dir)
    after_finding_count = len(updated_store.list_findings(mission_id))
    scan_runs = updated_store.list_scan_runs(mission_id)
    if not scan_runs:
        raise RuntimeError(f"{check.value} completed without recording a scan run")
    latest_run = scan_runs[0]
    return WebScanRunResult(
        check=check,
        label=preview.label,
        run_status=latest_run.status.value,
        command_count=latest_run.command_count,
        finding_count=max(after_finding_count - before_finding_count, 0),
    )


def parse_web_scan_check(value: str) -> AuditCheck:
    try:
        return AuditCheck(value.strip())
    except ValueError as error:
        raise ValueError(f"unsupported audit check: {value}") from error


def scan_plan_preview_for_check(
    mission_id: str,
    data_dir: Path,
    check: AuditCheck,
) -> ScanPlanPreview:
    mission = JsonStore(data_dir).get_mission(mission_id)
    previews = {
        selected_check: preview
        for selected_check, preview in zip(
            mission.selected_checks,
            build_scan_plan_previews(mission),
        )
    }
    if check not in previews:
        raise ValueError(f"{check.value} is not available in the current scan plan")
    return previews[check]


def run_nmap_web_check(mission_id: str, data_dir: Path, evidence_dir: Path) -> None:
    run_nmap_scan(
        mission_id=mission_id,
        data_dir=data_dir,
        output_dir=evidence_dir,
        execute=True,
    )


def run_http_web_check(mission_id: str, data_dir: Path, evidence_dir: Path) -> None:
    _ = evidence_dir
    run_http_headers_audit(mission_id=mission_id, data_dir=data_dir, execute=True)


def run_dns_mail_web_check(mission_id: str, data_dir: Path, evidence_dir: Path) -> None:
    _ = evidence_dir
    run_dns_mail_audit(mission_id=mission_id, data_dir=data_dir, execute=True)


def run_tls_web_check(mission_id: str, data_dir: Path, evidence_dir: Path) -> None:
    run_tls_audit(
        mission_id=mission_id,
        data_dir=data_dir,
        output_dir=evidence_dir,
        execute=True,
    )


def run_smb_web_check(mission_id: str, data_dir: Path, evidence_dir: Path) -> None:
    run_smb_audit(
        mission_id=mission_id,
        data_dir=data_dir,
        output_dir=evidence_dir,
        execute=True,
    )


def run_ldap_web_check(mission_id: str, data_dir: Path, evidence_dir: Path) -> None:
    run_ldap_audit(
        mission_id=mission_id,
        data_dir=data_dir,
        output_dir=evidence_dir,
        execute=True,
    )


DEFAULT_WEB_SCAN_RUNNERS: dict[AuditCheck, WebScanRunner] = {
    AuditCheck.NMAP: run_nmap_web_check,
    AuditCheck.HTTP_HEADERS: run_http_web_check,
    AuditCheck.DNS_MAIL: run_dns_mail_web_check,
    AuditCheck.TLS: run_tls_web_check,
    AuditCheck.SMB: run_smb_web_check,
    AuditCheck.LDAP: run_ldap_web_check,
}
