from pathlib import Path
import shutil
import unittest

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.models import (  # noqa: E402
    AuditType,
    Client,
    Finding,
    Mission,
    ScopeEnvironment,
    ScopeItem,
    ScopeType,
    Severity,
)
from media_security_audit.storage import JsonStore  # noqa: E402
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

    def test_mission_view_orders_scope_findings_and_remediation(self) -> None:
        store = JsonStore(clean_data_dir("web-ui-mission"))
        client = store.create_client(Client(name="Client Y"))
        mission = store.create_mission(
            Mission(
                client_id=client.id,
                name="Internal Audit",
                authorization_reference="AUTH-002",
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
        self.assertEqual(view.scope[0].status, "approved")
        self.assertEqual(view.findings[0].severity, "high")
        self.assertEqual(view.findings[0].review_note, "")
        self.assertEqual(view.reports, [])
        self.assertEqual(len(view.remediation_items), 1)
        self.assertIn("High-priority", view.executive_summary)


if __name__ == "__main__":
    unittest.main()
