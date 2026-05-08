from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.models import Client, Mission, MissionStatus, ScopeItem, ScopeType  # noqa: E402
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


if __name__ == "__main__":
    unittest.main()
