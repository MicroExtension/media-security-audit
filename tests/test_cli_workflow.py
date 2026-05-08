from __future__ import annotations

import io
import sys
import unittest
from contextlib import redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.cli import (  # noqa: E402
    add_finding,
    add_scope,
    app,
    create_client,
    create_mission,
    generate_mission_reports,
    list_scope,
    show_mission,
)
from media_security_audit.models import AuditType, MissionStatus, ScopeType, Severity  # noqa: E402


class CliWorkflowTests(unittest.TestCase):
    def test_creates_basic_local_workflow(self) -> None:
        root_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / "cli-workflow"
        data_dir = root_dir / "data"
        output_dir = root_dir / "reports"

        client = create_client(name="Client X", data_dir=data_dir)
        mission = create_mission(
            client_id=client.id,
            name="External audit",
            audit_type=AuditType.EXTERNAL,
            authorization_reference="signed-order",
            data_dir=data_dir,
        )
        updated = add_scope(
            mission_id=mission.id,
            scope_type=ScopeType.DOMAIN,
            value="example.invalid",
            approved=True,
            data_dir=data_dir,
        )
        finding = add_finding(
            mission_id=mission.id,
            title="Missing HSTS",
            severity=Severity.MEDIUM,
            affected_asset="https://example.invalid",
            category="http_headers",
            proof="HSTS header is absent.",
            risk="Users may be exposed to downgrade attempts.",
            remediation="Enable the Strict-Transport-Security header.",
            counter_test="Request the URL and confirm the HSTS header is present.",
            data_dir=data_dir,
        )
        reports = generate_mission_reports(
            mission_id=mission.id,
            data_dir=data_dir,
            output=output_dir,
        )

        self.assertEqual(updated.status, MissionStatus.READY_TO_SCAN)
        self.assertEqual(finding.title, "Missing HSTS")
        self.assertEqual(len(reports), 3)
        self.assertTrue(all(path.exists() for path in reports))
        self.assertIn("Missing HSTS", (output_dir / f"{mission.id}.md").read_text(encoding="utf-8"))

        summary = show_mission(mission_id=mission.id, data_dir=data_dir)
        scope_items = list_scope(mission_id=mission.id, data_dir=data_dir)

        self.assertIn("Status: ready_to_scan", summary)
        self.assertIn("Findings: 1", summary)
        self.assertEqual(len(scope_items), 1)
        self.assertEqual(scope_items[0].value, "example.invalid")

    def test_missing_mission_error_is_readable(self) -> None:
        data_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / "cli-errors"
        stderr = io.StringIO()

        with self.assertRaises(SystemExit) as error, redirect_stderr(stderr):
            app(["mission", "show", "--mission-id", "missing", "--data-dir", str(data_dir)])

        self.assertEqual(error.exception.code, 2)
        self.assertIn("error: mission not found: missing", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
