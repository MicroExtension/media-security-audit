from __future__ import annotations

import json
import shutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.mission_readiness import (  # noqa: E402
    build_mission_readiness_payload,
    format_mission_readiness_json,
    format_mission_readiness_text,
    mission_readiness_exit_code,
)
from media_security_audit.models import (  # noqa: E402
    Client,
    Finding,
    FindingStatus,
    Mission,
    ScopeItem,
    ScopeType,
    Severity,
)
from media_security_audit.storage import JsonStore  # noqa: E402
from media_security_audit.web_reports import generate_web_reports  # noqa: E402


def clean_dir(name: str) -> Path:
    path = Path(__file__).resolve().parents[1] / ".tmp-tests" / name
    if path.exists():
        shutil.rmtree(path)
    return path


class MissionReadinessTests(unittest.TestCase):
    def test_reports_blocked_mission_without_running_scans(self) -> None:
        data_dir = clean_dir("mission-readiness-blocked")
        reports_dir = clean_dir("mission-readiness-blocked-reports")
        store = JsonStore(data_dir)
        client = store.create_client(Client(name="Client Blocked"))
        mission = store.create_mission(Mission(client_id=client.id, name="Blocked Audit"))

        payload = build_mission_readiness_payload(store, mission.id, reports_dir)
        text = format_mission_readiness_text(store, mission.id, reports_dir)

        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["summary"]["blocked"], 2)
        self.assertEqual(payload["summary"]["execution"], "not_executed")
        self.assertEqual(payload["scan_plan"]["execution"], "not_executed")
        self.assertEqual(payload["scan_plan"]["blocked"], 3)
        self.assertEqual(mission_readiness_exit_code(payload), 1)
        self.assertIn("Mission readiness: blocked", text)
        self.assertIn("[blocked] Authorization", text)
        self.assertEqual(store.list_scan_runs(mission.id), [])

    def test_reports_ready_mission_with_reviewed_findings_and_reports(self) -> None:
        data_dir = clean_dir("mission-readiness-ready")
        reports_dir = clean_dir("mission-readiness-ready-reports")
        store = JsonStore(data_dir)
        client = store.create_client(Client(name="Client Ready"))
        mission = store.create_mission(
            Mission(
                client_id=client.id,
                name="Ready Audit",
                authorization_reference="AUTH-READY",
                scope=[
                    ScopeItem(type=ScopeType.DOMAIN, value="client.example", approved=True),
                    ScopeItem(type=ScopeType.URL, value="https://client.example", approved=True),
                ],
            )
        )
        store.add_finding(
            mission.id,
            Finding(
                title="Reviewed finding",
                severity=Severity.LOW,
                affected_asset="client.example",
                category="manual",
                source_module="manual",
                proof="Reviewed evidence.",
                risk="Known low risk.",
                remediation="Apply remediation.",
                counter_test="Repeat approved checks.",
                confidence=0.8,
                status=FindingStatus.CONFIRMED,
            ),
        )
        generate_web_reports(store, mission.id, reports_dir)

        payload = json.loads(format_mission_readiness_json(store, mission.id, reports_dir))

        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["summary"]["ready"], 5)
        self.assertEqual(payload["summary"]["generated_reports"], 3)
        self.assertEqual(payload["scan_plan"]["ready"], 3)
        self.assertEqual(payload["scan_plan"]["planned_commands"], 4)
        self.assertEqual(mission_readiness_exit_code(payload, strict=True), 0)
        self.assertEqual(store.list_scan_runs(mission.id), [])


if __name__ == "__main__":
    unittest.main()
