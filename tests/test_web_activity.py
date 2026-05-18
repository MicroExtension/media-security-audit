from pathlib import Path
import csv
from datetime import datetime, timedelta, timezone
import json
import shutil
import sys
import unittest
from io import StringIO

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.models import (  # noqa: E402
    ActivityEvent,
    Client,
    Mission,
    utc_now,
)
from media_security_audit.storage import JsonStore  # noqa: E402
from media_security_audit.web_activity import (  # noqa: E402
    ActivityExportFormat,
    build_activity_log_export,
    build_activity_log_view,
)


def clean_dir(name: str) -> Path:
    path = Path(__file__).resolve().parents[1] / ".tmp-tests" / name
    if path.exists():
        shutil.rmtree(path)
    return path


class WebActivityTests(unittest.TestCase):
    def test_activity_template_links_rows_to_client_and_mission(self) -> None:
        template_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_templates"
            / "activity.html"
        )
        template = template_path.read_text(encoding="utf-8")

        self.assertIn('href="{{ row.client_url }}"', template)
        self.assertIn('href="{{ row.mission_url }}"', template)
        self.assertIn("{% if view.has_filters %}", template)
        self.assertIn("view.active_filters", template)
        self.assertIn('href="{{ view.clear_filters_url }}"', template)

    def test_builds_activity_log_view_across_missions(self) -> None:
        store = JsonStore(clean_dir("web-activity-view"))
        client_a = store.create_client(Client(name="Client A"))
        client_b = store.create_client(Client(name="Client B"))
        mission_a = store.create_mission(Mission(client_id=client_a.id, name="Audit A"))
        mission_b = store.create_mission(Mission(client_id=client_b.id, name="Audit B"))
        first_created_at = utc_now()
        first = store.add_activity_event(
            ActivityEvent(
                mission_id=mission_a.id,
                action="mission.created",
                summary="Mission created",
                created_at=first_created_at,
            )
        )
        second = store.add_activity_event(
            ActivityEvent(
                mission_id=mission_b.id,
                action="scope.added",
                summary="Scope added",
                created_at=first_created_at + timedelta(seconds=1),
                metadata={"scope_id": "scope_1"},
            )
        )

        view = build_activity_log_view(store)

        self.assertEqual(view.total_events, 2)
        self.assertEqual(view.mission_count, 2)
        self.assertEqual(view.client_count, 2)
        self.assertEqual(view.visible_events, 2)
        self.assertEqual(view.action_filter, "")
        self.assertEqual(view.query, "")
        self.assertEqual(view.date_from_filter, "")
        self.assertEqual(view.date_to_filter, "")
        self.assertFalse(view.has_filters)
        self.assertEqual(view.active_filters, [])
        self.assertEqual(view.clear_filters_url, "/activity")
        self.assertEqual(view.actions, ["mission.created", "scope.added"])
        self.assertEqual([option.label for option in view.clients], ["Client A", "Client B"])
        self.assertEqual(
            [option.label for option in view.missions],
            ["Client A / Audit A", "Client B / Audit B"],
        )
        self.assertEqual(
            [link.label for link in view.export_links],
            ["JSON", "Markdown", "HTML", "CSV"],
        )
        self.assertEqual(view.export_links[0].url, "/activity/export/json")
        self.assertEqual(view.export_links[3].url, "/activity/export/csv")
        self.assertEqual([row.id for row in view.rows], [second.id, first.id])
        self.assertEqual(view.rows[0].client_name, "Client B")
        self.assertEqual(view.rows[0].client_url, f"/clients/{client_b.id}")
        self.assertEqual(view.rows[0].mission_name, "Audit B")
        self.assertEqual(view.rows[0].mission_url, f"/missions/{mission_b.id}")
        self.assertEqual(view.rows[0].metadata_summary, "scope_id=scope_1")

    def test_filters_activity_log_by_query_and_action(self) -> None:
        store = JsonStore(clean_dir("web-activity-filter"))
        client = store.create_client(Client(name="Client Filter"))
        mission = store.create_mission(Mission(client_id=client.id, name="Filter Audit"))
        store.add_activity_event(
            ActivityEvent(
                mission_id=mission.id,
                action="mission.created",
                summary="Mission created",
            )
        )
        expected = store.add_activity_event(
            ActivityEvent(
                mission_id=mission.id,
                action="scope.added",
                summary="Scope added",
                metadata={"scope_id": "scope_1"},
            )
        )
        store.add_activity_event(
            ActivityEvent(
                mission_id=mission.id,
                action="reports.generated",
                summary="Generated 3 report export(s)",
                metadata={"report_count": "3"},
            )
        )

        view = build_activity_log_view(store, query="scope_1", action="scope.added")
        export = build_activity_log_export(
            store,
            ActivityExportFormat.JSON,
            query="scope_1",
            action="scope.added",
        )
        payload = json.loads(export.content)

        self.assertEqual(view.total_events, 3)
        self.assertEqual(view.visible_events, 1)
        self.assertEqual(view.action_filter, "scope.added")
        self.assertEqual(view.query, "scope_1")
        self.assertEqual(
            view.export_links[0].url,
            "/activity/export/json?q=scope_1&action=scope.added",
        )
        self.assertEqual([row.id for row in view.rows], [expected.id])
        self.assertEqual(export.filename, "activity-log-scope-added-filtered.json")
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["total_events"], 3)
        self.assertEqual(payload["action"], "scope.added")
        self.assertEqual(payload["query"], "scope_1")
        self.assertEqual(payload["events"][0]["id"], expected.id)

    def test_filters_activity_log_by_client_and_mission(self) -> None:
        store = JsonStore(clean_dir("web-activity-client-mission-filter"))
        client_a = store.create_client(Client(name="Client A"))
        client_b = store.create_client(Client(name="Client B"))
        mission_a = store.create_mission(Mission(client_id=client_a.id, name="Audit A"))
        mission_b = store.create_mission(Mission(client_id=client_b.id, name="Audit B"))
        store.add_activity_event(
            ActivityEvent(
                mission_id=mission_a.id,
                action="mission.created",
                summary="Mission A created",
            )
        )
        expected = store.add_activity_event(
            ActivityEvent(
                mission_id=mission_b.id,
                action="mission.created",
                summary="Mission B created",
            )
        )

        view = build_activity_log_view(
            store,
            client_id=client_b.id,
            mission_id=mission_b.id,
        )
        export = build_activity_log_export(
            store,
            ActivityExportFormat.JSON,
            client_id=client_b.id,
            mission_id=mission_b.id,
        )
        payload = json.loads(export.content)

        self.assertEqual(view.total_events, 2)
        self.assertEqual(view.visible_events, 1)
        self.assertEqual(view.client_filter, client_b.id)
        self.assertEqual(view.mission_filter, mission_b.id)
        self.assertTrue(view.has_filters)
        self.assertEqual(
            [(item.label, item.value, item.url) for item in view.active_filters],
            [
                ("Client", "Client B", f"/clients/{client_b.id}"),
                ("Mission", "Client B / Audit B", f"/missions/{mission_b.id}"),
            ],
        )
        self.assertEqual(view.clear_filters_url, "/activity")
        self.assertEqual(
            view.export_links[0].url,
            f"/activity/export/json?client_id={client_b.id}&mission_id={mission_b.id}",
        )
        self.assertEqual([row.id for row in view.rows], [expected.id])
        self.assertEqual(export.filename, "activity-log-client-mission-filtered.json")
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["total_events"], 2)
        self.assertEqual(payload["client_id"], client_b.id)
        self.assertEqual(payload["mission_id"], mission_b.id)
        self.assertEqual(payload["events"][0]["client_id"], client_b.id)
        self.assertEqual(payload["events"][0]["mission_id"], mission_b.id)

    def test_filters_activity_log_by_date_range(self) -> None:
        store = JsonStore(clean_dir("web-activity-date-filter"))
        client = store.create_client(Client(name="Client Date"))
        mission = store.create_mission(Mission(client_id=client.id, name="Date Audit"))
        store.add_activity_event(
            ActivityEvent(
                mission_id=mission.id,
                action="mission.created",
                summary="Created before range",
                created_at=datetime(2026, 5, 9, 10, 0, tzinfo=timezone.utc),
            )
        )
        expected = store.add_activity_event(
            ActivityEvent(
                mission_id=mission.id,
                action="scope.added",
                summary="Created inside range",
                created_at=datetime(2026, 5, 10, 10, 0, tzinfo=timezone.utc),
            )
        )
        store.add_activity_event(
            ActivityEvent(
                mission_id=mission.id,
                action="reports.generated",
                summary="Created after range",
                created_at=datetime(2026, 5, 11, 10, 0, tzinfo=timezone.utc),
            )
        )

        view = build_activity_log_view(
            store,
            date_from="2026-05-10",
            date_to="2026-05-10",
        )
        export = build_activity_log_export(
            store,
            ActivityExportFormat.JSON,
            date_from="2026-05-10",
            date_to="2026-05-10",
        )
        csv_export = build_activity_log_export(
            store,
            ActivityExportFormat.CSV,
            date_from="2026-05-10",
            date_to="2026-05-10",
        )
        payload = json.loads(export.content)
        csv_rows = list(csv.DictReader(StringIO(csv_export.content)))

        self.assertEqual(view.total_events, 3)
        self.assertEqual(view.visible_events, 1)
        self.assertEqual(view.date_from_filter, "2026-05-10")
        self.assertEqual(view.date_to_filter, "2026-05-10")
        self.assertEqual(
            view.export_links[0].url,
            "/activity/export/json?date_from=2026-05-10&date_to=2026-05-10",
        )
        self.assertEqual([row.id for row in view.rows], [expected.id])
        self.assertEqual(export.filename, "activity-log-dates-filtered.json")
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["total_events"], 3)
        self.assertEqual(payload["date_from"], "2026-05-10")
        self.assertEqual(payload["date_to"], "2026-05-10")
        self.assertEqual(payload["events"][0]["created_date"], "2026-05-10")
        self.assertEqual(csv_export.filename, "activity-log-dates-filtered.csv")
        self.assertEqual(len(csv_rows), 1)
        self.assertEqual(csv_rows[0]["id"], expected.id)
        self.assertEqual(csv_rows[0]["created_date"], "2026-05-10")

    def test_exports_activity_log_as_json_markdown_and_html(self) -> None:
        store = JsonStore(clean_dir("web-activity-export"))
        client = store.create_client(Client(name="Client Export"))
        mission = store.create_mission(Mission(client_id=client.id, name="Export Audit"))
        store.add_activity_event(
            ActivityEvent(
                mission_id=mission.id,
                action="reports.generated",
                summary="Generated 3 report export(s)",
                metadata={"report_count": "3"},
            )
        )

        json_export = build_activity_log_export(store, ActivityExportFormat.JSON)
        markdown_export = build_activity_log_export(store, ActivityExportFormat.MARKDOWN)
        html_export = build_activity_log_export(store, ActivityExportFormat.HTML)
        csv_export = build_activity_log_export(store, ActivityExportFormat.CSV)

        payload = json.loads(json_export.content)
        csv_rows = list(csv.DictReader(StringIO(csv_export.content)))
        self.assertEqual(json_export.filename, "activity-log.json")
        self.assertEqual(json_export.media_type, "application/json")
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["events"][0]["action"], "reports.generated")
        self.assertEqual(payload["events"][0]["metadata"], {"report_count": "3"})
        self.assertEqual(markdown_export.filename, "activity-log.md")
        self.assertIn("# Activity Log", markdown_export.content)
        self.assertIn("Generated 3 report export(s)", markdown_export.content)
        self.assertEqual(html_export.filename, "activity-log.html")
        self.assertIn("<!doctype html>", html_export.content)
        self.assertIn("Client Export", html_export.content)
        self.assertEqual(csv_export.filename, "activity-log.csv")
        self.assertEqual(csv_export.media_type, "text/csv; charset=utf-8")
        self.assertEqual(csv_rows[0]["client_name"], "Client Export")
        self.assertEqual(csv_rows[0]["mission_name"], "Export Audit")
        self.assertEqual(csv_rows[0]["action"], "reports.generated")
        self.assertEqual(csv_rows[0]["metadata"], "report_count=3")


if __name__ == "__main__":
    unittest.main()
