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
from media_security_audit.web_ui import (  # noqa: E402
    build_client_view,
    build_dashboard_view,
    build_mission_view,
)


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
        self.assertEqual(view.clients[0].preparation_priority, "warning")
        self.assertEqual(view.clients[0].next_action, "Review 1 new finding(s).")
        self.assertEqual(view.clients[0].next_action_mission_id, mission.id)
        self.assertEqual(view.clients[0].next_action_mission_name, "External Audit")
        self.assertEqual(view.clients[0].blocked_preparation_count, 0)
        self.assertEqual(view.clients[0].warning_preparation_count, 1)
        self.assertEqual(view.clients[0].ready_preparation_count, 0)
        self.assertEqual(view.missions[0].client_name, "Client X")
        self.assertEqual(view.missions[0].approved_scope_count, 1)
        self.assertEqual(view.missions[0].audit_template_title, "")
        self.assertEqual(view.missions[0].preparation_status, "warning")
        self.assertEqual(view.missions[0].preparation_next_action, "Review 1 new finding(s).")
        self.assertEqual(view.blocked_preparation_count, 0)
        self.assertEqual(view.warning_preparation_count, 1)
        self.assertEqual(view.ready_preparation_count, 0)
        self.assertEqual(view.preparation_items[0].client_name, "Client X")
        self.assertEqual(view.preparation_items[0].status, "warning")
        self.assertEqual(
            view.preparation_items[0].next_action,
            "Review 1 new finding(s).",
        )

    def test_dashboard_view_builds_workspace_preparation_summary(self) -> None:
        store = JsonStore(clean_data_dir("web-ui-dashboard-preparation"))
        client_a = store.create_client(Client(name="Client A"))
        client_b = store.create_client(Client(name="Client B"))
        client_c = store.create_client(Client(name="Client C"))
        ready_mission = store.create_mission(
            Mission(
                client_id=client_a.id,
                name="Ready Audit",
                authorization_reference="AUTH-READY",
            )
        )
        store.add_scope_item(
            ready_mission.id,
            ScopeItem(type=ScopeType.IP, value="192.0.2.10", approved=True),
        )
        blocked_mission = store.create_mission(
            Mission(client_id=client_b.id, name="Blocked Audit", selected_checks=[])
        )
        warning_mission = store.create_mission(
            Mission(
                client_id=client_b.id,
                name="Warning Audit",
                authorization_reference="AUTH-WARN",
            )
        )
        store.add_scope_item(
            warning_mission.id,
            ScopeItem(type=ScopeType.DOMAIN, value="client-b.example", approved=True),
        )
        store.add_finding(
            warning_mission.id,
            Finding(
                title="Finding awaiting review",
                severity=Severity.LOW,
                affected_asset="client-b.example",
                category="manual",
                source_module="manual",
                proof="Observed manually.",
                risk="Risk needs review.",
                remediation="Apply correction.",
                counter_test="Repeat the check.",
                confidence=0.8,
            ),
        )

        view = build_dashboard_view(store)

        self.assertEqual(view.blocked_preparation_count, 1)
        self.assertEqual(view.warning_preparation_count, 1)
        self.assertEqual(view.ready_preparation_count, 1)
        self.assertEqual(
            [item.status for item in view.preparation_items],
            ["blocked", "warning", "ready"],
        )
        self.assertEqual(view.preparation_items[0].mission_id, blocked_mission.id)
        self.assertEqual(view.preparation_items[0].client_name, "Client B")
        self.assertEqual(
            view.preparation_items[0].next_action,
            "Add written authorization reference.",
        )
        self.assertEqual(view.preparation_items[1].mission_id, warning_mission.id)
        self.assertEqual(view.preparation_items[2].mission_id, ready_mission.id)
        self.assertEqual(
            [client.name for client in view.clients],
            ["Client B", "Client A", "Client C"],
        )
        client_rows = {client.name: client for client in view.clients}
        self.assertEqual(client_rows["Client A"].preparation_priority, "ready")
        self.assertEqual(client_rows["Client A"].next_action_mission_id, ready_mission.id)
        self.assertEqual(client_rows["Client A"].blocked_preparation_count, 0)
        self.assertEqual(client_rows["Client A"].warning_preparation_count, 0)
        self.assertEqual(client_rows["Client A"].ready_preparation_count, 1)
        self.assertEqual(client_rows["Client B"].preparation_priority, "blocked")
        self.assertEqual(client_rows["Client B"].next_action_mission_id, blocked_mission.id)
        self.assertEqual(client_rows["Client B"].blocked_preparation_count, 1)
        self.assertEqual(client_rows["Client B"].warning_preparation_count, 1)
        self.assertEqual(client_rows["Client B"].ready_preparation_count, 0)
        self.assertEqual(client_rows["Client C"].preparation_priority, "none")
        self.assertEqual(client_rows["Client C"].next_action, "Create first mission for this client.")
        self.assertEqual(client_rows["Client C"].next_action_mission_id, "")

    def test_client_view_summarizes_only_client_missions(self) -> None:
        store = JsonStore(clean_data_dir("web-ui-client"))
        client_a = store.create_client(
            Client(name="Client A", internal_reference="CA", notes="Priority client")
        )
        client_b = store.create_client(Client(name="Client B"))
        mission_a = store.create_mission(
            Mission(
                client_id=client_a.id,
                name="Client A Audit",
                audit_type=AuditType.EXTERNAL,
                authorization_reference="AUTH-A",
            )
        )
        store.add_scope_item(
            mission_a.id,
            ScopeItem(
                type=ScopeType.DOMAIN,
                value="client-a.example",
                environment=ScopeEnvironment.EXTERNAL,
                approved=True,
            ),
        )
        store.add_finding(
            mission_a.id,
            Finding(
                title="High finding",
                severity=Severity.HIGH,
                affected_asset="client-a.example",
                category="manual",
                source_module="manual",
                proof="Observed manually.",
                risk="Risk needs correction.",
                remediation="Apply correction.",
                counter_test="Repeat the check.",
                confidence=0.8,
            ),
        )
        mission_b = store.create_mission(Mission(client_id=client_b.id, name="Client B Audit"))
        store.add_activity_event(
            ActivityEvent(
                mission_id=mission_a.id,
                action="scope.approved",
                summary="Scope approved for Client A Audit",
            )
        )
        store.add_activity_event(
            ActivityEvent(
                mission_id=mission_b.id,
                action="mission.created",
                summary="Client B mission created",
            )
        )

        view = build_client_view(store, client_a.id)

        self.assertEqual(view.client.name, "Client A")
        self.assertEqual(view.client.reference, "CA")
        self.assertEqual(view.client.notes, "Priority client")
        self.assertEqual(view.total_missions, 1)
        self.assertEqual(view.total_findings, 1)
        self.assertEqual(view.high_or_critical_findings, 1)
        self.assertEqual(view.approved_scope_count, 1)
        self.assertEqual(view.scope_count, 1)
        self.assertEqual([mission.name for mission in view.missions], ["Client A Audit"])
        self.assertEqual(view.missions[0].client_name, "Client A")
        self.assertEqual(view.missions[0].preparation_status, "warning")
        self.assertEqual(view.missions[0].preparation_next_action, "Review 1 new finding(s).")
        self.assertEqual(view.activity_log_url, f"/activity?client_id={client_a.id}")
        self.assertEqual(len(view.recent_activity_events), 1)
        self.assertEqual(view.recent_activity_events[0].mission_name, "Client A Audit")
        self.assertEqual(view.recent_activity_events[0].action, "scope.approved")

    def test_client_view_builds_preparation_summary_by_client(self) -> None:
        store = JsonStore(clean_data_dir("web-ui-client-preparation"))
        client_a = store.create_client(Client(name="Client A"))
        client_b = store.create_client(Client(name="Client B"))
        ready_mission = store.create_mission(
            Mission(
                client_id=client_a.id,
                name="Ready Audit",
                authorization_reference="AUTH-READY",
            )
        )
        store.add_scope_item(
            ready_mission.id,
            ScopeItem(type=ScopeType.IP, value="192.0.2.10", approved=True),
        )
        store.create_mission(
            Mission(client_id=client_a.id, name="Blocked Audit", selected_checks=[])
        )
        warning_mission = store.create_mission(
            Mission(
                client_id=client_a.id,
                name="Warning Audit",
                authorization_reference="AUTH-WARN",
            )
        )
        store.add_scope_item(
            warning_mission.id,
            ScopeItem(type=ScopeType.DOMAIN, value="client-a.example", approved=True),
        )
        store.add_finding(
            warning_mission.id,
            Finding(
                title="Finding awaiting review",
                severity=Severity.MEDIUM,
                affected_asset="client-a.example",
                category="manual",
                source_module="manual",
                proof="Observed manually.",
                risk="Risk needs review.",
                remediation="Apply correction.",
                counter_test="Repeat the check.",
                confidence=0.8,
            ),
        )
        store.create_mission(Mission(client_id=client_b.id, name="Other Blocked Audit"))

        view = build_client_view(store, client_a.id)

        self.assertEqual(view.blocked_preparation_count, 1)
        self.assertEqual(view.warning_preparation_count, 1)
        self.assertEqual(view.ready_preparation_count, 1)
        self.assertEqual(
            [item.status for item in view.preparation_items],
            ["blocked", "warning", "ready"],
        )
        self.assertEqual(
            [item.mission_name for item in view.preparation_items],
            ["Blocked Audit", "Warning Audit", "Ready Audit"],
        )
        blocked = view.preparation_items[0]
        self.assertEqual(blocked.authorization_status, "missing")
        self.assertEqual(blocked.scope_status, "missing")
        self.assertEqual(blocked.check_status, "missing")
        self.assertEqual(blocked.blocked_count, 3)
        self.assertEqual(blocked.next_action, "Add written authorization reference.")
        warning = view.preparation_items[1]
        self.assertEqual(warning.warning_count, 1)
        self.assertEqual(warning.next_action, "Review 1 new finding(s).")

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
        self.assertIsNotNone(view.template_guidance)
        self.assertEqual(view.template_guidance.title, "Internal Network Hygiene")
        self.assertEqual(view.template_guidance.recommended_checks, ["Nmap services"])
        self.assertIn("Approved internal CIDR ranges", view.template_guidance.scope_guidance)
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
        self.assertIsNone(view.template_guidance)

    def test_mission_view_readiness_items_include_action_targets(self) -> None:
        store = JsonStore(clean_data_dir("web-ui-readiness-actions"))
        client = store.create_client(Client(name="Client Readiness"))
        mission = store.create_mission(
            Mission(
                client_id=client.id,
                name="Blocked Readiness Audit",
                selected_checks=[],
            )
        )
        store.add_finding(
            mission.id,
            Finding(
                title="Finding awaiting review",
                severity=Severity.LOW,
                affected_asset="client.example",
                category="manual",
                source_module="manual",
                proof="Observed manually.",
                risk="Risk needs review.",
                remediation="Apply correction.",
                counter_test="Repeat the check.",
                confidence=0.8,
            ),
        )

        view = build_mission_view(store, mission.id)
        readiness = {item.label: item for item in view.readiness_items}

        self.assertEqual(readiness["Authorization"].action_label, "Update Setup")
        self.assertEqual(readiness["Authorization"].action_href, "#mission-setup")
        self.assertEqual(readiness["Approved Scope"].action_label, "Review Scope")
        self.assertEqual(readiness["Approved Scope"].action_href, "#scope")
        self.assertEqual(readiness["Check Selection"].action_label, "Select Checks")
        self.assertEqual(readiness["Check Selection"].action_href, "#check-selection")
        self.assertEqual(readiness["Finding Review"].action_label, "Review Findings")
        self.assertEqual(readiness["Finding Review"].action_href, "#findings")
        self.assertEqual(readiness["Reports"].action_label, "Open Reports")
        self.assertEqual(readiness["Reports"].action_href, "#reports")

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
        self.assertEqual(view.mission_export.integrity_status, "ready")
        self.assertIn("packaged file(s) verified", view.mission_export.integrity_detail)

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
