from __future__ import annotations

import json
import shutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.mission_roadmap import (  # noqa: E402
    MissionRoadmapExportFormat,
    build_mission_roadmap_export,
    build_mission_roadmap_payload,
)
from media_security_audit.models import (  # noqa: E402
    AuditCheck,
    AuditType,
    Client,
    Mission,
    ScopeItem,
    ScopeType,
)
from media_security_audit.storage import JsonStore  # noqa: E402


def clean_data_dir(name: str) -> Path:
    root = Path(__file__).resolve().parents[1] / ".tmp-tests" / name
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    return root


class MissionRoadmapTests(unittest.TestCase):
    def test_builds_mission_roadmap_payload_and_exports(self) -> None:
        data_dir = clean_data_dir("mission-roadmap")
        reports_dir = clean_data_dir("mission-roadmap-reports")
        store = JsonStore(data_dir)
        client = store.create_client(Client(name="Client Roadmap"))
        mission = store.create_mission(
            Mission(
                client_id=client.id,
                name="External Roadmap Audit",
                audit_type=AuditType.EXTERNAL,
                authorization_reference="AUTH-ROADMAP-001",
                selected_checks=[AuditCheck.HTTP_HEADERS],
            )
        )
        store.add_scope_item(
            mission.id,
            ScopeItem(
                type=ScopeType.URL,
                value="https://example.invalid",
                approved=True,
            ),
        )

        payload = build_mission_roadmap_payload(store, mission.id, reports_dir)
        markdown = build_mission_roadmap_export(
            store,
            mission.id,
            reports_dir,
            MissionRoadmapExportFormat.MARKDOWN,
        )
        json_export = build_mission_roadmap_export(
            store,
            mission.id,
            reports_dir,
            MissionRoadmapExportFormat.JSON,
        )
        json_payload = json.loads(json_export.content)

        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["mission"]["name"], "External Roadmap Audit")
        self.assertEqual(payload["summary"]["steps"], 5)
        self.assertEqual(payload["summary"]["ready"], 2)
        self.assertEqual(payload["summary"]["warning"], 2)
        self.assertEqual(payload["summary"]["blocked"], 1)
        self.assertEqual(payload["steps"][0]["label"], "Authorization")
        self.assertEqual(payload["steps"][0]["status"], "ready")
        self.assertEqual(payload["steps"][2]["label"], "Guarded launch")
        self.assertEqual(payload["steps"][2]["status"], "warning")
        self.assertEqual(payload["steps"][4]["label"], "Reports and handoff")
        self.assertEqual(payload["steps"][4]["status"], "blocked")
        self.assertEqual(markdown.filename, f"{mission.id}-roadmap.md")
        self.assertEqual(markdown.media_type, "text/markdown; charset=utf-8")
        self.assertIn("# Mission Roadmap", markdown.content)
        self.assertIn("### 3. Guarded launch", markdown.content)
        self.assertEqual(json_export.filename, f"{mission.id}-roadmap.json")
        self.assertEqual(json_payload["mission"]["client_name"], "Client Roadmap")
        self.assertEqual(json_payload["steps"][3]["label"], "CVE/KEV review")


if __name__ == "__main__":
    unittest.main()
