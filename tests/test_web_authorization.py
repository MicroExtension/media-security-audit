from __future__ import annotations

from datetime import date
from pathlib import Path
import shutil
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.models import AuditType, Client, Mission, ScopeItem, ScopeType  # noqa: E402
from media_security_audit.storage import JsonStore  # noqa: E402
from media_security_audit.web_authorization import (  # noqa: E402
    AuthorizationBriefFormat,
    authorization_brief_file,
    authorization_decision,
    generate_authorization_brief,
    list_authorization_briefs,
    render_authorization_brief_markdown,
)


def clean_dir(name: str) -> Path:
    path = Path(__file__).resolve().parents[1] / ".tmp-tests" / name
    if path.exists():
        shutil.rmtree(path)
    return path


class WebAuthorizationTests(unittest.TestCase):
    def test_generates_authorization_brief_files(self) -> None:
        data_dir = clean_dir("web-auth-brief-data")
        reports_dir = clean_dir("web-auth-brief-reports")
        store = JsonStore(data_dir)
        client = store.create_client(Client(name="Client Brief"))
        mission = store.create_mission(
            Mission(
                client_id=client.id,
                name="Authorized External Audit",
                audit_type=AuditType.EXTERNAL,
                audit_template_id="tpl_external_perimeter",
                authorization_reference="AUTH-2026-001",
                authorization_contact="RSSI Client",
                authorization_date=date(2026, 5, 10),
                authorization_expires_at=date(2026, 6, 10),
                emergency_contact="astreinte@example.invalid",
                report_recipients="direction@example.invalid",
                evidence_retention_days=90,
                scope=[
                    ScopeItem(
                        type=ScopeType.DOMAIN,
                        value="client.example",
                        approved=True,
                    )
                ],
            )
        )

        paths = generate_authorization_brief(store, mission.id, reports_dir)
        links = list_authorization_briefs(mission.id, reports_dir)
        markdown = authorization_brief_file(
            reports_dir,
            mission.id,
            AuthorizationBriefFormat.MARKDOWN,
        ).read_text(encoding="utf-8")
        html = authorization_brief_file(
            reports_dir,
            mission.id,
            AuthorizationBriefFormat.HTML,
        ).read_text(encoding="utf-8")

        self.assertEqual(len(paths), 2)
        self.assertTrue(all(path.exists() for path in paths))
        self.assertEqual([link.format for link in links], ["markdown", "html"])
        self.assertIn("Status: `ready_for_guarded_cli_execution`", markdown)
        self.assertIn("RSSI Client", markdown)
        self.assertIn("domain:client.example", markdown)
        self.assertIn("## Audit Template", markdown)
        self.assertIn("External Perimeter Review", markdown)
        self.assertIn("Approved public IP addresses and hostnames", markdown)
        self.assertIn("External exposure summary", markdown)
        self.assertIn("## Planned Scan Commands", markdown)
        self.assertIn("Execution: `not_executed`", markdown)
        self.assertIn("### Nmap", markdown)
        self.assertIn("nmap -sV", markdown)
        self.assertIn("TXT client.example", markdown)
        self.assertIn("<h2>Audit Template</h2>", html)
        self.assertIn("External Perimeter Review", html)
        self.assertIn("<h2>Planned Scan Commands</h2>", html)
        self.assertIn("not_executed", html)
        self.assertIn("TXT client.example", html)
        self.assertIn("No scan is executed by this brief.", markdown)

    def test_marks_missing_authorization_or_scope_as_not_ready(self) -> None:
        mission = Mission(client_id="client_1", name="Draft Audit")

        markdown = render_authorization_brief_markdown(mission, client_name="Client Draft")

        self.assertEqual(authorization_decision(mission), "not_ready")
        self.assertIn("Blocking items: `authorization reference, approved scope`", markdown)
        self.assertIn("Client Draft", markdown)
        self.assertNotIn("## Audit Template", markdown)
        self.assertIn("## Planned Scan Commands", markdown)
        self.assertIn("### Nmap", markdown)
        self.assertIn("Status: `blocked`", markdown)

    def test_missing_authorization_brief_has_named_error(self) -> None:
        reports_dir = clean_dir("web-auth-brief-missing")

        with self.assertRaises(FileNotFoundError) as error:
            authorization_brief_file(
                reports_dir,
                "mission_missing",
                AuthorizationBriefFormat.HTML,
            )

        self.assertIn("authorization brief not found: html", str(error.exception))


if __name__ == "__main__":
    unittest.main()
