from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.cli import (  # noqa: E402
    add_finding,
    add_scope,
    app,
    create_client,
    create_mission,
    format_scan_plan_json,
    format_scan_plan_text,
    generate_mission_reports,
    list_scope,
    plan_all_scans,
    plan_dns_mail_audit,
    plan_http_headers_audit,
    plan_ldap_audit,
    plan_nmap_scan,
    plan_smb_audit,
    plan_tls_audit,
    run_dns_mail_audit,
    run_http_headers_audit,
    run_ldap_audit,
    run_nmap_scan,
    run_smb_audit,
    run_tls_audit,
    show_mission,
)
from media_security_audit.models import (  # noqa: E402
    AuditCheck,
    AuditType,
    FindingStatus,
    MissionStatus,
    ScopeType,
    Severity,
)
from media_security_audit.scanners.http_headers import HttpHeaderResponse  # noqa: E402
from media_security_audit.scanners.ldap import LdapExecutor  # noqa: E402
from media_security_audit.scanners.nmap import NmapExecutor, nmap_output_path  # noqa: E402
from media_security_audit.scanners.smb import SmbExecutor  # noqa: E402
from media_security_audit.scanners.testssl import TestsslExecutor, testssl_output_path  # noqa: E402
from media_security_audit.storage import JsonStore  # noqa: E402
from media_security_audit.web_exports import generate_mission_export  # noqa: E402
from media_security_audit.web_reports import generate_web_reports  # noqa: E402


