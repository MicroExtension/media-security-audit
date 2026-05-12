from pathlib import Path
import json
import shutil
import sys
import unittest
from zipfile import ZipFile

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
from media_security_audit.web_exports import (  # noqa: E402
    generate_mission_export,
    list_mission_export,
    mission_export_file,
)
from media_security_audit.web_reports import generate_web_reports  # noqa: E402


def clean_dir(name: str) -> Path:
    path = Path(__file__).resolve().parents[1] / ".tmp-tests" / name
    if path.exists():
        shutil.rmtree(path)
    return path


class WebExportTests(unittest.TestCase):
    def test_generates_mission_export_package(self) -> None:
        data_dir = clean_dir("web-export-data")
        reports_dir = clean_dir("web-export-reports")
        store = JsonStore(data_dir)
        client = store.create_client(Client(name="Client Export"))
        mission = store.create_mission(
            Mission(
                client_id=client.id,
                name="Export Audit",
                audit_template_id="tpl_web_mail_hygiene",
                authorization_reference="AUTH-EXPORT",
                selected_checks=[AuditCheck.HTTP_HEADERS, AuditCheck.DNS_MAIL],
                scope=[
                    ScopeItem(
                        type=ScopeType.URL,
                        value="https://client.example",
                        approved=True,
                    )
                ],
            )
        )
        finding = store.add_finding(
            mission.id,
            Finding(
                title="Exported finding",
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
        event = store.add_activity_event(
            ActivityEvent(
                mission_id=mission.id,
                action="mission.created",
                summary="Mission created",
            )
        )
        run = store.add_scan_run(
            ScanRun(
                mission_id=mission.id,
                check=AuditCheck.HTTP_HEADERS,
                status=ScanRunStatus.COMPLETED,
                command_count=1,
                finding_count=1,
                evidence_paths=["runs/evidence/http-headers.json"],
            )
        )
        generate_web_reports(store, mission.id, reports_dir)
        generate_authorization_brief(store, mission.id, reports_dir)

        export_path = generate_mission_export(store, mission.id, reports_dir)

        self.assertEqual(export_path, mission_export_file(reports_dir, mission.id))
        self.assertEqual(list_mission_export(mission.id, reports_dir).filename, export_path.name)
        with ZipFile(export_path) as archive:
            names = set(archive.namelist())
            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))

        self.assertEqual(manifest["mission_id"], mission.id)
        self.assertEqual(manifest["mission_name"], "Export Audit")
        self.assertEqual(manifest["client_name"], "Client Export")
        self.assertEqual(manifest["audit_template_id"], "tpl_web_mail_hygiene")
        self.assertEqual(manifest["audit_template_title"], "Web And Mail Hygiene")
        self.assertEqual(manifest["authorization_decision"], "ready_for_guarded_cli_execution")
        self.assertEqual(manifest["selected_checks"], ["http_headers", "dns_mail"])
        self.assertEqual(manifest["scope"]["approved_count"], 1)
        self.assertEqual(manifest["finding_count"], 1)
        self.assertEqual(manifest["report_count"], 3)
        self.assertEqual(manifest["authorization_brief_count"], 2)
        self.assertEqual(manifest["evidence_path_count"], 1)
        self.assertEqual(
            manifest["authorization_briefs"],
            [
                f"authorization/{mission.id}-authorization-brief.md",
                f"authorization/{mission.id}-authorization-brief.html",
            ],
        )
        self.assertIn("data/client.json", names)
        self.assertIn("data/mission.json", names)
        self.assertIn(f"data/findings/{finding.id}.json", names)
        self.assertIn(f"data/activity/{event.id}.json", names)
        self.assertIn(f"data/runs/{run.id}.json", names)
        self.assertIn(f"authorization/{mission.id}-authorization-brief.md", names)
        self.assertIn(f"reports/{mission.id}.json", names)
        self.assertIn(f"reports/{mission.id}.html", names)

    def test_missing_mission_export_has_named_error(self) -> None:
        reports_dir = clean_dir("web-export-missing")

        with self.assertRaises(FileNotFoundError) as error:
            mission_export_file(reports_dir, "mission_missing")

        self.assertIn("mission export package not found", str(error.exception))


if __name__ == "__main__":
    unittest.main()
