from datetime import date
from pathlib import Path
import shutil
import unittest

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.models import (  # noqa: E402
    ActivityEvent,
    AuditCheck,
    AuditType,
    Client,
    Finding,
    FindingStatus,
    Mission,
    ScanRun,
    ScanRunStatus,
    ScopeEnvironment,
    ScopeItem,
    ScopeType,
    Severity,
)
from media_security_audit.storage import JsonStore  # noqa: E402
from media_security_audit.web_authorization import generate_authorization_brief  # noqa: E402
from media_security_audit.web_exports import generate_mission_export  # noqa: E402
from media_security_audit.web_ui import build_dashboard_view, build_mission_view  # noqa: E402


def clean_data_dir(name: str) -> Path:
    data_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / name
    if data_dir.exists():
        shutil.rmtree(data_dir)
    return data_dir


class WebUiTests(unittest.TestCase):
    def test_dashboard_view_summarizes_clients_missions_and_findings(self) -> None:
        store = JsonStore(clean_data_dir("web-ui-dashboard"))
        client = store.create_client(Client(name="Client X", internal_reference="CX"))
        mission = store.create_mission(
            Mission(
                client_id=client.id,
                name="External Audit",
                audit_type=AuditType.EXTERNAL,
                authorization_reference="AUTH-001",
            )
        )
        store.add_scope_item(
            mission.id,
            ScopeItem(
                type=ScopeType.DOMAIN,
                value="client.example",
                environment=ScopeEnvironment.EXTERNAL,
                approved=True,
            ),
        )
        store.add_finding(
            mission.id,
            Finding(
                title="Missing DMARC policy",
                severity=Severity.MEDIUM,
                affected_asset="client.example",
                category="mail",
                source_module="dns_mail",
                proof="No DMARC TXT record found.",
                risk="Spoofing risk.",
                remediation="Publish a DMARC policy.",
                counter_test="Resolve TXT _dmarc.client.example.",
                confidence=0.9,
            ),
        )

        view = build_dashboard_view(store)

        self.assertEqual(view.total_clients, 1)
        self.assertEqual(view.total_missions, 1)
        self.assertEqual(view.total_findings, 1)
        self.assertEqual(view.high_or_critical_findings, 0)
        self.assertEqual(view.clients[0].mission_count, 1)
        self.assertEqual(view.missions[0].client_name, "Client X")
        self.assertEqual(view.missions[0].approved_scope_count, 1)
        self.assertEqual(view.missions[0].audit_template_title, "")

    def test_mission_view_orders_scope_findings_and_remediation(self) -> None:
        store = JsonStore(clean_data_dir("web-ui-mission"))
        client = store.create_client(Client(name="Client Y"))
        mission = store.create_mission(
            Mission(
                client_id=client.id,
                name="Internal Audit",
                audit_template_id="tpl_internal_hygiene",
                authorization_reference="AUTH-002",
                authorization_contact="RSSI Client",
                authorization_date=date(2026, 5, 10),
                authorization_expires_at=date(2026, 6, 10),
                emergency_contact="astreinte@example.invalid",
                report_recipients="direction@example.invalid",
                evidence_retention_days=60,
            )
        )
        store.add_scope_item(
            mission.id,
            ScopeItem(type=ScopeType.IP, value="192.0.2.10", approved=True),
        )
        store.add_finding(
            mission.id,
            Finding(
                title="Open administrative service",
                severity=Severity.HIGH,
                affected_asset="192.0.2.10",
                category="network",
                source_module="nmap",
                proof="tcp/3389 open",
                risk="Remote administration is exposed.",
                remediation="Restrict access to trusted sources.",
                counter_test="Run the approved Nmap plan again.",
                confidence=0.8,
            ),
        )

        view = build_mission_view(store, mission.id)

        self.assertEqual(view.mission.client_name, "Client Y")
        self.assertEqual(view.mission.audit_template_id, "tpl_internal_hygiene")
        self.assertEqual(view.mission.audit_template_title, "Internal Network Hygiene")
        self.assertEqual(view.mission.authorization_reference, "AUTH-002")
        self.assertEqual(view.mission.authorization_contact, "RSSI Client")
        self.assertEqual(view.mission.authorization_date, "2026-05-10")
        self.assertEqual(view.mission.authorization_expires_at, "2026-06-10")
        self.assertEqual(view.mission.emergency_contact, "astreinte@example.invalid")
        self.assertEqual(view.mission.report_recipients, "direction@example.invalid")
        self.assertEqual(view.mission.evidence_retention_days, "60")
        self.assertEqual(view.mission.notes, "")
        self.assertEqual(view.scope[0].status, "approved")
        self.assertEqual(view.findings[0].severity, "high")
        self.assertEqual(view.findings[0].review_note, "")
        self.assertEqual(view.findings[0].related_remediations[0].id, "rem_rdp_restrict_exposure")
        self.assertEqual(view.reports, [])
        self.assertIsNone(view.mission_export)
        self.assertEqual(len(view.readiness_items), 5)
        self.assertEqual(view.check_selection[0].value, "nmap")
        self.assertTrue(view.check_selection[0].selected)
        self.assertEqual(view.scan_plans[0].label, "Nmap")
        self.assertEqual(view.scan_plans[0].status, "ready")
        self.assertEqual(view.counter_test_items, [])
        self.assertEqual(view.activity_events, [])
        self.assertEqual(len(view.remediation_items), 1)
        self.assertIn("High-priority", view.executive_summary)

    def test_mission_view_builds_counter_test_plan_for_actionable_statuses(self) -> None:
        store = JsonStore(clean_data_dir("web-ui-counter-test"))
        client = store.create_client(Client(name="Client Z"))
        mission = store.create_mission(
            Mission(
                client_id=client.id,
                name="Counter-test Audit",
                authorization_reference="AUTH-003",
            )
        )
        store.add_finding(
            mission.id,
            Finding(
                title="Confirmed finding",
                severity=Severity.MEDIUM,
                affected_asset="client.example",
                category="manual",
                source_module="manual",
                proof="Observed manually.",
                risk="Risk pending correction.",
                remediation="Apply the corrective action.",
                counter_test="Repeat the manual check.",
                confidence=0.8,
                status=FindingStatus.CONFIRMED,
            ),
        )
        store.add_finding(
            mission.id,
            Finding(
                title="Passed finding",
                severity=Severity.HIGH,
                affected_asset="admin.client.example",
                category="manual",
                source_module="manual",
                proof="Observed manually.",
                risk="Risk was corrected.",
                remediation="No further action.",
                counter_test="Already passed.",
                confidence=0.8,
                status=FindingStatus.COUNTER_TEST_PASSED,
            ),
        )

        view = build_mission_view(store, mission.id)

        self.assertEqual(len(view.counter_test_items), 1)
        self.assertEqual(view.counter_test_items[0].title, "Confirmed finding")
        self.assertEqual(view.counter_test_items[0].status, "confirmed")
        self.assertEqual(view.findings[0].related_remediations, [])

    def test_mission_view_includes_activity_events(self) -> None:
        store = JsonStore(clean_data_dir("web-ui-activity"))
        client = store.create_client(Client(name="Client Activity"))
        mission = store.create_mission(Mission(client_id=client.id, name="Activity Audit"))
        store.add_activity_event(
            ActivityEvent(
                mission_id=mission.id,
                action="mission.created",
                summary="Mission created",
            )
        )

        view = build_mission_view(store, mission.id)

        self.assertEqual(len(view.activity_events), 1)
        self.assertEqual(view.activity_events[0].action, "mission.created")
        self.assertEqual(view.activity_events[0].summary, "Mission created")

    def test_mission_view_marks_unselected_checks(self) -> None:
        store = JsonStore(clean_data_dir("web-ui-check-selection"))
        client = store.create_client(Client(name="Client Checks"))
        mission = store.create_mission(
            Mission(
                client_id=client.id,
                name="Check Audit",
                selected_checks=[AuditCheck.DNS_MAIL],
            )
        )

        view = build_mission_view(store, mission.id)
        selected = {item.value: item.selected for item in view.check_selection}

        self.assertFalse(selected["nmap"])
        self.assertFalse(selected["http_headers"])
        self.assertTrue(selected["dns_mail"])
        self.assertEqual([plan.label for plan in view.scan_plans], ["DNS/Mail"])

    def test_mission_view_includes_scan_runs(self) -> None:
        store = JsonStore(clean_data_dir("web-ui-runs"))
        client = store.create_client(Client(name="Client Runs"))
        mission = store.create_mission(Mission(client_id=client.id, name="Run Audit"))
        store.add_scan_run(
            ScanRun(
                mission_id=mission.id,
                check=AuditCheck.HTTP_HEADERS,
                status=ScanRunStatus.COMPLETED,
                command_count=1,
                finding_count=2,
                evidence_paths=["evidence/http.json"],
            )
        )

        view = build_mission_view(store, mission.id)

        self.assertEqual(len(view.scan_runs), 1)
        self.assertEqual(view.scan_runs[0].check, "http_headers")
        self.assertEqual(view.scan_runs[0].status, "completed")
        self.assertEqual(view.scan_runs[0].finding_count, 2)
        self.assertEqual(view.scan_runs[0].evidence_count, 1)

    def test_mission_view_includes_export_link(self) -> None:
        store = JsonStore(clean_data_dir("web-ui-export-data"))
        reports_dir = clean_data_dir("web-ui-export-reports")
        client = store.create_client(Client(name="Client Export"))
        mission = store.create_mission(Mission(client_id=client.id, name="Export Audit"))
        generate_mission_export(store, mission.id, reports_dir)

        view = build_mission_view(store, mission.id, reports_dir=reports_dir)

        self.assertIsNotNone(view.mission_export)
        self.assertEqual(view.mission_export.filename, f"{mission.id}-package.zip")

    def test_mission_view_includes_authorization_brief_links(self) -> None:
        store = JsonStore(clean_data_dir("web-ui-authorization-data"))
        reports_dir = clean_data_dir("web-ui-authorization-reports")
        client = store.create_client(Client(name="Client Authorization"))
        mission = store.create_mission(
            Mission(
                client_id=client.id,
                name="Authorization Audit",
                authorization_reference="AUTH-004",
            )
        )
        generate_authorization_brief(store, mission.id, reports_dir)

        view = build_mission_view(store, mission.id, reports_dir=reports_dir)

        self.assertEqual([brief.format for brief in view.authorization_briefs], ["markdown", "html"])
        self.assertEqual(
            view.authorization_briefs[0].filename,
            f"{mission.id}-authorization-brief.md",
        )


if __name__ == "__main__":
    unittest.main()
