from __future__ import annotations

import shutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.models import (  # noqa: E402
    AuditCheck,
    Client,
    Finding,
    Mission,
    ScanRun,
    ScanRunStatus,
    ScopeEnvironment,
    ScopeItem,
    ScopeType,
    Severity,
)
from media_security_audit.storage import JsonStore  # noqa: E402
from media_security_audit.web_scan_runs import (  # noqa: E402
    parse_web_scan_check,
    run_web_scan_check,
    run_web_scan_check_from_form,
)


ROOT = Path(__file__).resolve().parents[1]


class WebScanRunTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base_dir = ROOT / ".tmp-tests" / self.id().rsplit(".", 1)[-1]
        if self.base_dir.exists():
            shutil.rmtree(self.base_dir)
        self.data_dir = self.base_dir / "data"
        self.runs_dir = self.base_dir / "runs"

    def tearDown(self) -> None:
        if self.base_dir.exists():
            shutil.rmtree(self.base_dir)

    def test_runs_ready_selected_check_after_explicit_confirmation(self) -> None:
        store = JsonStore(self.data_dir)
        mission = self._create_ready_mission(
            store,
            selected_checks=[AuditCheck.HTTP_HEADERS],
            scope=[
                ScopeItem(
                    type=ScopeType.URL,
                    value="https://client.example",
                    environment=ScopeEnvironment.EXTERNAL,
                    approved=True,
                )
            ],
        )
        evidence_dirs: list[Path] = []

        def fake_runner(mission_id: str, data_dir: Path, evidence_dir: Path) -> None:
            evidence_dirs.append(evidence_dir)
            runner_store = JsonStore(data_dir)
            runner_store.add_finding(
                mission_id,
                Finding(
                    title="Missing HTTP security header",
                    severity=Severity.MEDIUM,
                    affected_asset="https://client.example",
                    category="http_headers",
                    source_module="http_headers",
                    proof="The pilot response did not include a test header.",
                    risk="Browser-side protection may be weaker than expected.",
                    remediation="Enable the missing response header on the web server.",
                    counter_test="Repeat the HTTP header audit on the approved URL.",
                    confidence=0.8,
                ),
            )
            runner_store.add_scan_run(
                ScanRun(
                    mission_id=mission_id,
                    check=AuditCheck.HTTP_HEADERS,
                    status=ScanRunStatus.COMPLETED,
                    command_count=1,
                    finding_count=1,
                )
            )

        result = run_web_scan_check_from_form(
            mission_id=mission.id,
            data_dir=self.data_dir,
            runs_dir=self.runs_dir,
            form={"check": "http_headers", "execute_confirm": "on"},
            runners={AuditCheck.HTTP_HEADERS: fake_runner},
        )

        self.assertEqual(result.check, AuditCheck.HTTP_HEADERS)
        self.assertEqual(result.label, "HTTP Headers")
        self.assertEqual(result.run_status, "completed")
        self.assertEqual(result.command_count, 1)
        self.assertEqual(result.finding_count, 1)
        self.assertEqual(evidence_dirs, [self.runs_dir / mission.id / "evidence"])
        self.assertEqual(len(JsonStore(self.data_dir).list_scan_runs(mission.id)), 1)

    def test_blocks_missing_execution_confirmation(self) -> None:
        store = JsonStore(self.data_dir)
        mission = self._create_ready_mission(
            store,
            selected_checks=[AuditCheck.HTTP_HEADERS],
            scope=[
                ScopeItem(type=ScopeType.URL, value="https://client.example", approved=True)
            ],
        )

        with self.assertRaisesRegex(ValueError, "explicit scan execution confirmation"):
            run_web_scan_check_from_form(
                mission_id=mission.id,
                data_dir=self.data_dir,
                runs_dir=self.runs_dir,
                form={"check": "http_headers"},
                runners={},
            )

    def test_blocks_unselected_check(self) -> None:
        store = JsonStore(self.data_dir)
        mission = self._create_ready_mission(
            store,
            selected_checks=[AuditCheck.HTTP_HEADERS],
            scope=[
                ScopeItem(type=ScopeType.URL, value="https://client.example", approved=True),
                ScopeItem(type=ScopeType.DOMAIN, value="client.example", approved=True),
            ],
        )

        with self.assertRaisesRegex(ValueError, "dns_mail is not selected"):
            run_web_scan_check(
                mission_id=mission.id,
                data_dir=self.data_dir,
                runs_dir=self.runs_dir,
                check=AuditCheck.DNS_MAIL,
                confirmed=True,
                runners={},
            )

    def test_blocks_selected_check_when_plan_is_not_ready(self) -> None:
        store = JsonStore(self.data_dir)
        mission = self._create_ready_mission(
            store,
            selected_checks=[AuditCheck.SMB],
            scope=[
                ScopeItem(
                    type=ScopeType.URL,
                    value="https://client.example",
                    environment=ScopeEnvironment.EXTERNAL,
                    approved=True,
                )
            ],
        )

        with self.assertRaisesRegex(ValueError, "SMB is not ready"):
            run_web_scan_check(
                mission_id=mission.id,
                data_dir=self.data_dir,
                runs_dir=self.runs_dir,
                check=AuditCheck.SMB,
                confirmed=True,
                runners={},
            )

    def test_rejects_unknown_check_value(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported audit check"):
            parse_web_scan_check("unknown")

    def _create_ready_mission(
        self,
        store: JsonStore,
        selected_checks: list[AuditCheck],
        scope: list[ScopeItem],
    ) -> Mission:
        client = store.create_client(Client(name="Client Pilot"))
        return store.create_mission(
            Mission(
                client_id=client.id,
                name="Audit Pilot",
                authorization_reference="AUTH-001",
                selected_checks=selected_checks,
                scope=scope,
            )
        )


if __name__ == "__main__":
    unittest.main()
