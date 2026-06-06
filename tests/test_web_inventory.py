from __future__ import annotations

from pathlib import Path
import shutil
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.models import (  # noqa: E402
    ActivityEvent,
    AuditCheck,
    Client,
    Finding,
    Mission,
    ScanRun,
    ScanRunStatus,
    ScopeItem,
    ScopeType,
    Severity,
)
from media_security_audit.storage import JsonStore  # noqa: E402
from media_security_audit.web_authorization import generate_authorization_brief  # noqa: E402
from media_security_audit.web_exports import generate_mission_export  # noqa: E402
from media_security_audit.web_inventory import build_workspace_inventory  # noqa: E402
from media_security_audit.web_reports import generate_web_reports  # noqa: E402


def clean_dir(name: str) -> Path:
    path = Path(__file__).resolve().parents[1] / ".tmp-tests" / name
    if path.exists():
        shutil.rmtree(path)
    return path


class WebInventoryTests(unittest.TestCase):
    def test_builds_workspace_inventory_counts(self) -> None:
        data_dir = clean_dir("web-inventory-data")
        reports_dir = clean_dir("web-inventory-reports")
        store = JsonStore(data_dir)
        client = store.create_client(Client(name="Client Inventory"))
        mission = store.create_mission(
            Mission(
                client_id=client.id,
                name="Inventory Audit",
                authorization_reference="AUTH-INV",
                scope=[ScopeItem(type=ScopeType.DOMAIN, value="client.example", approved=True)],
            )
        )
        store.add_finding(
            mission.id,
            Finding(
                title="Inventory finding",
                severity=Severity.LOW,
                affected_asset="client.example",
                category="manual",
                source_module="manual",
                proof="Observed manually.",
                risk="Risk pending review.",
                remediation="Apply remediation.",
                counter_test="Repeat the check.",
                confidence=0.8,
            ),
        )
        store.add_activity_event(
            ActivityEvent(
                mission_id=mission.id,
                action="mission.created",
                summary="Mission created",
            )
        )
        store.add_scan_run(
            ScanRun(
                mission_id=mission.id,
                check=AuditCheck.NMAP,
                status=ScanRunStatus.COMPLETED,
                command_count=1,
                finding_count=1,
            )
        )
        generate_web_reports(store, mission.id, reports_dir)
        generate_authorization_brief(store, mission.id, reports_dir)
        generate_mission_export(store, mission.id, reports_dir)

        inventory = build_workspace_inventory(store, reports_dir)
        metrics = {metric.label: metric.value for metric in inventory.metrics}

        self.assertEqual(inventory.status, "ready")
        self.assertEqual(metrics["Clients"], 1)
        self.assertEqual(metrics["Missions"], 1)
        self.assertEqual(metrics["Ready missions"], 1)
        self.assertEqual(metrics["Findings"], 1)
        self.assertEqual(metrics["Activity events"], 1)
        self.assertEqual(metrics["Scan runs"], 1)
        self.assertEqual(metrics["Generated reports"], 4)
        self.assertEqual(metrics["Authorization briefs"], 2)
        self.assertEqual(metrics["Mission exports"], 1)
        self.assertEqual(inventory.issues[0].status, "ready")

    def test_reports_missing_clients_and_orphan_directories(self) -> None:
        data_dir = clean_dir("web-inventory-issues-data")
        reports_dir = clean_dir("web-inventory-issues-reports")
        store = JsonStore(data_dir)
        store.ensure()
        missing_client_mission = Mission(client_id="client_missing", name="Missing Client Audit")
        (store.missions_dir / f"{missing_client_mission.id}.json").write_text(
            missing_client_mission.model_dump_json(),
            encoding="utf-8",
        )
        (store.findings_dir / "mission_orphan_findings").mkdir(parents=True)
        (store.events_dir / "mission_orphan_events").mkdir(parents=True)
        (store.runs_dir / "mission_orphan_runs").mkdir(parents=True)
        (reports_dir / "mission_orphan_reports").mkdir(parents=True)

        inventory = build_workspace_inventory(store, reports_dir)
        issues = {issue.label: issue for issue in inventory.issues}

        self.assertEqual(inventory.status, "blocked")
        self.assertEqual(issues["Missing client references"].status, "blocked")
        self.assertIn(missing_client_mission.id, issues["Missing client references"].detail)
        self.assertIn("mission_orphan_findings", issues["Orphan finding folders"].detail)
        self.assertIn("mission_orphan_events", issues["Orphan activity folders"].detail)
        self.assertIn("mission_orphan_runs", issues["Orphan scan run folders"].detail)
        self.assertIn("mission_orphan_reports", issues["Orphan report folders"].detail)


if __name__ == "__main__":
    unittest.main()