class CliWorkflowTests(unittest.TestCase):
    def test_typer_options_do_not_use_date_annotations(self) -> None:
        cli_path = Path(__file__).resolve().parents[1] / "app" / "media_security_audit" / "cli.py"
        source = cli_path.read_text(encoding="utf-8")

        self.assertNotIn(": date | None = typer.Option", source)
        self.assertNotIn(": datetime.date | None = typer.Option", source)

    def test_typer_command_graph_builds(self) -> None:
        try:
            from typer.main import get_command
        except ModuleNotFoundError:
            self.skipTest("typer is not installed")

        command = get_command(app)

        self.assertIn("preflight", command.commands)
        self.assertIn("mission", command.commands)
        self.assertIn("vuln", command.commands)

    def test_creates_basic_local_workflow(self) -> None:
        root_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / "cli-workflow"
        data_dir = root_dir / "data"
        output_dir = root_dir / "reports"

        client = create_client(name="Client X", data_dir=data_dir)
        mission = create_mission(
            client_id=client.id,
            name="External audit",
            audit_type=AuditType.EXTERNAL,
            authorization_reference="signed-order",
            authorization_contact="Jane Sponsor",
            authorization_date=date(2026, 5, 10),
            authorization_expires_at=date(2026, 6, 10),
            emergency_contact="security@example.invalid",
            report_recipients="owner@example.invalid",
            evidence_retention_days=90,
            data_dir=data_dir,
        )
        updated = add_scope(
            mission_id=mission.id,
            scope_type=ScopeType.DOMAIN,
            value="example.invalid",
            approved=True,
            data_dir=data_dir,
        )
        add_scope(
            mission_id=mission.id,
            scope_type=ScopeType.URL,
            value="https://example.invalid",
            approved=True,
            data_dir=data_dir,
        )
        finding = add_finding(
            mission_id=mission.id,
            title="Missing HSTS",
            severity=Severity.MEDIUM,
            affected_asset="https://example.invalid",
            category="http_headers",
            proof="HSTS header is absent.",
            risk="Users may be exposed to downgrade attempts.",
            remediation="Enable the Strict-Transport-Security header.",
            counter_test="Request the URL and confirm the HSTS header is present.",
            data_dir=data_dir,
        )
        reports = generate_mission_reports(
            mission_id=mission.id,
            data_dir=data_dir,
            output=output_dir,
        )

        self.assertEqual(updated.status, MissionStatus.READY_TO_SCAN)
        self.assertEqual(finding.title, "Missing HSTS")
        self.assertEqual(len(reports), 4)
        self.assertTrue(all(path.exists() for path in reports))
        self.assertIn("Missing HSTS", (output_dir / f"{mission.id}.md").read_text(encoding="utf-8"))
        self.assertTrue((output_dir / f"{mission.id}.pdf").read_bytes().startswith(b"%PDF-1.4"))

        summary = show_mission(mission_id=mission.id, data_dir=data_dir)
        scope_items = list_scope(mission_id=mission.id, data_dir=data_dir)

        self.assertIn("Status: ready_to_scan", summary)
        self.assertIn("Authorization contact: Jane Sponsor", summary)
        self.assertIn("Evidence retention days: 90", summary)
        self.assertIn("Findings: 1", summary)
        self.assertEqual(len(scope_items), 2)
        self.assertEqual(scope_items[0].value, "example.invalid")

        commands = plan_nmap_scan(mission_id=mission.id, data_dir=data_dir)
        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0][0], "nmap")
        self.assertEqual(commands[0][-1], "example.invalid")
        self.assertIn("-oX", commands[0])

        http_targets = plan_http_headers_audit(mission_id=mission.id, data_dir=data_dir)
        self.assertEqual(http_targets, ["https://example.invalid"])

        http_findings = run_http_headers_audit(
            mission_id=mission.id,
            data_dir=data_dir,
            execute=True,
            fetcher=lambda url: HttpHeaderResponse(url=url, status_code=200, headers={}),
        )
        self.assertTrue(any(finding.category == "http_headers" for finding in http_findings))

        dns_queries = plan_dns_mail_audit(
            mission_id=mission.id,
            data_dir=data_dir,
            dkim_selectors=["default"],
        )
        self.assertEqual(
            dns_queries,
            [
                "TXT example.invalid",
                "TXT _dmarc.example.invalid",
                "TXT default._domainkey.example.invalid",
            ],
        )

        dns_records = {
            "example.invalid": ["v=spf1 +all"],
            "_dmarc.example.invalid": ["v=DMARC1; p=none"],
            "default._domainkey.example.invalid": [],
        }
        dns_findings = run_dns_mail_audit(
            mission_id=mission.id,
            data_dir=data_dir,
            execute=True,
            dkim_selectors=["default"],
            resolver=lambda name: dns_records.get(name, []),
        )
        self.assertTrue(any(finding.category == "dns_mail" for finding in dns_findings))

        tls_commands = plan_tls_audit(
            mission_id=mission.id,
            data_dir=data_dir,
            output_dir=root_dir / "evidence",
        )
        self.assertEqual(len(tls_commands), 1)
        self.assertEqual(tls_commands[0][0], "testssl.sh")
        self.assertEqual(tls_commands[0][-1], "example.invalid")

        tls_fixture = Path(__file__).parent / "fixtures" / "testssl_sample.json"

        def tls_runner(
            command: list[str],
            timeout_seconds: int,
        ) -> subprocess.CompletedProcess[str]:
            output_path = testssl_output_path(command)
            assert output_path is not None
            output_path.write_text(tls_fixture.read_text(encoding="utf-8"), encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, "", "")

        tls_results, tls_findings = run_tls_audit(
            mission_id=mission.id,
            data_dir=data_dir,
            output_dir=root_dir / "evidence",
            execute=True,
            executor=TestsslExecutor(
                runner=tls_runner,
                executable_lookup=lambda executable: f"/usr/bin/{executable}",
            ),
        )
        self.assertEqual(len(tls_results), 1)
        self.assertTrue(any(finding.category == "tls" for finding in tls_findings))

        smb_commands = plan_smb_audit(mission_id=mission.id, data_dir=data_dir)
        self.assertEqual(len(smb_commands), 1)
        self.assertEqual(smb_commands[0][0], "smbclient")
        self.assertEqual(smb_commands[0][2], "//example.invalid")

        smb_fixture = Path(__file__).parent / "fixtures" / "smbclient_list_sample.txt"

        def smb_runner(
            command: list[str],
            timeout_seconds: int,
        ) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(
                command,
                0,
                smb_fixture.read_text(encoding="utf-8"),
                "",
            )

        smb_results, smb_findings = run_smb_audit(
            mission_id=mission.id,
            data_dir=data_dir,
            output_dir=root_dir / "evidence",
            execute=True,
            executor=SmbExecutor(
                runner=smb_runner,
                executable_lookup=lambda executable: f"/usr/bin/{executable}",
            ),
        )
        self.assertEqual(len(smb_results), 1)
        self.assertTrue(any(finding.category == "smb" for finding in smb_findings))

        ldap_commands = plan_ldap_audit(mission_id=mission.id, data_dir=data_dir)
        self.assertEqual(len(ldap_commands), 1)
        self.assertEqual(ldap_commands[0][0], "ldapsearch")
        self.assertEqual(ldap_commands[0][4], "ldap://example.invalid")

        ldap_fixture = Path(__file__).parent / "fixtures" / "ldap_rootdse_sample.ldif"

        def ldap_runner(
            command: list[str],
            timeout_seconds: int,
        ) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(
                command,
                0,
                ldap_fixture.read_text(encoding="utf-8"),
                "",
            )

        ldap_results, ldap_findings = run_ldap_audit(
            mission_id=mission.id,
            data_dir=data_dir,
            output_dir=root_dir / "evidence",
            execute=True,
            executor=LdapExecutor(
                runner=ldap_runner,
                executable_lookup=lambda executable: f"/usr/bin/{executable}",
            ),
        )
        self.assertEqual(len(ldap_results), 1)
        self.assertTrue(any(finding.category == "ldap" for finding in ldap_findings))

        fixture = Path(__file__).parent / "fixtures" / "nmap_sample.xml"

        def runner(command: list[str], timeout_seconds: int) -> subprocess.CompletedProcess[str]:
            output_path = nmap_output_path(command)
            assert output_path is not None
            output_path.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, "", "")

        results, findings = run_nmap_scan(
            mission_id=mission.id,
            data_dir=data_dir,
            output_dir=root_dir / "evidence",
            execute=True,
            executor=NmapExecutor(
                runner=runner,
                executable_lookup=lambda executable: f"/usr/bin/{executable}",
            ),
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(len(findings), 2)
        self.assertTrue(any("RDP" in finding.title for finding in findings))

        runs = JsonStore(data_dir).list_scan_runs(mission.id)
        self.assertEqual(
            [run.check.value for run in runs],
            ["nmap", "ldap", "smb", "tls", "dns_mail", "http_headers"],
        )
        self.assertTrue(all(run.status.value == "completed" for run in runs))
        self.assertEqual(runs[0].finding_count, 2)

    def test_nmap_run_requires_execute_flag(self) -> None:
        root_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / "cli-nmap-guard"
        data_dir = root_dir / "data"

        client = create_client(name="Client X", data_dir=data_dir)
        mission = create_mission(
            client_id=client.id,
            name="External audit",
            audit_type=AuditType.EXTERNAL,
            authorization_reference="signed-order",
            data_dir=data_dir,
        )
        add_scope(
            mission_id=mission.id,
            scope_type=ScopeType.DOMAIN,
            value="example.invalid",
            approved=True,
            data_dir=data_dir,
        )

        with self.assertRaises(ValueError) as error:
            run_nmap_scan(mission_id=mission.id, data_dir=data_dir)

        self.assertIn("without --execute", str(error.exception))

    def test_nmap_run_requires_authorization(self) -> None:
        root_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / "cli-nmap-auth"
        data_dir = root_dir / "data"

        client = create_client(name="Client X", data_dir=data_dir)
        mission = create_mission(
            client_id=client.id,
            name="External audit",
            audit_type=AuditType.EXTERNAL,
            data_dir=data_dir,
        )
        add_scope(
            mission_id=mission.id,
            scope_type=ScopeType.DOMAIN,
            value="example.invalid",
            approved=True,
            data_dir=data_dir,
        )

        with self.assertRaises(ValueError) as error:
            run_nmap_scan(mission_id=mission.id, data_dir=data_dir, execute=True)

        self.assertIn("authorization is required", str(error.exception))

    def test_http_run_requires_execute_flag(self) -> None:
        root_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / "cli-http-guard"
        data_dir = root_dir / "data"

        client = create_client(name="Client X", data_dir=data_dir)
        mission = create_mission(
            client_id=client.id,
            name="External audit",
            audit_type=AuditType.EXTERNAL,
            authorization_reference="signed-order",
            data_dir=data_dir,
        )
        add_scope(
            mission_id=mission.id,
            scope_type=ScopeType.URL,
            value="https://example.invalid",
            approved=True,
            data_dir=data_dir,
        )

        with self.assertRaises(ValueError) as error:
            run_http_headers_audit(mission_id=mission.id, data_dir=data_dir)

        self.assertIn("without --execute", str(error.exception))

    def test_http_run_records_failed_execution(self) -> None:
        root_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / "cli-http-failed-run"
        data_dir = root_dir / "data"

        client = create_client(name="Client X", data_dir=data_dir)
        mission = create_mission(
            client_id=client.id,
            name="External audit",
            audit_type=AuditType.EXTERNAL,
            authorization_reference="signed-order",
            data_dir=data_dir,
        )
        add_scope(
            mission_id=mission.id,
            scope_type=ScopeType.URL,
            value="https://example.invalid",
            approved=True,
            data_dir=data_dir,
        )

        def failing_fetcher(url: str) -> HttpHeaderResponse:
            raise RuntimeError(f"request failed: {url}")

        with self.assertRaises(RuntimeError):
            run_http_headers_audit(
                mission_id=mission.id,
                data_dir=data_dir,
                execute=True,
                fetcher=failing_fetcher,
            )

        runs = JsonStore(data_dir).list_scan_runs(mission.id)

        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0].check.value, "http_headers")
        self.assertEqual(runs[0].status.value, "failed")
        self.assertIn("request failed", runs[0].error or "")

    def test_dns_run_requires_execute_flag(self) -> None:
        root_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / "cli-dns-guard"
        data_dir = root_dir / "data"

        client = create_client(name="Client X", data_dir=data_dir)
        mission = create_mission(
            client_id=client.id,
            name="External audit",
            audit_type=AuditType.EXTERNAL,
            authorization_reference="signed-order",
            data_dir=data_dir,
        )
        add_scope(
            mission_id=mission.id,
            scope_type=ScopeType.DOMAIN,
            value="example.invalid",
            approved=True,
            data_dir=data_dir,
        )

        with self.assertRaises(ValueError) as error:
            run_dns_mail_audit(mission_id=mission.id, data_dir=data_dir)

        self.assertIn("without --execute", str(error.exception))

    def test_tls_run_requires_execute_flag(self) -> None:
        root_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / "cli-tls-guard"
        data_dir = root_dir / "data"

        client = create_client(name="Client X", data_dir=data_dir)
        mission = create_mission(
            client_id=client.id,
            name="External audit",
            audit_type=AuditType.EXTERNAL,
            authorization_reference="signed-order",
            data_dir=data_dir,
        )
        add_scope(
            mission_id=mission.id,
            scope_type=ScopeType.DOMAIN,
            value="example.invalid",
            approved=True,
            data_dir=data_dir,
        )

        with self.assertRaises(ValueError) as error:
            run_tls_audit(mission_id=mission.id, data_dir=data_dir)

        self.assertIn("without --execute", str(error.exception))

    def test_tls_run_records_failed_execution(self) -> None:
        root_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / "cli-tls-failed-run"
        data_dir = root_dir / "data"

        client = create_client(name="Client X", data_dir=data_dir)
        mission = create_mission(
            client_id=client.id,
            name="External audit",
            audit_type=AuditType.EXTERNAL,
            authorization_reference="signed-order",
            data_dir=data_dir,
        )
        add_scope(
            mission_id=mission.id,
            scope_type=ScopeType.DOMAIN,
            value="example.invalid",
            approved=True,
            data_dir=data_dir,
        )

        def failing_runner(
            command: list[str],
            timeout_seconds: int,
        ) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(command, 2, "", "tls failed")

        with self.assertRaises(RuntimeError):
            run_tls_audit(
                mission_id=mission.id,
                data_dir=data_dir,
                execute=True,
                executor=TestsslExecutor(
                    runner=failing_runner,
                    executable_lookup=lambda executable: f"/usr/bin/{executable}",
                ),
            )

        runs = JsonStore(data_dir).list_scan_runs(mission.id)

        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0].check.value, "tls")
        self.assertEqual(runs[0].status.value, "failed")
        self.assertIn("tls failed", runs[0].error or "")

    def test_smb_run_requires_execute_flag(self) -> None:
        root_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / "cli-smb-guard"
        data_dir = root_dir / "data"

        client = create_client(name="Client X", data_dir=data_dir)
        mission = create_mission(
            client_id=client.id,
            name="Internal audit",
            audit_type=AuditType.INTERNAL,
            authorization_reference="signed-order",
            data_dir=data_dir,
        )
        add_scope(
            mission_id=mission.id,
            scope_type=ScopeType.HOST,
            value="fs01.client.local",
            approved=True,
            data_dir=data_dir,
        )

        with self.assertRaises(ValueError) as error:
            run_smb_audit(mission_id=mission.id, data_dir=data_dir)

        self.assertIn("without --execute", str(error.exception))

    def test_smb_run_records_failed_execution(self) -> None:
        root_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / "cli-smb-failed-run"
        data_dir = root_dir / "data"

        client = create_client(name="Client X", data_dir=data_dir)
        mission = create_mission(
            client_id=client.id,
            name="Internal audit",
            audit_type=AuditType.INTERNAL,
            authorization_reference="signed-order",
            data_dir=data_dir,
        )
        add_scope(
            mission_id=mission.id,
            scope_type=ScopeType.HOST,
            value="fs01.client.local",
            approved=True,
            data_dir=data_dir,
        )

        def failing_runner(
            command: list[str],
            timeout_seconds: int,
        ) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(command, 1, "", "anonymous listing denied")

        with self.assertRaises(RuntimeError):
            run_smb_audit(
                mission_id=mission.id,
                data_dir=data_dir,
                execute=True,
                executor=SmbExecutor(
                    runner=failing_runner,
                    executable_lookup=lambda executable: f"/usr/bin/{executable}",
                ),
            )

        runs = JsonStore(data_dir).list_scan_runs(mission.id)

        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0].check.value, "smb")
        self.assertEqual(runs[0].status.value, "failed")
        self.assertIn("anonymous listing denied", runs[0].error or "")

    def test_ldap_run_requires_execute_flag(self) -> None:
        root_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / "cli-ldap-guard"
        data_dir = root_dir / "data"

        client = create_client(name="Client X", data_dir=data_dir)
        mission = create_mission(
            client_id=client.id,
            name="Internal audit",
            audit_type=AuditType.INTERNAL,
            authorization_reference="signed-order",
            data_dir=data_dir,
        )
        add_scope(
            mission_id=mission.id,
            scope_type=ScopeType.HOST,
            value="dc01.client.local",
            approved=True,
            data_dir=data_dir,
        )

        with self.assertRaises(ValueError) as error:
            run_ldap_audit(mission_id=mission.id, data_dir=data_dir)

        self.assertIn("without --execute", str(error.exception))

    def test_ldap_run_records_failed_execution(self) -> None:
        root_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / "cli-ldap-failed-run"
        data_dir = root_dir / "data"

        client = create_client(name="Client X", data_dir=data_dir)
        mission = create_mission(
            client_id=client.id,
            name="Internal audit",
            audit_type=AuditType.INTERNAL,
            authorization_reference="signed-order",
            data_dir=data_dir,
        )
        add_scope(
            mission_id=mission.id,
            scope_type=ScopeType.HOST,
            value="dc01.client.local",
            approved=True,
            data_dir=data_dir,
        )

        def failing_runner(
            command: list[str],
            timeout_seconds: int,
        ) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(command, 49, "", "invalid credentials")

        with self.assertRaises(RuntimeError):
            run_ldap_audit(
                mission_id=mission.id,
                data_dir=data_dir,
                execute=True,
                executor=LdapExecutor(
                    runner=failing_runner,
                    executable_lookup=lambda executable: f"/usr/bin/{executable}",
                ),
            )

        runs = JsonStore(data_dir).list_scan_runs(mission.id)

        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0].check.value, "ldap")
        self.assertEqual(runs[0].status.value, "failed")
        self.assertIn("invalid credentials", runs[0].error or "")

    def test_scan_plan_all_formats_selected_checks_without_execution(self) -> None:
        root_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / "cli-plan-all"
        data_dir = root_dir / "data"

        client = create_client(name="Client X", data_dir=data_dir)
        mission = create_mission(
            client_id=client.id,
            name="Mixed audit",
            audit_type=AuditType.MIXED,
            authorization_reference="signed-order",
            data_dir=data_dir,
        )
        add_scope(
            mission_id=mission.id,
            scope_type=ScopeType.DOMAIN,
            value="client.example",
            approved=True,
            data_dir=data_dir,
        )
        add_scope(
            mission_id=mission.id,
            scope_type=ScopeType.URL,
            value="https://client.example",
            approved=True,
            data_dir=data_dir,
        )
        add_scope(
            mission_id=mission.id,
            scope_type=ScopeType.HOST,
            value="dc01.client.local",
            approved=True,
            data_dir=data_dir,
        )
        store = JsonStore(data_dir)
        selected = [
            AuditCheck.NMAP,
            AuditCheck.HTTP_HEADERS,
            AuditCheck.DNS_MAIL,
            AuditCheck.TLS,
            AuditCheck.SMB,
            AuditCheck.LDAP,
        ]
        mission = store.save_mission(
            store.get_mission(mission.id).model_copy(update={"selected_checks": selected})
        )

        plans = plan_all_scans(mission_id=mission.id, data_dir=data_dir)
        payload = json.loads(format_scan_plan_json(mission_id=mission.id, data_dir=data_dir))
        text = format_scan_plan_text(mission_id=mission.id, data_dir=data_dir)

        self.assertEqual(
            [plan.label for plan in plans],
            ["Nmap", "HTTP Headers", "DNS/Mail", "TLS", "SMB", "LDAP"],
        )
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["mission"]["id"], mission.id)
        self.assertEqual(payload["summary"]["execution"], "not_executed")
        self.assertEqual(payload["summary"]["ready"], 6)
        self.assertGreaterEqual(payload["summary"]["planned_commands"], 6)
        self.assertTrue(all(item["status"] == "ready" for item in payload["plans"]))
        self.assertIn("Execution: not executed by this command", text)
        self.assertIn("[ready] LDAP", text)
        self.assertIn("ldapsearch -x -LLL", text)

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            app(
                [
                    "scan",
                    "plan-all",
                    "--mission-id",
                    mission.id,
                    "--data-dir",
                    str(data_dir),
                    "--format",
                    "json",
                ]
            )

        cli_payload = json.loads(stdout.getvalue())
        self.assertEqual(cli_payload["summary"]["execution"], "not_executed")
        self.assertEqual(JsonStore(data_dir).list_scan_runs(mission.id), [])

    def test_missing_mission_error_is_readable(self) -> None:
        data_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / "cli-errors"
        stderr = io.StringIO()

        with self.assertRaises(SystemExit) as error, redirect_stderr(stderr):
            app(["mission", "show", "--mission-id", "missing", "--data-dir", str(data_dir)])

        self.assertEqual(error.exception.code, 2)
        self.assertIn("error: mission not found: missing", stderr.getvalue())

    def test_mission_readiness_json_command_is_machine_readable(self) -> None:
        root_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / "cli-mission-readiness-json"
        data_dir = root_dir / "data"
        reports_dir = root_dir / "reports"
        client = create_client(name="Client Readiness", data_dir=data_dir)
        mission = create_mission(
            client_id=client.id,
            name="Readiness Audit",
            authorization_reference="AUTH-READY",
            data_dir=data_dir,
        )
        add_scope(
            mission_id=mission.id,
            scope_type=ScopeType.DOMAIN,
            value="client.example",
            approved=True,
            data_dir=data_dir,
        )
        add_finding(
            mission_id=mission.id,
            title="Reviewed finding",
            severity=Severity.LOW,
            affected_asset="client.example",
            category="manual",
            proof="Reviewed evidence.",
            risk="Known low risk.",
            remediation="Apply remediation.",
            counter_test="Repeat approved checks.",
            data_dir=data_dir,
        )
        finding = JsonStore(data_dir).list_findings(mission.id)[0]
        finding.status = FindingStatus.CONFIRMED
        JsonStore(data_dir).save_finding(mission.id, finding)
        generate_web_reports(JsonStore(data_dir), mission.id, reports_dir)
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            app(
                [
                    "mission",
                    "readiness",
                    "--mission-id",
                    mission.id,
                    "--data-dir",
                    str(data_dir),
                    "--reports-dir",
                    str(reports_dir),
                    "--format",
                    "json",
                ]
            )

        payload = json.loads(stdout.getvalue())

        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["summary"]["execution"], "not_executed")
        self.assertEqual(payload["summary"]["generated_reports"], 4)
        self.assertEqual(payload["scan_plan"]["execution"], "not_executed")
        self.assertEqual(JsonStore(data_dir).list_scan_runs(mission.id), [])

    def test_mission_export_verify_json_command_is_machine_readable(self) -> None:
        root_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / "cli-mission-export-verify-json"
        data_dir = root_dir / "data"
        reports_dir = root_dir / "reports"
        client = create_client(name="Client Export Verify", data_dir=data_dir)
        mission = create_mission(
            client_id=client.id,
            name="Export Verify Audit",
            authorization_reference="AUTH-VERIFY",
            data_dir=data_dir,
        )
        add_scope(
            mission_id=mission.id,
            scope_type=ScopeType.DOMAIN,
            value="client.example",
            approved=True,
            data_dir=data_dir,
        )
        generate_web_reports(JsonStore(data_dir), mission.id, reports_dir)
        generate_mission_export(JsonStore(data_dir), mission.id, reports_dir)
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            app(
                [
                    "mission",
                    "export-verify",
                    "--mission-id",
                    mission.id,
                    "--reports-dir",
                    str(reports_dir),
                    "--format",
                    "json",
                ]
            )

        payload = json.loads(stdout.getvalue())

        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["execution"], "not_executed")
        self.assertGreater(payload["summary"]["checked_files"], 0)
        self.assertEqual(payload["summary"]["missing_files"], 0)
        self.assertEqual(payload["summary"]["mismatched_files"], 0)
        self.assertEqual(JsonStore(data_dir).list_scan_runs(mission.id), [])

    def test_mission_export_manifest_command_reads_existing_package(self) -> None:
        root_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / "cli-mission-export-manifest"
        data_dir = root_dir / "data"
        reports_dir = root_dir / "reports"
        client = create_client(name="Client Export Manifest", data_dir=data_dir)
        mission = create_mission(
            client_id=client.id,
            name="Export Manifest Audit",
            authorization_reference="AUTH-MANIFEST",
            data_dir=data_dir,
        )
        add_scope(
            mission_id=mission.id,
            scope_type=ScopeType.DOMAIN,
            value="client.example",
            approved=True,
            data_dir=data_dir,
        )
        generate_web_reports(JsonStore(data_dir), mission.id, reports_dir)
        export_path = generate_mission_export(JsonStore(data_dir), mission.id, reports_dir)
        json_stdout = io.StringIO()
        markdown_stdout = io.StringIO()

        with redirect_stdout(json_stdout):
            app(
                [
                    "mission",
                    "export-manifest",
                    "--mission-id",
                    mission.id,
                    "--reports-dir",
                    str(reports_dir),
                    "--format",
                    "json",
                ]
            )
        with redirect_stdout(markdown_stdout):
            app(
                [
                    "mission",
                    "export-manifest",
                    "--package",
                    str(export_path),
                    "--format",
                    "markdown",
                ]
            )

        payload = json.loads(json_stdout.getvalue())
        markdown = markdown_stdout.getvalue()

        self.assertEqual(payload["manifest_version"], 4)
        self.assertEqual(payload["mission_id"], mission.id)
        self.assertGreater(payload["archive_file_count"], 0)
        self.assertIn("# Mission Export Manifest", markdown)
        self.assertIn("- Execution: `not_executed`", markdown)
        self.assertEqual(JsonStore(data_dir).list_scan_runs(mission.id), [])

    def test_mission_export_inventory_command_lists_packages(self) -> None:
        root_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / "cli-mission-export-inventory"
        if root_dir.exists():
            shutil.rmtree(root_dir)
        data_dir = root_dir / "data"
        reports_dir = root_dir / "reports"
        client = create_client(name="Client Export Inventory", data_dir=data_dir)
        packaged_mission = create_mission(
            client_id=client.id,
            name="Packaged Audit",
            authorization_reference="AUTH-PACKAGED",
            data_dir=data_dir,
        )
        missing_mission = create_mission(
            client_id=client.id,
            name="Missing Package Audit",
            authorization_reference="AUTH-MISSING",
            data_dir=data_dir,
        )
        add_scope(
            mission_id=packaged_mission.id,
            scope_type=ScopeType.DOMAIN,
            value="client.example",
            approved=True,
            data_dir=data_dir,
        )
        generate_web_reports(JsonStore(data_dir), packaged_mission.id, reports_dir)
        generate_mission_export(JsonStore(data_dir), packaged_mission.id, reports_dir)
        json_stdout = io.StringIO()
        text_stdout = io.StringIO()

        with redirect_stdout(json_stdout):
            app(
                [
                    "mission",
                    "export-inventory",
                    "--data-dir",
                    str(data_dir),
                    "--reports-dir",
                    str(reports_dir),
                    "--format",
                    "json",
                    "--include-missing",
                ]
            )
        with redirect_stdout(text_stdout):
            app(
                [
                    "mission",
                    "export-inventory",
                    "--data-dir",
                    str(data_dir),
                    "--reports-dir",
                    str(reports_dir),
                ]
            )

        payload = json.loads(json_stdout.getvalue())
        text = text_stdout.getvalue()
        statuses = {item["mission_id"]: item["status"] for item in payload["items"]}

        self.assertEqual(payload["summary"]["items"], 2)
        self.assertEqual(payload["summary"]["packages"], 1)
        self.assertEqual(payload["summary"]["ready"], 1)
        self.assertEqual(payload["summary"]["missing"], 1)
        self.assertEqual(statuses[packaged_mission.id], "ready")
        self.assertEqual(statuses[missing_mission.id], "missing")
        self.assertIn("Mission export inventory", text)
        self.assertIn(packaged_mission.id, text)
        self.assertNotIn(missing_mission.id, text)
        self.assertEqual(JsonStore(data_dir).list_scan_runs(packaged_mission.id), [])
        self.assertEqual(JsonStore(data_dir).list_scan_runs(missing_mission.id), [])

    def test_mission_export_verify_missing_package_returns_failure(self) -> None:
        root_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / "cli-mission-export-verify-missing"
        stdout = io.StringIO()

        with self.assertRaises(SystemExit) as error, redirect_stdout(stdout):
            app(
                [
                    "mission",
                    "export-verify",
                    "--package",
                    str(root_dir / "missing.zip"),
                ]
            )

        text = stdout.getvalue()

        self.assertEqual(error.exception.code, 1)
        self.assertIn("Mission export verification: failed", text)
        self.assertIn("package cannot be verified", text)
        self.assertIn("Execution: not executed by this command", text)

    def test_preflight_json_command_is_machine_readable(self) -> None:
        root_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / "cli-preflight-json"
        data_dir = root_dir / "data"
        reports_dir = root_dir / "reports"
        data_dir.mkdir(parents=True, exist_ok=True)
        reports_dir.mkdir(parents=True, exist_ok=True)
        stdout = io.StringIO()

        with (
            patch.dict(os.environ, {"MEDIA_AUDIT_REQUIRE_AUTH": "false"}, clear=False),
            redirect_stdout(stdout),
        ):
            app(
                [
                    "preflight",
                    "--data-dir",
                    str(data_dir),
                    "--reports-dir",
                    str(reports_dir),
                    "--format",
                    "json",
                ]
            )

        payload = json.loads(stdout.getvalue())

        self.assertEqual(payload["schema_version"], 1)
        self.assertIn(payload["status"], {"ready", "warning"})
        self.assertIn("ready", payload["summary"])
        self.assertIn("missing", payload["summary"])
        self.assertTrue(all("action" in item for item in payload["items"]))
        self.assertTrue(
            any(
                item["category"] == "storage"
                and item["label"] == "Data directory"
                for item in payload["items"]
            )
        )

    def test_preflight_strict_returns_error_on_warning(self) -> None:
        root_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / "cli-preflight-strict"
        data_dir = root_dir / "data"
        reports_dir = root_dir / "reports"
        data_dir.mkdir(parents=True, exist_ok=True)
        reports_dir.mkdir(parents=True, exist_ok=True)
        stdout = io.StringIO()

        with (
            patch.dict(os.environ, {"MEDIA_AUDIT_REQUIRE_AUTH": "false"}, clear=False),
            redirect_stdout(stdout),
            self.assertRaises(SystemExit) as error,
        ):
            app(
                [
                    "preflight",
                    "--data-dir",
                    str(data_dir),
                    "--reports-dir",
                    str(reports_dir),
                    "--strict",
                ]
            )

        self.assertEqual(error.exception.code, 1)
        self.assertIn("Deployment preflight: warning", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
