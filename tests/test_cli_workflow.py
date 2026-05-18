from __future__ import annotations

import io
import json
import os
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
    generate_mission_reports,
    list_scope,
    plan_dns_mail_audit,
    plan_http_headers_audit,
    plan_nmap_scan,
    run_dns_mail_audit,
    run_http_headers_audit,
    run_nmap_scan,
    show_mission,
)
from media_security_audit.models import AuditType, MissionStatus, ScopeType, Severity  # noqa: E402
from media_security_audit.scanners.http_headers import HttpHeaderResponse  # noqa: E402
from media_security_audit.scanners.nmap import NmapExecutor, nmap_output_path  # noqa: E402
from media_security_audit.storage import JsonStore  # noqa: E402


class CliWorkflowTests(unittest.TestCase):
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
        self.assertEqual(len(reports), 3)
        self.assertTrue(all(path.exists() for path in reports))
        self.assertIn("Missing HSTS", (output_dir / f"{mission.id}.md").read_text(encoding="utf-8"))

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
        self.assertEqual([run.check.value for run in runs], ["nmap", "dns_mail", "http_headers"])
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

    def test_missing_mission_error_is_readable(self) -> None:
        data_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / "cli-errors"
        stderr = io.StringIO()

        with self.assertRaises(SystemExit) as error, redirect_stderr(stderr):
            app(["mission", "show", "--mission-id", "missing", "--data-dir", str(data_dir)])

        self.assertEqual(error.exception.code, 2)
        self.assertIn("error: mission not found: missing", stderr.getvalue())

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

        self.assertIn(payload["status"], {"ready", "warning"})
        self.assertTrue(
            any(
                item["category"] == "storage"
                and item["label"] == "Data directory"
                for item in payload["items"]
            )
        )


if __name__ == "__main__":
    unittest.main()
