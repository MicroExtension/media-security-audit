from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.models import AuditCheck, Mission, ScopeItem, ScopeType  # noqa: E402
from media_security_audit.scan_plan_exports import (  # noqa: E402
    ScanPlanExportFormat,
    build_scan_plan_export,
    format_scan_plan_json,
    format_scan_plan_markdown,
    format_scan_plan_text,
    scan_plan_payload,
)


class ScanPlanExportTests(unittest.TestCase):
    def test_builds_json_text_and_markdown_without_execution(self) -> None:
        mission = Mission(
            client_id="client_1",
            name="Pre Audit",
            authorization_reference="AUTH-PLAN",
            selected_checks=[AuditCheck.HTTP_HEADERS, AuditCheck.DNS_MAIL],
            scope=[
                ScopeItem(type=ScopeType.URL, value="https://client.example", approved=True),
                ScopeItem(type=ScopeType.DOMAIN, value="client.example", approved=True),
            ],
        )

        payload = scan_plan_payload(mission)
        json_payload = json.loads(format_scan_plan_json(mission))
        text = format_scan_plan_text(mission)
        markdown = format_scan_plan_markdown(mission)
        export = build_scan_plan_export(mission, ScanPlanExportFormat.JSON)

        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(json_payload["summary"]["execution"], "not_executed")
        self.assertEqual(json_payload["summary"]["ready"], 2)
        self.assertEqual(json_payload["summary"]["planned_commands"], 3)
        self.assertIn("Execution: not executed by this command", text)
        self.assertIn("[ready] HTTP Headers", text)
        self.assertIn("# Scan Plan", markdown)
        self.assertIn("## [ready] DNS/Mail", markdown)
        self.assertEqual(export.filename, f"{mission.id}-scan-plan.json")
        self.assertEqual(export.media_type, "application/json")

    def test_builds_markdown_export_filename(self) -> None:
        mission = Mission(client_id="client_1", name="Blocked Audit", selected_checks=[])

        export = build_scan_plan_export(mission, ScanPlanExportFormat.MARKDOWN)

        self.assertEqual(export.filename, f"{mission.id}-scan-plan.md")
        self.assertEqual(export.media_type, "text/markdown; charset=utf-8")
        self.assertIn("## [blocked] Check Selection", export.content)


if __name__ == "__main__":
    unittest.main()
