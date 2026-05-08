from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.models import Client, Finding, Mission, MissionStatus, ScopeItem, ScopeType, Severity  # noqa: E402
from media_security_audit.storage import JsonStore  # noqa: E402


class JsonStoreTests(unittest.TestCase):
    def test_creates_client_and_mission(self) -> None:
        data_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / "storage-create"
        store = JsonStore(data_dir)
        client = store.create_client(Client(name="Client X"))
        mission = store.create_mission(Mission(client_id=client.id, name="Audit"))

        self.assertEqual(store.get_client(client.id).name, "Client X")
        self.assertEqual(store.get_mission(mission.id).name, "Audit")
        self.assertEqual(mission.status, MissionStatus.DRAFT)

    def test_approved_scope_updates_mission_status(self) -> None:
        data_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / "storage-status"
        store = JsonStore(data_dir)
        client = store.create_client(Client(name="Client X"))
        mission = store.create_mission(
            Mission(
                client_id=client.id,
                name="Audit",
                authorization_reference="signed-order",
            )
        )

        updated = store.add_scope_item(
            mission.id,
            ScopeItem(type=ScopeType.DOMAIN, value="example.invalid", approved=True),
        )

        self.assertEqual(updated.status, MissionStatus.READY_TO_SCAN)
        self.assertTrue(updated.has_approved_scope)

    def test_adds_and_deduplicates_findings(self) -> None:
        data_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / "storage-findings"
        store = JsonStore(data_dir)
        client = store.create_client(Client(name="Client X"))
        mission = store.create_mission(Mission(client_id=client.id, name="Audit"))

        first = Finding(
            title="Missing security header",
            severity=Severity.LOW,
            affected_asset="https://example.invalid",
            category="http_headers",
            source_module="manual",
            proof="Observed manually",
            risk="Browser-side protection is reduced.",
            remediation="Enable the missing header.",
            counter_test="Repeat the request and confirm the header.",
            confidence=0.7,
        )
        second = first.model_copy(
            update={
                "id": "finding_second",
                "severity": Severity.MEDIUM,
                "source_module": "http_headers",
                "proof": "Observed by scanner",
                "confidence": 0.9,
            }
        )

        store.add_finding(mission.id, first)
        stored = store.add_finding(mission.id, second)
        findings = store.list_findings(mission.id)

        self.assertEqual(len(findings), 1)
        self.assertEqual(stored.severity, Severity.MEDIUM)
        self.assertIn("manual", findings[0].sources)
        self.assertIn("http_headers", findings[0].sources)

    def test_missing_mission_error_names_the_id(self) -> None:
        data_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / "storage-missing"
        store = JsonStore(data_dir)

        with self.assertRaises(FileNotFoundError) as error:
            store.get_mission("missing")

        self.assertIn("mission not found: missing", str(error.exception))


if __name__ == "__main__":
    unittest.main()
