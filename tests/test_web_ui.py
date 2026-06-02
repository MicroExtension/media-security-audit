import csv
import json
import re
import shutil
import unittest
from datetime import date
from hashlib import sha256
from io import BytesIO, StringIO
from pathlib import Path
from zipfile import ZipFile

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
from media_security_audit.web_auth import WebAuthSettings  # noqa: E402
from media_security_audit.web_exports import generate_mission_export  # noqa: E402
from media_security_audit.web_pilot import (  # noqa: E402
    PilotReadinessItem,
    build_pilot_acceptance_json_export,
    build_pilot_attention_export,
    build_pilot_attention_json_export,
    build_pilot_bundle_inventory_csv_export,
    build_pilot_bundle_inventory_json_export,
    build_pilot_bundle_index_export,
    build_pilot_bundle_index_json_export,
    build_pilot_delivery_receipt_export,
    build_pilot_delivery_receipt_json_export,
    build_pilot_evidence_bundle,
    build_pilot_evidence_manifest,
    build_pilot_evidence_verification,
    build_pilot_evidence_verification_json,
    build_pilot_handoff_summary_export,
    build_pilot_handoff_summary_json_export,
    build_pilot_readiness_json_export,
    build_pilot_readiness_items,
    build_pilot_runbook_json_export,
    build_pilot_runbook_view,
    format_pilot_acceptance_markdown,
    format_pilot_readiness_markdown,
    format_pilot_runbook_markdown,
)
from media_security_audit.web_system import build_system_status  # noqa: E402
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
    def test_base_template_marks_active_top_navigation(self) -> None:
        template_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_templates"
            / "base.html"
        )
        template = template_path.read_text(encoding="utf-8")

        self.assertIn("{% set current_path = request.url.path %}", template)
        self.assertIn("dashboard_active", template)
        self.assertIn('aria-current="page"', template)
        self.assertIn('class="skip-link"', template)
        self.assertIn('href="#main-content"', template)
        self.assertIn('id="main-content"', template)
        self.assertIn('tabindex="-1"', template)
        self.assertIn('aria-label="Primary navigation"', template)
        self.assertIn('role="status"', template)
        self.assertIn('aria-live="polite"', template)
        self.assertIn('role="alert"', template)
        self.assertIn('aria-label="Workspace metadata"', template)

        self.assertIn('href="/exports"', template)
        self.assertIn(">Exports</a>", template)
        self.assertIn('href="/pilot"', template)
        self.assertIn(">Pilot</a>", template)

        for prefix in [
            "/activity",
            "/exports",
            "/templates",
            "/remediations",
            "/pilot",
            "/system",
        ]:
            self.assertIn(f"current_path.startswith('{prefix}')", template)

    def test_global_styles_expose_visible_keyboard_focus(self) -> None:
        css_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_static"
            / "app.css"
        )
        css = css_path.read_text(encoding="utf-8")

        self.assertIn(":focus-visible", css)
        self.assertIn("outline-offset", css)
        self.assertIn("button:focus-visible", css)
        self.assertIn("textarea:focus-visible", css)

    def test_global_styles_mark_required_fields(self) -> None:
        css_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_static"
            / "app.css"
        )
        css = css_path.read_text(encoding="utf-8")

        self.assertIn("label:has(input[required])", css)
        self.assertIn("label:has(select[required])", css)
        self.assertIn("label:has(textarea[required])", css)
        self.assertIn('content: " *";', css)
        self.assertIn(".counter-test-form", css)
        self.assertIn(".counter-test-actions", css)
        self.assertIn(".counter-test-summary", css)
        self.assertIn(".counter-test-summary-passed", css)

    def test_global_styles_expose_anchor_target_context(self) -> None:
        css_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_static"
            / "app.css"
        )
        css = css_path.read_text(encoding="utf-8")

        self.assertIn("scroll-margin-top", css)
        self.assertIn(".section:target", css)
        self.assertIn(".report-links:target", css)
        self.assertIn("outline-offset", css)

    def test_table_templates_expose_accessible_captions(self) -> None:
        template_dir = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_templates"
        )
        css = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_static"
            / "app.css"
        ).read_text(encoding="utf-8")

        self.assertIn(".sr-only", css)
        for filename in [
            "activity.html",
            "client.html",
            "dashboard.html",
            "exports.html",
            "mission.html",
            "system.html",
        ]:
            template = (template_dir / filename).read_text(encoding="utf-8")
            self.assertEqual(
                template.count("<table>"),
                template.count('<caption class="sr-only">'),
                filename,
            )

    def test_form_templates_expose_accessible_names(self) -> None:
        template_dir = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_templates"
        )

        for path in template_dir.glob("*.html"):
            template = path.read_text(encoding="utf-8")
            for form_tag in re.findall(r"<form\b[^>]*>", template):
                self.assertIn("aria-label=", form_tag, f"{path.name}: {form_tag}")

    def test_mission_template_groups_checkbox_controls(self) -> None:
        template_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_templates"
            / "mission.html"
        )
        css_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_static"
            / "app.css"
        )
        template = template_path.read_text(encoding="utf-8")
        css = css_path.read_text(encoding="utf-8")

        self.assertIn("<fieldset class=\"field-group\">", template)
        self.assertIn("<legend>Audit Checks</legend>", template)
        self.assertIn("<legend>Scope Status</legend>", template)
        self.assertEqual(template.count("<fieldset"), template.count("</fieldset>"))
        self.assertIn(".field-group", css)
        self.assertIn(".field-group legend", css)

    def test_dashboard_template_exposes_shortcut_anchors(self) -> None:
        template_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_templates"
            / "dashboard.html"
        )
        template = template_path.read_text(encoding="utf-8")

        for anchor in [
            "ready-missions",
            "review-missions",
            "blocked-missions",
            "no-mission-clients",
            "blocked-clients",
            "top-risk-clients",
            "review-backlog-clients",
            "counter-tests",
            "failed-counter-tests",
            "preparation",
        ]:
            self.assertIn(f'href="#{anchor}"', template)
            self.assertIn(f'id="{anchor}"', template)

        for counter in [
            "view.ready_missions|length",
            "view.review_missions|length",
            "view.blocked_missions|length",
            "view.no_mission_clients|length",
            "view.blocked_clients|length",
            "view.top_risk_clients|length",
            "view.review_backlog_clients|length",
            "view.counter_test_summary|length",
            "view.failed_counter_test_missions|length",
            "view.preparation_items|length",
        ]:
            self.assertIn(f"{{{{ {counter} }}}}", template)

        self.assertIn('aria-label="Workspace counter-test summary"', template)
        self.assertIn("Failed counter-test missions watchlist", template)
        self.assertIn("mission.counter_test_failed_count", template)
        self.assertIn("/missions/{{ mission.id }}#counter-test", template)
        self.assertIn("mission.counter_test_ready_count", template)
        self.assertIn("mission.counter_test_passed_count", template)
        self.assertIn("mission.counter_test_failed_count", template)
        self.assertIn('id="new-mission"', template)
        self.assertIn("item.next_action_href", template)
        self.assertIn("client.next_action_href", template)
        self.assertIn("client.export_inventory_url", template)
        self.assertIn("mission.preparation_action_href", template)

    def test_client_template_exposes_preparation_action_links(self) -> None:
        template_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_templates"
            / "client.html"
        )
        template = template_path.read_text(encoding="utf-8")

        self.assertIn("item.next_action_href", template)
        self.assertIn("item.next_action_label", template)
        self.assertIn('href="{{ view.export_inventory_url }}"', template)
        self.assertIn('href="{{ view.activity_log_url }}"', template)
        self.assertIn("mission.preparation_action_href", template)
        self.assertIn("mission.preparation_action_label", template)

        for anchor in [
            "client-dispositions",
            "client-counter-tests",
            "client-failed-counter-tests",
            "client-preparation",
            "client-activity",
            "client-missions",
        ]:
            self.assertIn(f'href="#{anchor}"', template)
            self.assertIn(f'id="{anchor}"', template)

        for counter in [
            "view.finding_dispositions|length",
            "view.counter_test_summary|length",
            "view.failed_counter_test_missions|length",
            "view.preparation_items|length",
            "view.recent_activity_events|length",
            "view.missions|length",
        ]:
            self.assertIn(f"{{{{ {counter} }}}}", template)

        self.assertIn('aria-label="Client counter-test summary"', template)
        self.assertIn("Client failed counter-test missions watchlist", template)
        self.assertIn("mission.counter_test_failed_count", template)
        self.assertIn("/missions/{{ mission.id }}#counter-test", template)
        self.assertIn("mission.counter_test_ready_count", template)
        self.assertIn("mission.counter_test_passed_count", template)
        self.assertIn("mission.counter_test_failed_count", template)

    def test_export_inventory_template_exposes_package_actions(self) -> None:
        template_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_templates"
            / "exports.html"
        )
        template = template_path.read_text(encoding="utf-8")

        self.assertIn('aria-label="Mission export shortcuts"', template)
        self.assertIn('href="#export-filters"', template)
        self.assertIn('href="#mission-export-inventory"', template)
        self.assertIn('href="#export-downloads"', template)
        self.assertIn("active_filters|length", template)
        self.assertIn("{% if has_filters %}", template)
        self.assertIn("active_filters", template)
        self.assertIn('aria-label="Active mission export filters"', template)
        self.assertIn('href="{{ clear_filters_url }}"', template)
        self.assertIn("total_items", template)
        self.assertIn('id="export-filters"', template)
        self.assertIn('aria-label="Filter mission exports"', template)
        self.assertIn('aria-label="Mission export inventory summary"', template)
        self.assertIn('id="mission-export-inventory"', template)
        self.assertIn('id="export-downloads"', template)
        self.assertIn('aria-label="Mission export inventory downloads"', template)
        self.assertIn('name="q"', template)
        self.assertIn('name="status"', template)
        self.assertIn("status_options", template)
        self.assertIn('name="include_missing"', template)
        self.assertIn('summary["items"]', template)
        self.assertIn("summary.packages", template)
        self.assertIn("summary.ready", template)
        self.assertIn("summary.warning", template)
        self.assertIn("summary.failed", template)
        self.assertIn("summary.missing", template)
        self.assertIn("item.mission_name", template)
        self.assertIn("item.client_name", template)
        self.assertIn('name="client_id"', template)
        self.assertIn("client_options", template)
        self.assertIn("client_filter", template)
        self.assertIn("item.status", template)
        self.assertIn("item.detail", template)
        self.assertIn("/exports/download/csv?{{ download_query }}", template)
        self.assertIn("/exports/download/markdown?{{ download_query }}", template)
        self.assertIn("/exports/download/json?{{ download_query }}", template)
        self.assertIn("/missions/{{ item.mission_id }}/export", template)
        self.assertIn("/exports?{{ toggle_query }}", template)

    def test_web_exports_route_is_inventory_only(self) -> None:
        web_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web.py"
        )
        web = web_path.read_text(encoding="utf-8")

        self.assertIn('@app.get("/exports"', web)
        self.assertIn('@app.get("/exports/download/{export_format}"', web)
        self.assertIn("MISSION_EXPORT_INVENTORY_STATUSES", web)
        self.assertIn("MissionExportInventoryFormat", web)
        self.assertIn("build_mission_export_inventory_export", web)
        self.assertIn("build_mission_export_inventory", web)
        self.assertIn("filter_mission_export_inventory", web)
        self.assertIn("mission_export_inventory_filter_payload", web)
        self.assertIn("mission_export_inventory_payload", web)
        self.assertIn("mission_export_inventory_active_filters", web)
        self.assertIn('"exports.html"', web)
        self.assertIn("q: str | None = None", web)
        self.assertIn("status: str | None = None", web)
        self.assertIn("client_id: str | None = None", web)
        self.assertIn("client_options = sorted(store.list_clients()", web)
        self.assertIn("client_id=client_filter", web)
        self.assertIn("include_missing: bool = True", web)

    def test_pilot_template_exposes_client_pilot_runbook(self) -> None:
        template_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_templates"
            / "pilot.html"
        )
        template = template_path.read_text(encoding="utf-8")

        self.assertIn("view.title", template)
        self.assertIn("view.subtitle", template)
        self.assertIn("view.metrics", template)
        self.assertIn("view.sections", template)
        self.assertIn("view.acceptance_items", template)
        self.assertIn("view.readiness_items", template)
        self.assertIn("view.attention_items", template)
        self.assertIn("view.readiness_rollup", template)
        self.assertIn("view.evidence_files", template)
        self.assertIn('aria-label="Pilot runbook summary"', template)
        self.assertIn('aria-label="Pilot readiness rollup"', template)
        self.assertIn("view.readiness_rollup.status", template)
        self.assertIn("view.readiness_rollup.ready", template)
        self.assertIn("view.readiness_rollup.warning", template)
        self.assertIn("view.readiness_rollup.blocked", template)
        self.assertIn('aria-label="Pilot evidence file categories"', template)
        self.assertIn("view.evidence_automation_file_count", template)
        self.assertIn("view.evidence_human_file_count", template)
        self.assertIn('aria-label="Pilot runbook shortcuts"', template)
        self.assertIn('id="pilot-attention"', template)
        self.assertIn('aria-label="Pilot attention links"', template)
        self.assertIn('id="pilot-bundle"', template)
        self.assertIn('aria-label="Pilot evidence bundle links"', template)
        self.assertIn('<caption class="sr-only">Pilot evidence bundle files</caption>', template)
        self.assertIn("<th>Kind</th>", template)
        self.assertIn("item.kind", template)
        self.assertIn("item.sha256_short", template)
        self.assertIn('id="pilot-readiness"', template)
        self.assertIn('aria-label="Pilot readiness links"', template)
        self.assertIn('href="/pilot/acceptance.json"', template)
        self.assertIn('href="/pilot/attention.json"', template)
        self.assertIn('href="/pilot/attention.md"', template)
        self.assertIn('href="/pilot/bundle-inventory.csv"', template)
        self.assertIn('href="/pilot/bundle-inventory.json"', template)
        self.assertIn('href="/pilot/bundle-index.json"', template)
        self.assertIn('href="/pilot/bundle-index.md"', template)
        self.assertIn('href="/pilot/delivery-receipt.md"', template)
        self.assertIn('href="/pilot/delivery-receipt.json"', template)
        self.assertIn('href="/pilot/handoff-summary.md"', template)
        self.assertIn('href="/pilot/handoff-summary.json"', template)
        self.assertIn('href="/pilot/readiness.json"', template)
        self.assertIn('href="/pilot/readiness.md"', template)
        self.assertIn('href="/pilot/bundle.zip"', template)
        self.assertIn('href="/pilot/bundle-manifest.json"', template)
        self.assertIn('href="/pilot/bundle-verification.md"', template)
        self.assertIn('href="/pilot/bundle-verification.json"', template)
        self.assertIn("item.status", template)
        self.assertIn("item.href", template)
        self.assertIn('href="/pilot/runbook.md"', template)
        self.assertIn('href="/pilot/runbook.json"', template)
        self.assertIn('href="/pilot/acceptance.md"', template)
        self.assertIn("section.anchor", template)
        self.assertIn("section.steps|length", template)
        self.assertIn("section.links", template)
        self.assertIn("step.title", template)
        self.assertIn("step.detail", template)
        self.assertIn('id="pilot-acceptance"', template)
        self.assertIn('aria-label="Pilot acceptance export"', template)
        self.assertIn("item.phase", template)
        self.assertIn("item.evidence", template)

        view = build_pilot_runbook_view()
        anchors = [section.anchor for section in view.sections]
        self.assertEqual(
            anchors,
            [
                "pilot-setup",
                "pilot-mission",
                "pilot-review",
                "pilot-handoff",
                "pilot-closeout",
            ],
        )
        hrefs = {link.href for section in view.sections for link in section.links}
        for href in [
            "/",
            "/system",
            "/templates",
            "/activity",
            "/remediations",
            "/exports",
            "/system#system-backup",
        ]:
            self.assertIn(href, hrefs)
        self.assertEqual(len(view.acceptance_items), 11)
        self.assertEqual(view.attention_items, [])
        self.assertEqual(view.readiness_rollup.status, "warning")
        self.assertEqual(view.readiness_rollup.total, 0)
        self.assertEqual(view.readiness_rollup.detail, "No readiness item was generated.")
        self.assertEqual(
            [item.path for item in view.evidence_files],
            [
                "pilot-acceptance-checklist.json",
                "pilot-acceptance-checklist.md",
                "pilot-attention.json",
                "pilot-attention.md",
                "pilot-bundle-index.json",
                "pilot-bundle-index.md",
                "pilot-bundle-inventory.json",
                "pilot-delivery-receipt.json",
                "pilot-delivery-receipt.md",
                "pilot-handoff-summary.json",
                "pilot-handoff-summary.md",
                "pilot-readiness.json",
                "pilot-readiness.md",
                "pilot-runbook.json",
                "pilot-runbook.md",
            ],
        )
        self.assertEqual(view.evidence_automation_file_count, 8)
        self.assertEqual(view.evidence_human_file_count, 7)
        self.assertEqual(view.evidence_files[0].kind, "Automation JSON")
        self.assertEqual(view.evidence_files[1].kind, "Human-readable Markdown")
        self.assertEqual(
            len([item for item in view.evidence_files if item.kind == "Automation JSON"]),
            8,
        )
        self.assertEqual(
            len(
                [
                    item
                    for item in view.evidence_files
                    if item.kind == "Human-readable Markdown"
                ]
            ),
            7,
        )
        self.assertTrue(all(len(item.sha256_short) == 12 for item in view.evidence_files))
        acceptance_titles = [item.title for item in view.acceptance_items]
        self.assertIn("Appliance status reviewed", acceptance_titles)
        self.assertIn("Workspace backup created", acceptance_titles)

        markdown = format_pilot_runbook_markdown(view)
        self.assertIn("# Pilot Runbook", markdown)
        for title in [
            "Setup",
            "Mission",
            "Review",
            "Handoff",
            "Closeout",
        ]:
            self.assertIn(f"### {title}", markdown)
        for step in [
            "Check appliance status",
            "Create client and mission",
            "Review dispositions",
            "Verify export inventory",
            "Plan next iteration",
        ]:
            self.assertIn(step, markdown)

    def test_pilot_runbook_view_keeps_known_phase_counts(self) -> None:
        view = build_pilot_runbook_view()
        counts = {section.title: len(section.steps) for section in view.sections}

        self.assertEqual(
            counts,
            {
                "Setup": 3,
                "Mission": 4,
                "Review": 4,
                "Handoff": 4,
                "Closeout": 3,
            },
        )
        self.assertEqual(
            [metric.value for metric in view.metrics],
            ["5", "Local", "Guarded", "Reports"],
        )
        self.assertEqual(len(view.acceptance_items), 11)
        self.assertEqual(view.readiness_items, [])
        self.assertEqual(view.attention_items, [])
        self.assertEqual(view.readiness_rollup.warning, 0)
        self.assertEqual(len(view.evidence_files), 15)

    def test_pilot_readiness_items_summarize_workspace_state(self) -> None:
        root_dir = clean_data_dir("web-ui-pilot-readiness")
        data_dir = root_dir / "data"
        reports_dir = root_dir / "reports"
        reports_dir.mkdir(parents=True)
        store = JsonStore(data_dir)
        client = store.create_client(Client(name="Pilot Client"))
        mission = store.create_mission(Mission(client_id=client.id, name="Pilot Audit"))
        generate_mission_export(store, mission.id, reports_dir)
        system_status = build_system_status(
            data_dir=data_dir,
            reports_dir=reports_dir,
            auth_settings=WebAuthSettings(enabled=True, username="pilot", password="secret"),
            tool_resolver=lambda command: f"/usr/bin/{command}",
        )

        items = build_pilot_readiness_items(store, reports_dir, system_status)
        view = build_pilot_runbook_view(readiness_items=items)
        by_label = {item.label: item for item in items}

        self.assertEqual(by_label["Web authentication"].status, "ready")
        self.assertEqual(by_label["Storage readiness"].status, "ready")
        self.assertEqual(by_label["Client records"].detail, "1 client record(s) available.")
        self.assertEqual(by_label["Mission records"].detail, "1 mission record(s) available.")
        self.assertEqual(by_label["Mission exports"].status, "ready")
        self.assertIn("1 ready package(s)", by_label["Mission exports"].detail)
        self.assertEqual(by_label["Workspace backup"].status, "warning")
        self.assertEqual(by_label["External tools"].detail, "5/5 tool(s) available.")
        self.assertEqual(view.readiness_rollup.status, "warning")
        self.assertEqual(view.readiness_rollup.ready, 6)
        self.assertEqual(view.readiness_rollup.warning, 1)
        self.assertEqual(view.readiness_rollup.blocked, 0)
        self.assertEqual(view.readiness_rollup.total, 7)
        self.assertEqual(view.readiness_rollup.detail, "6 ready, 1 warning, 0 blocked.")
        self.assertEqual(len(view.attention_items), 1)
        self.assertEqual(view.attention_items[0].label, "Workspace backup")
        self.assertEqual(view.attention_items[0].status, "warning")
        attention_export = build_pilot_attention_export(items)
        self.assertEqual(attention_export.filename, "pilot-attention.md")
        self.assertEqual(attention_export.media_type, "text/markdown; charset=utf-8")
        self.assertIn("# Pilot Attention Items", attention_export.content)
        self.assertIn("- Open items: `1`", attention_export.content)
        self.assertIn("| Workspace backup | warning |", attention_export.content)
        attention_json = build_pilot_attention_json_export(items)
        attention_payload = json.loads(attention_json.content)
        self.assertEqual(attention_json.filename, "pilot-attention.json")
        self.assertEqual(attention_json.media_type, "application/json")
        self.assertEqual(attention_payload, attention_json.payload)
        self.assertEqual(attention_payload["schema_version"], 1)
        self.assertEqual(attention_payload["attention_type"], "pilot")
        self.assertEqual(attention_payload["open_item_count"], 1)
        self.assertEqual(attention_payload["items"][0]["label"], "Workspace backup")
        handoff_summary = build_pilot_handoff_summary_export(items)
        self.assertEqual(handoff_summary.filename, "pilot-handoff-summary.md")
        self.assertEqual(handoff_summary.media_type, "text/markdown; charset=utf-8")
        self.assertIn("# Pilot Handoff Summary", handoff_summary.content)
        self.assertIn("- Readiness status: `warning`", handoff_summary.content)
        self.assertIn("- Attention items: `1`", handoff_summary.content)
        self.assertIn("pilot-bundle-index.md", handoff_summary.content)
        self.assertIn("pilot-delivery-receipt.md", handoff_summary.content)
        self.assertIn("pilot-handoff-summary.json", handoff_summary.content)
        self.assertIn("pilot-readiness.json", handoff_summary.content)
        self.assertIn("pilot-attention.md", handoff_summary.content)
        handoff_json = build_pilot_handoff_summary_json_export(items)
        handoff_payload = json.loads(handoff_json.content)
        self.assertEqual(handoff_json.filename, "pilot-handoff-summary.json")
        self.assertEqual(handoff_json.media_type, "application/json")
        self.assertEqual(handoff_payload, handoff_json.payload)
        self.assertEqual(handoff_payload["schema_version"], 1)
        self.assertEqual(handoff_payload["handoff_type"], "pilot")
        self.assertEqual(handoff_payload["context"], "Client Pilot")
        self.assertEqual(handoff_payload["source"], "Pilot Runbook")
        self.assertEqual(handoff_payload["readiness"]["status"], "warning")
        self.assertEqual(handoff_payload["readiness"]["warning"], 1)
        self.assertEqual(handoff_payload["next_action_count"], 1)
        self.assertEqual(handoff_payload["attention_items"][0]["label"], "Workspace backup")
        self.assertEqual(handoff_payload["attention_items"][0]["status"], "warning")
        self.assertIn("pilot-attention.json", handoff_payload["handoff_files"])
        self.assertIn("pilot-bundle-index.json", handoff_payload["handoff_files"])
        self.assertIn("pilot-bundle-inventory.json", handoff_payload["handoff_files"])
        self.assertIn("pilot-handoff-summary.json", handoff_payload["handoff_files"])
        self.assertIn("pilot-readiness.json", handoff_payload["handoff_files"])
        self.assertIn("pilot-runbook.json", handoff_payload["handoff_files"])
        bundle_index = build_pilot_bundle_index_export(items)
        self.assertEqual(bundle_index.filename, "pilot-bundle-index.md")
        self.assertEqual(bundle_index.media_type, "text/markdown; charset=utf-8")
        self.assertIn("# Pilot Evidence Bundle Index", bundle_index.content)
        self.assertIn("Open `pilot-handoff-summary.md` first", bundle_index.content)
        self.assertIn("pilot-acceptance-checklist.json", bundle_index.content)
        self.assertIn("pilot-attention.json", bundle_index.content)
        self.assertIn("pilot-bundle-index.json", bundle_index.content)
        self.assertIn("pilot-bundle-inventory.json", bundle_index.content)
        self.assertIn("pilot-delivery-receipt.json", bundle_index.content)
        self.assertIn("pilot-handoff-summary.json", bundle_index.content)
        self.assertIn("pilot-delivery-receipt.md", bundle_index.content)
        self.assertIn("pilot-readiness.json", bundle_index.content)
        self.assertIn("| manifest.json | File checksums", bundle_index.content)
        bundle_index_json = build_pilot_bundle_index_json_export(items)
        bundle_index_payload = json.loads(bundle_index_json.content)
        self.assertEqual(bundle_index_json.filename, "pilot-bundle-index.json")
        self.assertEqual(bundle_index_json.media_type, "application/json")
        self.assertEqual(bundle_index_payload, bundle_index_json.payload)
        self.assertEqual(bundle_index_payload["schema_version"], 1)
        self.assertEqual(bundle_index_payload["index_type"], "pilot_evidence")
        self.assertEqual(bundle_index_payload["bundle_file_count"], 15)
        self.assertEqual(bundle_index_payload["review_step_count"], 16)
        self.assertEqual(bundle_index_payload["review_order"][3]["path"], "pilot-bundle-index.json")
        self.assertEqual(
            bundle_index_payload["review_order"][4]["path"],
            "pilot-bundle-inventory.json",
        )
        inventory_csv = build_pilot_bundle_inventory_csv_export(items)
        inventory_rows = list(csv.DictReader(StringIO(inventory_csv.content)))
        self.assertEqual(inventory_csv.filename, "pilot-bundle-inventory.csv")
        self.assertEqual(inventory_csv.media_type, "text/csv; charset=utf-8")
        self.assertEqual(
            inventory_csv.content.splitlines()[0],
            "review_order,path,kind,size_bytes,sha256,sha256_short",
        )
        self.assertEqual(inventory_rows[0]["path"], "pilot-acceptance-checklist.json")
        self.assertEqual(inventory_rows[0]["kind"], "Automation JSON")
        self.assertEqual(inventory_rows[0]["review_order"], "11")
        self.assertEqual(inventory_rows[1]["path"], "pilot-acceptance-checklist.md")
        self.assertEqual(inventory_rows[1]["kind"], "Human-readable Markdown")
        self.assertEqual(inventory_rows[1]["review_order"], "10")
        self.assertEqual(len(inventory_rows[0]["sha256_short"]), 12)
        inventory_json = build_pilot_bundle_inventory_json_export(items)
        inventory_payload = json.loads(inventory_json.content)
        self.assertEqual(inventory_json.filename, "pilot-bundle-inventory.json")
        self.assertEqual(inventory_json.media_type, "application/json")
        self.assertEqual(inventory_payload, inventory_json.payload)
        self.assertEqual(inventory_payload["schema_version"], 2)
        self.assertEqual(inventory_payload["bundle_type"], "pilot_evidence")
        self.assertEqual(inventory_payload["expected_file_count"], 15)
        self.assertEqual(inventory_payload["automation_file_count"], 8)
        self.assertEqual(inventory_payload["human_file_count"], 7)
        self.assertEqual(inventory_payload["files"][0]["path"], "pilot-acceptance-checklist.json")
        self.assertEqual(inventory_payload["files"][0]["kind"], "Automation JSON")
        self.assertEqual(inventory_payload["files"][0]["review_order"], 11)
        acceptance_json = build_pilot_acceptance_json_export(view)
        acceptance_payload = json.loads(acceptance_json.content)
        self.assertEqual(acceptance_json.filename, "pilot-acceptance-checklist.json")
        self.assertEqual(acceptance_json.media_type, "application/json")
        self.assertEqual(acceptance_payload, acceptance_json.payload)
        self.assertEqual(acceptance_payload["schema_version"], 1)
        self.assertEqual(acceptance_payload["acceptance_type"], "pilot")
        self.assertEqual(acceptance_payload["item_count"], 11)
        self.assertEqual(acceptance_payload["items"][0]["status"], "pending")
        delivery_receipt = build_pilot_delivery_receipt_export(items)
        self.assertEqual(delivery_receipt.filename, "pilot-delivery-receipt.md")
        self.assertEqual(delivery_receipt.media_type, "text/markdown; charset=utf-8")
        self.assertIn("# Pilot Delivery Receipt", delivery_receipt.content)
        self.assertIn("- Readiness status: `warning`", delivery_receipt.content)
        self.assertIn("pilot-acceptance-checklist.json", delivery_receipt.content)
        self.assertIn("pilot-delivery-receipt.json", delivery_receipt.content)
        self.assertIn("Client representative:", delivery_receipt.content)
        self.assertIn("Remaining attention items reviewed", delivery_receipt.content)
        delivery_json = build_pilot_delivery_receipt_json_export(items)
        delivery_payload = json.loads(delivery_json.content)
        self.assertEqual(delivery_json.filename, "pilot-delivery-receipt.json")
        self.assertEqual(delivery_json.media_type, "application/json")
        self.assertEqual(delivery_payload, delivery_json.payload)
        self.assertEqual(delivery_payload["schema_version"], 1)
        self.assertEqual(delivery_payload["delivery_type"], "pilot")
        self.assertEqual(delivery_payload["readiness"]["status"], "warning")
        self.assertEqual(delivery_payload["attention_items"], 1)
        self.assertIn("pilot-attention.json", delivery_payload["delivered_files"])
        self.assertIn("pilot-acceptance-checklist.json", delivery_payload["delivered_files"])
        self.assertIn("pilot-bundle-index.json", delivery_payload["delivered_files"])
        self.assertIn("pilot-bundle-inventory.json", delivery_payload["delivered_files"])
        self.assertIn("pilot-runbook.json", delivery_payload["delivered_files"])
        self.assertIn("client_representative", delivery_payload["sign_off_fields"])
        readiness_json = build_pilot_readiness_json_export(items)
        readiness_payload = json.loads(readiness_json.content)
        self.assertEqual(readiness_json.filename, "pilot-readiness.json")
        self.assertEqual(readiness_json.media_type, "application/json")
        self.assertEqual(readiness_payload["schema_version"], 1)
        self.assertEqual(readiness_payload["rollup"]["status"], "warning")
        self.assertEqual(readiness_payload["rollup"]["attention_items"], 1)
        self.assertEqual(readiness_payload["items"][0]["label"], "Web authentication")
        runbook_json = build_pilot_runbook_json_export(view)
        runbook_payload = json.loads(runbook_json.content)
        self.assertEqual(runbook_json.filename, "pilot-runbook.json")
        self.assertEqual(runbook_json.media_type, "application/json")
        self.assertEqual(runbook_payload, runbook_json.payload)
        self.assertEqual(runbook_payload["schema_version"], 1)
        self.assertEqual(runbook_payload["runbook_type"], "pilot")
        self.assertEqual(runbook_payload["sections"][0]["title"], "Setup")
        self.assertEqual(runbook_payload["readiness"]["status"], "warning")

        markdown = format_pilot_readiness_markdown(items)
        self.assertIn("# Pilot Readiness Summary", markdown)
        self.assertIn("- Ready: `6`", markdown)
        self.assertIn("- Warning: `1`", markdown)
        self.assertIn("| Web authentication | ready |", markdown)
        self.assertIn("| Workspace backup | warning | No workspace backup package found. |", markdown)

    def test_web_pilot_route_is_local_runbook_only(self) -> None:
        web_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web.py"
        )
        web = web_path.read_text(encoding="utf-8")

        self.assertIn('@app.get("/pilot"', web)
        self.assertIn("def pilot_runbook(", web)
        self.assertIn('"pilot.html"', web)
        self.assertIn("build_pilot_readiness_items(", web)
        self.assertIn("build_pilot_runbook_view(", web)
        self.assertIn('@app.get("/pilot/runbook.md"', web)
        self.assertIn("def pilot_runbook_markdown(", web)
        self.assertIn("format_pilot_runbook_markdown()", web)
        self.assertIn('filename="pilot-runbook.md"', web)
        self.assertIn('@app.get("/pilot/runbook.json"', web)
        self.assertIn("def pilot_runbook_json(", web)
        self.assertIn("build_pilot_runbook_json_export()", web)
        self.assertIn('@app.get("/pilot/handoff-summary.md"', web)
        self.assertIn("def pilot_handoff_summary_markdown(", web)
        self.assertIn("build_pilot_handoff_summary_export(readiness_items)", web)
        self.assertIn('@app.get("/pilot/handoff-summary.json"', web)
        self.assertIn("def pilot_handoff_summary_json(", web)
        self.assertIn("build_pilot_handoff_summary_json_export(readiness_items)", web)
        self.assertIn('@app.get("/pilot/bundle-index.md"', web)
        self.assertIn("def pilot_bundle_index_markdown(", web)
        self.assertIn("build_pilot_bundle_index_export(readiness_items)", web)
        self.assertIn('@app.get("/pilot/bundle-index.json"', web)
        self.assertIn("def pilot_bundle_index_json(", web)
        self.assertIn("build_pilot_bundle_index_json_export(readiness_items)", web)
        self.assertIn('@app.get("/pilot/bundle-inventory.csv"', web)
        self.assertIn("def pilot_bundle_inventory_csv(", web)
        self.assertIn("build_pilot_bundle_inventory_csv_export(readiness_items)", web)
        self.assertIn('@app.get("/pilot/bundle-inventory.json"', web)
        self.assertIn("def pilot_bundle_inventory_json(", web)
        self.assertIn("build_pilot_bundle_inventory_json_export(readiness_items)", web)
        self.assertIn('@app.get("/pilot/delivery-receipt.md"', web)
        self.assertIn("def pilot_delivery_receipt_markdown(", web)
        self.assertIn("build_pilot_delivery_receipt_export(readiness_items)", web)
        self.assertIn('@app.get("/pilot/delivery-receipt.json"', web)
        self.assertIn("def pilot_delivery_receipt_json(", web)
        self.assertIn("build_pilot_delivery_receipt_json_export(readiness_items)", web)
        self.assertIn('@app.get("/pilot/acceptance.md"', web)
        self.assertIn("def pilot_acceptance_markdown(", web)
        self.assertIn("format_pilot_acceptance_markdown()", web)
        self.assertIn('filename="pilot-acceptance-checklist.md"', web)
        self.assertIn('@app.get("/pilot/acceptance.json"', web)
        self.assertIn("def pilot_acceptance_json(", web)
        self.assertIn("build_pilot_acceptance_json_export()", web)
        self.assertIn('@app.get("/pilot/readiness.md"', web)
        self.assertIn("def pilot_readiness_markdown(", web)
        self.assertIn("format_pilot_readiness_markdown(readiness_items)", web)
        self.assertIn('filename="pilot-readiness.md"', web)
        self.assertIn('@app.get("/pilot/readiness.json"', web)
        self.assertIn("def pilot_readiness_json(", web)
        self.assertIn("build_pilot_readiness_json_export(readiness_items)", web)
        self.assertIn('@app.get("/pilot/attention.md"', web)
        self.assertIn("def pilot_attention_markdown(", web)
        self.assertIn("build_pilot_attention_export(readiness_items)", web)
        self.assertIn('@app.get("/pilot/attention.json"', web)
        self.assertIn("def pilot_attention_json(", web)
        self.assertIn("build_pilot_attention_json_export(readiness_items)", web)
        self.assertIn("export.filename", web)
        self.assertIn('@app.get("/pilot/bundle.zip"', web)
        self.assertIn("def pilot_evidence_bundle(", web)
        self.assertIn("build_pilot_evidence_bundle(readiness_items)", web)
        self.assertIn("bundle.filename", web)
        self.assertIn('@app.get("/pilot/bundle-manifest.json"', web)
        self.assertIn("def pilot_evidence_manifest(", web)
        self.assertIn("build_pilot_evidence_manifest(readiness_items)", web)
        self.assertIn("manifest.filename", web)
        self.assertIn('@app.get("/pilot/bundle-verification.md"', web)
        self.assertIn("def pilot_evidence_verification(", web)
        self.assertIn("build_pilot_evidence_verification(readiness_items)", web)
        self.assertIn("verification.filename", web)
        self.assertIn('@app.get("/pilot/bundle-verification.json"', web)
        self.assertIn("def pilot_evidence_verification_json(", web)
        self.assertIn("build_pilot_evidence_verification_json(readiness_items)", web)

    def test_pilot_runbook_export_is_deterministic_markdown(self) -> None:
        markdown = format_pilot_runbook_markdown()

        self.assertTrue(markdown.startswith("# Pilot Runbook\n"))
        self.assertIn("- Context: `Client Pilot`", markdown)
        self.assertIn("- Scans: `Guarded`", markdown)
        self.assertIn("[System](/system)", markdown)
        self.assertIn("[Backup](/system#system-backup)", markdown)
        self.assertTrue(markdown.endswith("\n"))

    def test_pilot_acceptance_export_is_deterministic_markdown(self) -> None:
        markdown = format_pilot_acceptance_markdown()

        self.assertTrue(markdown.startswith("# Pilot Acceptance Checklist\n"))
        self.assertIn("- Context: `Client Pilot`", markdown)
        self.assertIn("- Source: `Pilot Runbook`", markdown)
        self.assertIn("- [ ] **Setup: Appliance status reviewed**", markdown)
        self.assertIn("- [ ] **Mission: Authorization details completed**", markdown)
        self.assertIn("- [ ] **Handoff: Export inventory verified**", markdown)
        self.assertIn("- [ ] **Closeout: Workspace backup created**", markdown)
        self.assertIn("Evidence: System status page checked before client use.", markdown)
        self.assertTrue(markdown.endswith("\n"))

    def test_pilot_readiness_export_handles_empty_items(self) -> None:
        markdown = format_pilot_readiness_markdown([])

        self.assertTrue(markdown.startswith("# Pilot Readiness Summary\n"))
        self.assertIn("- Ready: `0`", markdown)
        self.assertIn("- Warning: `0`", markdown)
        self.assertIn("- Blocked: `0`", markdown)
        self.assertIn("| None | warning | No readiness item was generated. | - |", markdown)
        self.assertTrue(markdown.endswith("\n"))
        attention_export = build_pilot_attention_export([])
        self.assertIn("- Open items: `0`", attention_export.content)
        self.assertIn(
            "| None | ready | No attention item is currently open. | - |",
            attention_export.content,
        )
        self.assertTrue(attention_export.content.endswith("\n"))

    def test_pilot_evidence_bundle_contains_manifest_and_markdown(self) -> None:
        readiness_items = [
            PilotReadinessItem(
                label="Web authentication",
                status="ready",
                detail="Authentication enabled.",
                href="/system#system-auth",
            )
        ]

        bundle = build_pilot_evidence_bundle(readiness_items)

        self.assertEqual(bundle.filename, "pilot-evidence-bundle.zip")
        self.assertEqual(bundle.media_type, "application/zip")
        with ZipFile(BytesIO(bundle.content)) as archive:
            self.assertEqual(
                sorted(archive.namelist()),
                [
                    "manifest.json",
                    "pilot-acceptance-checklist.json",
                    "pilot-acceptance-checklist.md",
                    "pilot-attention.json",
                    "pilot-attention.md",
                    "pilot-bundle-index.json",
                    "pilot-bundle-index.md",
                    "pilot-bundle-inventory.json",
                    "pilot-delivery-receipt.json",
                    "pilot-delivery-receipt.md",
                    "pilot-handoff-summary.json",
                    "pilot-handoff-summary.md",
                    "pilot-readiness.json",
                    "pilot-readiness.md",
                    "pilot-runbook.json",
                    "pilot-runbook.md",
                ],
            )
            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
            public_manifest = build_pilot_evidence_manifest(readiness_items)
            self.assertEqual(manifest, public_manifest.payload)
            self.assertEqual(json.loads(public_manifest.content), public_manifest.payload)
            self.assertEqual(public_manifest.filename, "pilot-evidence-manifest.json")
            self.assertEqual(public_manifest.media_type, "application/json")
            verification = build_pilot_evidence_verification(readiness_items)
            self.assertEqual(verification.filename, "pilot-evidence-verification.md")
            self.assertEqual(verification.media_type, "text/markdown; charset=utf-8")
            self.assertIn("# Pilot Evidence Bundle Verification", verification.content)
            self.assertIn("- Schema version: `4`", verification.content)
            self.assertIn("- Readiness status: `ready`", verification.content)
            self.assertIn("- File count: `15`", verification.content)
            self.assertIn("- Automation files: `8`", verification.content)
            self.assertIn("- Human-readable files: `7`", verification.content)
            self.assertIn("## Review Order", verification.content)
            self.assertIn("1. `pilot-handoff-summary.md`", verification.content)
            self.assertIn("2. `pilot-handoff-summary.json`", verification.content)
            self.assertIn("4. `pilot-bundle-index.json`", verification.content)
            self.assertIn("5. `pilot-bundle-inventory.json`", verification.content)
            self.assertIn("7. `pilot-attention.json`", verification.content)
            self.assertIn("11. `pilot-acceptance-checklist.json`", verification.content)
            self.assertIn("13. `pilot-runbook.json`", verification.content)
            self.assertIn("15. `pilot-delivery-receipt.json`", verification.content)
            self.assertIn("16. `manifest.json`", verification.content)
            self.assertIn("pilot-bundle-index.md", verification.content)
            self.assertIn("pilot-delivery-receipt.md", verification.content)
            self.assertIn("pilot-readiness.md", verification.content)
            self.assertIn("Compare each extracted file hash", verification.content)
            verification_json = build_pilot_evidence_verification_json(readiness_items)
            verification_payload = json.loads(verification_json.content)
            self.assertEqual(
                verification_json.filename,
                "pilot-evidence-verification.json",
            )
            self.assertEqual(verification_json.media_type, "application/json")
            self.assertEqual(verification_payload, verification_json.payload)
            self.assertEqual(verification_payload["schema_version"], 1)
            self.assertEqual(verification_payload["verification_type"], "pilot_evidence")
            self.assertEqual(verification_payload["manifest_schema_version"], 4)
            self.assertEqual(verification_payload["file_count"], 15)
            self.assertEqual(verification_payload["automation_file_count"], 8)
            self.assertEqual(verification_payload["human_file_count"], 7)
            self.assertIn("pilot-runbook.json", verification_payload["automation_files"])
            self.assertIn("pilot-runbook.md", verification_payload["human_files"])
            self.assertEqual(verification_payload["readiness"]["status"], "ready")
            self.assertEqual(verification_payload["review_order"][0], "pilot-handoff-summary.md")
            self.assertEqual(verification_payload["review_order"][1], "pilot-handoff-summary.json")
            self.assertEqual(
                verification_payload["review_order"][3],
                "pilot-bundle-index.json",
            )
            self.assertEqual(
                verification_payload["review_order"][4],
                "pilot-bundle-inventory.json",
            )
            self.assertEqual(
                verification_payload["review_order"][6],
                "pilot-attention.json",
            )
            self.assertEqual(
                verification_payload["review_order"][10],
                "pilot-acceptance-checklist.json",
            )
            self.assertEqual(
                verification_payload["review_order"][12],
                "pilot-runbook.json",
            )
            self.assertEqual(
                verification_payload["review_order"][14],
                "pilot-delivery-receipt.json",
            )
            self.assertEqual(verification_payload["checks"][0]["id"], "download_bundle")
            self.assertEqual(verification_payload["checks"][0]["status"], "manual")
            self.assertEqual(
                verification_payload["files"][0]["path"],
                "pilot-acceptance-checklist.json",
            )
            self.assertEqual(manifest["schema_version"], 4)
            self.assertEqual(manifest["automation_file_count"], 8)
            self.assertEqual(manifest["human_file_count"], 7)
            self.assertEqual(
                manifest["automation_files"],
                [
                    "pilot-acceptance-checklist.json",
                    "pilot-attention.json",
                    "pilot-bundle-index.json",
                    "pilot-bundle-inventory.json",
                    "pilot-delivery-receipt.json",
                    "pilot-handoff-summary.json",
                    "pilot-readiness.json",
                    "pilot-runbook.json",
                ],
            )
            self.assertEqual(
                manifest["human_files"],
                [
                    "pilot-acceptance-checklist.md",
                    "pilot-attention.md",
                    "pilot-bundle-index.md",
                    "pilot-delivery-receipt.md",
                    "pilot-handoff-summary.md",
                    "pilot-readiness.md",
                    "pilot-runbook.md",
                ],
            )
            self.assertEqual(manifest["bundle_type"], "pilot_evidence")
            self.assertEqual(manifest["context"], "Client Pilot")
            self.assertEqual(manifest["file_count"], 15)
            self.assertEqual(manifest["source"], "Pilot Runbook")
            self.assertEqual(
                manifest["review_order"],
                [
                    "pilot-handoff-summary.md",
                    "pilot-handoff-summary.json",
                    "pilot-bundle-index.md",
                    "pilot-bundle-index.json",
                    "pilot-bundle-inventory.json",
                    "pilot-attention.md",
                    "pilot-attention.json",
                    "pilot-readiness.md",
                    "pilot-readiness.json",
                    "pilot-acceptance-checklist.md",
                    "pilot-acceptance-checklist.json",
                    "pilot-runbook.md",
                    "pilot-runbook.json",
                    "pilot-delivery-receipt.md",
                    "pilot-delivery-receipt.json",
                    "manifest.json",
                ],
            )
            self.assertEqual(
                manifest["readiness"],
                {
                    "attention_items": 0,
                    "blocked": 0,
                    "detail": "1 ready, 0 warning, 0 blocked.",
                    "ready": 1,
                    "status": "ready",
                    "total": 1,
                    "warning": 0,
                },
            )
            self.assertEqual(
                [item["path"] for item in manifest["files"]],
                [
                    "pilot-acceptance-checklist.json",
                    "pilot-acceptance-checklist.md",
                    "pilot-attention.json",
                    "pilot-attention.md",
                    "pilot-bundle-index.json",
                    "pilot-bundle-index.md",
                    "pilot-bundle-inventory.json",
                    "pilot-delivery-receipt.json",
                    "pilot-delivery-receipt.md",
                    "pilot-handoff-summary.json",
                    "pilot-handoff-summary.md",
                    "pilot-readiness.json",
                    "pilot-readiness.md",
                    "pilot-runbook.json",
                    "pilot-runbook.md",
                ],
            )
            for item in manifest["files"]:
                content = archive.read(item["path"])
                self.assertEqual(item["size_bytes"], len(content))
                self.assertEqual(item["sha256"], sha256(content).hexdigest())
            self.assertIn(
                "# Pilot Acceptance Checklist",
                archive.read("pilot-acceptance-checklist.md").decode("utf-8"),
            )
            archived_acceptance = json.loads(
                archive.read("pilot-acceptance-checklist.json").decode("utf-8")
            )
            self.assertEqual(archived_acceptance["acceptance_type"], "pilot")
            self.assertEqual(archived_acceptance["item_count"], 11)
            self.assertIn(
                "# Pilot Attention Items",
                archive.read("pilot-attention.md").decode("utf-8"),
            )
            archived_attention = json.loads(
                archive.read("pilot-attention.json").decode("utf-8")
            )
            self.assertEqual(archived_attention["attention_type"], "pilot")
            self.assertEqual(archived_attention["open_item_count"], 0)
            self.assertIn(
                "# Pilot Evidence Bundle Index",
                archive.read("pilot-bundle-index.md").decode("utf-8"),
            )
            archived_index = json.loads(
                archive.read("pilot-bundle-index.json").decode("utf-8")
            )
            self.assertEqual(archived_index["index_type"], "pilot_evidence")
            self.assertEqual(archived_index["bundle_file_count"], 15)
            archived_inventory = json.loads(
                archive.read("pilot-bundle-inventory.json").decode("utf-8")
            )
            self.assertEqual(archived_inventory["bundle_type"], "pilot_evidence")
            self.assertEqual(archived_inventory["expected_file_count"], 15)
            self.assertEqual(archived_inventory["schema_version"], 2)
            self.assertEqual(archived_inventory["automation_file_count"], 8)
            self.assertEqual(archived_inventory["human_file_count"], 7)
            self.assertEqual(
                archived_inventory["files"][0]["kind"],
                "Automation JSON",
            )
            self.assertIn(
                "# Pilot Delivery Receipt",
                archive.read("pilot-delivery-receipt.md").decode("utf-8"),
            )
            archived_delivery = json.loads(
                archive.read("pilot-delivery-receipt.json").decode("utf-8")
            )
            self.assertEqual(archived_delivery["delivery_type"], "pilot")
            self.assertEqual(archived_delivery["readiness"]["status"], "ready")
            self.assertIn(
                "# Pilot Handoff Summary",
                archive.read("pilot-handoff-summary.md").decode("utf-8"),
            )
            archived_handoff = json.loads(
                archive.read("pilot-handoff-summary.json").decode("utf-8")
            )
            self.assertEqual(archived_handoff["handoff_type"], "pilot")
            self.assertEqual(archived_handoff["readiness"]["status"], "ready")
            archived_readiness = json.loads(
                archive.read("pilot-readiness.json").decode("utf-8")
            )
            self.assertEqual(archived_readiness["rollup"]["status"], "ready")
            self.assertEqual(archived_readiness["items"][0]["status"], "ready")
            self.assertIn(
                "# Pilot Readiness Summary",
                archive.read("pilot-readiness.md").decode("utf-8"),
            )
            self.assertIn(
                "# Pilot Runbook",
                archive.read("pilot-runbook.md").decode("utf-8"),
            )
            archived_runbook = json.loads(
                archive.read("pilot-runbook.json").decode("utf-8")
            )
            self.assertEqual(archived_runbook["runbook_type"], "pilot")
            self.assertEqual(archived_runbook["sections"][0]["title"], "Setup")

    def test_mission_template_exposes_shortcut_anchors(self) -> None:
        template_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_templates"
            / "mission.html"
        )
        template = template_path.read_text(encoding="utf-8")

        for anchor in [
            "mission-readiness",
            "scan-plan",
            "run-monitor",
            "check-selection",
            "mission-setup",
            "reports",
            "activity",
            "scope",
            "counter-test",
            "findings",
        ]:
            self.assertIn(f'href="#{anchor}"', template)
            self.assertIn(f'id="{anchor}"', template)

        for counter in [
            "view.readiness_items|length",
            "view.scan_plans|length",
            "view.scan_runs|length",
            "view.check_selection|length",
            "view.reports|length",
            "view.activity_events|length",
            "view.scope|length",
            "view.counter_test_items|length",
            "view.findings|length",
        ]:
            self.assertIn(f"{{{{ {counter} }}}}", template)

        self.assertIn("view.counter_test_summary", template)
        self.assertIn('aria-label="Counter-test summary"', template)
        self.assertIn('href="/clients/{{ view.mission.client_id }}"', template)
        self.assertIn('href="{{ view.activity_log_url }}"', template)
        self.assertIn('/missions/{{ view.mission.id }}/readiness/markdown', template)
        self.assertIn('/missions/{{ view.mission.id }}/readiness/json', template)
        self.assertIn('aria-label="Mission readiness exports"', template)
        self.assertIn('/missions/{{ view.mission.id }}/scan-plan/markdown', template)
        self.assertIn('/missions/{{ view.mission.id }}/scan-plan/json', template)
        self.assertIn('aria-label="Scan plan exports"', template)
        self.assertIn('aria-label="Mission export integrity details"', template)
        self.assertIn("view.mission_export.checked_files", template)
        self.assertIn("view.mission_export.missing_count", template)
        self.assertIn("view.mission_export.mismatched_count", template)
        self.assertIn("view.mission_export.unexpected_count", template)
        self.assertIn("view.mission_export.has_integrity_issues", template)
        self.assertIn('aria-label="Mission export package"', template)
        self.assertIn('/missions/{{ view.mission.id }}/export-manifest/markdown', template)
        self.assertIn('/missions/{{ view.mission.id }}/export-manifest/json', template)
        self.assertIn('/missions/{{ view.mission.id }}/export-verification/markdown', template)
        self.assertIn('/missions/{{ view.mission.id }}/export-verification/json', template)
        self.assertIn(
            "Required for false positive, accepted risk, or counter-test status.",
            template,
        )
        self.assertIn("counter-test-form", template)
        self.assertIn('name="status" value="counter_test_failed"', template)
        self.assertIn('name="status" value="counter_test_passed"', template)
        self.assertIn('name="review_note" value="{{ item.review_note }}" required', template)

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
        dispositions = {item.status: item.count for item in view.finding_dispositions}
        self.assertEqual(dispositions["new"], 1)
        self.assertEqual(dispositions["confirmed"], 0)
        self.assertEqual(dispositions["accepted_risk"], 0)
        self.assertEqual(view.clients[0].mission_count, 1)
        self.assertEqual(view.clients[0].preparation_priority, "warning")
        self.assertEqual(view.clients[0].next_action, "Review 1 new finding(s).")
        self.assertEqual(view.clients[0].next_action_label, "Review Findings")
        self.assertEqual(
            view.clients[0].next_action_href,
            f"/missions/{mission.id}#findings",
        )
        self.assertEqual(view.clients[0].export_inventory_url, f"/exports?client_id={client.id}")
        self.assertEqual(view.clients[0].next_action_mission_id, mission.id)
        self.assertEqual(view.clients[0].next_action_mission_name, "External Audit")
        self.assertEqual(view.clients[0].blocked_preparation_count, 0)
        self.assertEqual(view.clients[0].warning_preparation_count, 1)
        self.assertEqual(view.clients[0].ready_preparation_count, 0)
        self.assertEqual(view.clients[0].new_finding_count, 1)
        self.assertEqual(view.clients[0].accepted_risk_count, 0)
        self.assertEqual(view.clients[0].false_positive_count, 0)
        self.assertEqual(view.clients[0].active_finding_count, 1)
        self.assertEqual(view.clients[0].high_or_critical_finding_count, 0)
        self.assertEqual(view.clients[0].risk_score, 10)
        self.assertEqual(view.clients[0].risk_level, "low")
        self.assertEqual(view.missions[0].client_name, "Client X")
        self.assertEqual(view.missions[0].approved_scope_count, 1)
        self.assertEqual(view.missions[0].audit_template_title, "")
        self.assertEqual(view.missions[0].new_finding_count, 1)
        self.assertEqual(view.missions[0].accepted_risk_count, 0)
        self.assertEqual(view.missions[0].false_positive_count, 0)
        self.assertEqual(view.missions[0].counter_test_ready_count, 0)
        self.assertEqual(view.missions[0].counter_test_passed_count, 0)
        self.assertEqual(view.missions[0].counter_test_failed_count, 0)
        self.assertEqual(view.missions[0].preparation_status, "warning")
        self.assertEqual(view.missions[0].preparation_next_action, "Review 1 new finding(s).")
        self.assertEqual(view.missions[0].preparation_action_label, "Review Findings")
        self.assertEqual(
            view.missions[0].preparation_action_href,
            f"/missions/{mission.id}#findings",
        )
        self.assertEqual(view.blocked_preparation_count, 0)
        self.assertEqual(view.warning_preparation_count, 1)
        self.assertEqual(view.ready_preparation_count, 0)
        priority_counts = {
            item.status: item.count for item in view.client_priority_items
        }
        self.assertEqual(priority_counts["blocked"], 0)
        self.assertEqual(priority_counts["warning"], 1)
        self.assertEqual(priority_counts["ready"], 0)
        self.assertEqual(priority_counts["none"], 0)
        risk_counts = {item.level: item.count for item in view.client_risk_items}
        self.assertEqual(risk_counts["critical"], 0)
        self.assertEqual(risk_counts["high"], 0)
        self.assertEqual(risk_counts["medium"], 0)
        self.assertEqual(risk_counts["low"], 1)
        self.assertEqual(risk_counts["none"], 0)
        self.assertEqual(view.preparation_items[0].client_name, "Client X")
        self.assertEqual(view.preparation_items[0].status, "warning")
        self.assertEqual(
            view.preparation_items[0].next_action,
            "Review 1 new finding(s).",
        )
        self.assertEqual(view.preparation_items[0].next_action_label, "Review Findings")
        self.assertEqual(
            view.preparation_items[0].next_action_href,
            f"/missions/{mission.id}#findings",
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
        priority_counts = {item.status: item for item in view.client_priority_items}
        self.assertEqual(priority_counts["blocked"].label, "Blocked")
        self.assertEqual(priority_counts["blocked"].count, 1)
        self.assertEqual(priority_counts["warning"].count, 0)
        self.assertEqual(priority_counts["ready"].count, 1)
        self.assertEqual(priority_counts["none"].label, "No mission")
        self.assertEqual(priority_counts["none"].count, 1)
        risk_counts = {item.level: item for item in view.client_risk_items}
        self.assertEqual(risk_counts["critical"].count, 0)
        self.assertEqual(risk_counts["high"].count, 0)
        self.assertEqual(risk_counts["medium"].count, 0)
        self.assertEqual(risk_counts["low"].label, "Low")
        self.assertEqual(risk_counts["low"].count, 1)
        self.assertEqual(risk_counts["none"].count, 2)
        self.assertEqual(
            [item.status for item in view.preparation_items],
            ["blocked", "warning", "ready"],
        )
        self.assertEqual(
            [item.mission_id for item in view.ready_missions],
            [ready_mission.id],
        )
        self.assertEqual(view.ready_missions[0].client_name, "Client A")
        mission_rows = {mission.name: mission for mission in view.missions}
        self.assertEqual(mission_rows["Ready Audit"].preparation_action_label, "Open Reports")
        self.assertEqual(
            mission_rows["Ready Audit"].preparation_action_href,
            f"/missions/{ready_mission.id}#reports",
        )
        self.assertEqual(mission_rows["Blocked Audit"].preparation_action_label, "Open Setup")
        self.assertEqual(
            mission_rows["Blocked Audit"].preparation_action_href,
            f"/missions/{blocked_mission.id}#mission-setup",
        )
        self.assertEqual(view.ready_missions[0].next_action_label, "Open Reports")
        self.assertEqual(
            view.ready_missions[0].next_action_href,
            f"/missions/{ready_mission.id}#reports",
        )
        self.assertEqual(
            [item.mission_id for item in view.review_missions],
            [warning_mission.id],
        )
        self.assertEqual(
            view.review_missions[0].next_action,
            "Review 1 new finding(s).",
        )
        self.assertEqual(
            [item.mission_id for item in view.blocked_missions],
            [blocked_mission.id],
        )
        self.assertEqual(
            view.blocked_missions[0].next_action,
            "Add written authorization reference.",
        )
        self.assertEqual(view.blocked_missions[0].next_action_label, "Open Setup")
        self.assertEqual(
            view.blocked_missions[0].next_action_href,
            f"/missions/{blocked_mission.id}#mission-setup",
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
        self.assertEqual(client_rows["Client C"].next_action_label, "Create Mission")
        self.assertEqual(client_rows["Client C"].next_action_href, "#new-mission")
        self.assertEqual(client_rows["Client C"].next_action_mission_id, "")
        self.assertEqual([client.name for client in view.no_mission_clients], ["Client C"])
        self.assertEqual(
            view.no_mission_clients[0].next_action,
            "Create first mission for this client.",
        )
        self.assertEqual([client.name for client in view.blocked_clients], ["Client B"])
        self.assertEqual(view.blocked_clients[0].next_action_mission_id, blocked_mission.id)

    def test_dashboard_action_links_target_preparation_sections(self) -> None:
        store = JsonStore(clean_data_dir("web-ui-dashboard-action-links"))
        client = store.create_client(Client(name="Client Action Links"))
        scope_mission = store.create_mission(
            Mission(
                client_id=client.id,
                name="Needs Scope",
                authorization_reference="AUTH-SCOPE",
            )
        )
        checks_mission = store.create_mission(
            Mission(
                client_id=client.id,
                name="Needs Checks",
                authorization_reference="AUTH-CHECKS",
                selected_checks=[],
            )
        )
        store.add_scope_item(
            checks_mission.id,
            ScopeItem(type=ScopeType.IP, value="192.0.2.55", approved=True),
        )

        view = build_dashboard_view(store)
        items = {item.mission_name: item for item in view.preparation_items}

        self.assertEqual(
            items["Needs Scope"].next_action,
            "Approve at least one scope target.",
        )
        self.assertEqual(items["Needs Scope"].next_action_label, "Review Scope")
        self.assertEqual(
            items["Needs Scope"].next_action_href,
            f"/missions/{scope_mission.id}#scope",
        )
        self.assertEqual(
            items["Needs Checks"].next_action,
            "Select audit checks for planning.",
        )
        self.assertEqual(items["Needs Checks"].next_action_label, "Select Checks")
        self.assertEqual(
            items["Needs Checks"].next_action_href,
            f"/missions/{checks_mission.id}#check-selection",
        )

    def test_failed_counter_tests_drive_next_action_links(self) -> None:
        store = JsonStore(clean_data_dir("web-ui-counter-test-next-actions"))
        client = store.create_client(Client(name="Client Retest"))
        mission = store.create_mission(
            Mission(
                client_id=client.id,
                name="Retest Audit",
                authorization_reference="AUTH-RETEST",
            )
        )
        store.add_scope_item(
            mission.id,
            ScopeItem(type=ScopeType.DOMAIN, value="client.example", approved=True),
        )
        store.add_finding(
            mission.id,
            Finding(
                title="Failed retest",
                severity=Severity.MEDIUM,
                affected_asset="client.example",
                category="manual",
                source_module="manual",
                proof="Counter-test still shows the issue.",
                risk="Risk remains after remediation.",
                remediation="Continue remediation.",
                counter_test="Repeat the check after correction.",
                confidence=0.8,
                status=FindingStatus.COUNTER_TEST_FAILED,
                metadata={"review_note": "Still visible."},
            ),
        )
        store.add_finding(
            mission.id,
            Finding(
                title="New related finding",
                severity=Severity.LOW,
                affected_asset="client.example",
                category="manual",
                source_module="manual",
                proof="New evidence still needs review.",
                risk="Risk needs review.",
                remediation="Apply correction.",
                counter_test="Repeat the check.",
                confidence=0.8,
            ),
        )

        dashboard = build_dashboard_view(store)
        client_view = build_client_view(store, client.id)

        self.assertEqual(dashboard.missions[0].preparation_status, "warning")
        self.assertEqual(
            dashboard.missions[0].preparation_next_action,
            "Review 1 failed counter-test(s).",
        )
        self.assertEqual(
            dashboard.missions[0].preparation_action_label,
            "Open Counter-tests",
        )
        self.assertEqual(
            dashboard.missions[0].preparation_action_href,
            f"/missions/{mission.id}#counter-test",
        )
        self.assertEqual(
            dashboard.review_missions[0].next_action,
            "Review 1 failed counter-test(s).",
        )
        self.assertEqual(
            dashboard.review_missions[0].next_action_label,
            "Open Counter-tests",
        )
        self.assertEqual(
            dashboard.review_missions[0].next_action_href,
            f"/missions/{mission.id}#counter-test",
        )
        self.assertEqual(
            dashboard.clients[0].next_action,
            "Review 1 failed counter-test(s).",
        )
        self.assertEqual(dashboard.clients[0].next_action_label, "Open Counter-tests")
        self.assertEqual(
            dashboard.clients[0].next_action_href,
            f"/missions/{mission.id}#counter-test",
        )
        self.assertEqual(
            client_view.preparation_items[0].next_action,
            "Review 1 failed counter-test(s).",
        )
        self.assertEqual(
            client_view.preparation_items[0].next_action_label,
            "Open Counter-tests",
        )
        self.assertEqual(
            client_view.preparation_items[0].next_action_href,
            f"/missions/{mission.id}#counter-test",
        )
        self.assertEqual(
            client_view.missions[0].preparation_action_href,
            f"/missions/{mission.id}#counter-test",
        )

    def test_dashboard_client_rows_include_review_and_risk_counts(self) -> None:
        store = JsonStore(clean_data_dir("web-ui-client-row-review-counts"))
        client_a = store.create_client(Client(name="Client A"))
        client_b = store.create_client(Client(name="Client B"))
        mission_a = store.create_mission(
            Mission(client_id=client_a.id, name="Client A Review Audit")
        )
        mission_b = store.create_mission(
            Mission(client_id=client_b.id, name="Client B Review Audit")
        )
        store.add_finding(
            mission_a.id,
            Finding(
                title="New finding",
                severity=Severity.LOW,
                affected_asset="new.example",
                category="manual",
                source_module="manual",
                proof="Observed manually.",
                risk="Risk needs review.",
                remediation="Apply correction.",
                counter_test="Repeat the check.",
                confidence=0.8,
            ),
        )
        store.add_finding(
            mission_a.id,
            Finding(
                title="Accepted risk",
                severity=Severity.HIGH,
                affected_asset="accepted.example",
                category="manual",
                source_module="manual",
                proof="Observed manually.",
                risk="Risk accepted by owner.",
                remediation="Track exception.",
                counter_test="Confirm exception remains documented.",
                confidence=0.8,
                status=FindingStatus.ACCEPTED_RISK,
                metadata={"review_note": "Accepted by owner."},
            ),
        )
        store.add_finding(
            mission_b.id,
            Finding(
                title="False positive",
                severity=Severity.MEDIUM,
                affected_asset="false-positive.example",
                category="manual",
                source_module="manual",
                proof="Observed manually.",
                risk="No confirmed risk.",
                remediation="No remediation required.",
                counter_test="Repeat manual verification.",
                confidence=0.8,
                status=FindingStatus.FALSE_POSITIVE,
                metadata={"review_note": "Verified as benign."},
            ),
        )

        view = build_dashboard_view(store)
        client_rows = {client.name: client for client in view.clients}

        self.assertEqual(client_rows["Client A"].new_finding_count, 1)
        self.assertEqual(client_rows["Client A"].accepted_risk_count, 1)
        self.assertEqual(client_rows["Client A"].false_positive_count, 0)
        self.assertEqual(client_rows["Client A"].active_finding_count, 2)
        self.assertEqual(client_rows["Client A"].high_or_critical_finding_count, 1)
        self.assertEqual(client_rows["Client A"].risk_score, 28)
        self.assertEqual(client_rows["Client A"].risk_level, "medium")
        self.assertEqual(client_rows["Client B"].new_finding_count, 0)
        self.assertEqual(client_rows["Client B"].accepted_risk_count, 0)
        self.assertEqual(client_rows["Client B"].false_positive_count, 1)
        self.assertEqual(client_rows["Client B"].active_finding_count, 0)
        self.assertEqual(client_rows["Client B"].high_or_critical_finding_count, 0)
        self.assertEqual(client_rows["Client B"].risk_score, 0)
        self.assertEqual(client_rows["Client B"].risk_level, "none")
        self.assertEqual([client.name for client in view.top_risk_clients], ["Client A"])
        self.assertEqual(
            [client.name for client in view.review_backlog_clients],
            ["Client A"],
        )

    def test_dashboard_client_rows_sort_equal_priority_by_risk(self) -> None:
        store = JsonStore(clean_data_dir("web-ui-client-row-risk-ordering"))
        low_client = store.create_client(Client(name="Low Risk Client"))
        high_client = store.create_client(Client(name="High Risk Client"))
        low_mission = store.create_mission(
            Mission(
                client_id=low_client.id,
                name="Low Risk Audit",
                authorization_reference="AUTH-LOW",
            )
        )
        high_mission = store.create_mission(
            Mission(
                client_id=high_client.id,
                name="High Risk Audit",
                authorization_reference="AUTH-HIGH",
            )
        )
        store.add_scope_item(
            low_mission.id,
            ScopeItem(type=ScopeType.DOMAIN, value="low.example", approved=True),
        )
        store.add_scope_item(
            high_mission.id,
            ScopeItem(type=ScopeType.DOMAIN, value="high.example", approved=True),
        )
        store.add_finding(
            low_mission.id,
            Finding(
                title="Low risk finding",
                severity=Severity.LOW,
                affected_asset="low.example",
                category="manual",
                source_module="manual",
                proof="Observed manually.",
                risk="Risk needs review.",
                remediation="Apply correction.",
                counter_test="Repeat the check.",
                confidence=0.8,
            ),
        )
        store.add_finding(
            high_mission.id,
            Finding(
                title="High risk finding",
                severity=Severity.HIGH,
                affected_asset="high.example",
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

        self.assertEqual(
            [client.name for client in view.clients],
            ["High Risk Client", "Low Risk Client"],
        )
        self.assertEqual(view.clients[0].preparation_priority, "warning")
        self.assertEqual(view.clients[0].risk_score, 25)
        self.assertEqual(view.clients[1].risk_score, 3)
        self.assertEqual(
            [client.name for client in view.top_risk_clients],
            ["High Risk Client", "Low Risk Client"],
        )
        self.assertEqual(
            [client.name for client in view.review_backlog_clients],
            ["High Risk Client", "Low Risk Client"],
        )

    def test_dashboard_view_summarizes_workspace_finding_dispositions(self) -> None:
        store = JsonStore(clean_data_dir("web-ui-dashboard-dispositions"))
        client = store.create_client(Client(name="Client Dispositions"))
        mission_a = store.create_mission(
            Mission(client_id=client.id, name="Disposition Audit A")
        )
        mission_b = store.create_mission(
            Mission(client_id=client.id, name="Disposition Audit B")
        )
        store.add_finding(
            mission_a.id,
            Finding(
                title="New finding",
                severity=Severity.LOW,
                affected_asset="new.example",
                category="manual",
                source_module="manual",
                proof="Observed manually.",
                risk="Risk needs review.",
                remediation="Apply correction.",
                counter_test="Repeat the check.",
                confidence=0.8,
            ),
        )
        store.add_finding(
            mission_a.id,
            Finding(
                title="Confirmed finding",
                severity=Severity.MEDIUM,
                affected_asset="confirmed.example",
                category="manual",
                source_module="manual",
                proof="Observed manually.",
                risk="Risk confirmed.",
                remediation="Apply correction.",
                counter_test="Repeat the check.",
                confidence=0.8,
                status=FindingStatus.CONFIRMED,
            ),
        )
        store.add_finding(
            mission_b.id,
            Finding(
                title="Accepted risk",
                severity=Severity.LOW,
                affected_asset="accepted.example",
                category="manual",
                source_module="manual",
                proof="Observed manually.",
                risk="Risk accepted by owner.",
                remediation="Track exception.",
                counter_test="Confirm exception remains documented.",
                confidence=0.8,
                status=FindingStatus.ACCEPTED_RISK,
                metadata={"review_note": "Accepted by owner."},
            ),
        )
        store.add_finding(
            mission_b.id,
            Finding(
                title="Counter-test passed",
                severity=Severity.LOW,
                affected_asset="passed.example",
                category="manual",
                source_module="manual",
                proof="Observed manually.",
                risk="Risk was corrected.",
                remediation="No further action.",
                counter_test="Already passed.",
                confidence=0.8,
                status=FindingStatus.COUNTER_TEST_PASSED,
                metadata={"review_note": "Counter-test passed."},
            ),
        )
        store.add_finding(
            mission_b.id,
            Finding(
                title="Counter-test failed",
                severity=Severity.LOW,
                affected_asset="failed.example",
                category="manual",
                source_module="manual",
                proof="Observed manually.",
                risk="Risk still appears present.",
                remediation="Continue the corrective action.",
                counter_test="Repeat the check.",
                confidence=0.8,
                status=FindingStatus.COUNTER_TEST_FAILED,
                metadata={"review_note": "Counter-test failed."},
            ),
        )

        view = build_dashboard_view(store)
        dispositions = {item.status: item for item in view.finding_dispositions}
        counter_tests = {item.status: item for item in view.counter_test_summary}

        self.assertEqual(dispositions["new"].label, "New")
        self.assertEqual(dispositions["new"].count, 1)
        self.assertEqual(dispositions["confirmed"].count, 1)
        self.assertEqual(dispositions["accepted_risk"].count, 1)
        self.assertEqual(dispositions["false_positive"].count, 0)
        self.assertEqual(counter_tests["ready"].count, 2)
        self.assertEqual(counter_tests["passed"].count, 1)
        self.assertEqual(counter_tests["failed"].count, 1)
        self.assertEqual(len(view.failed_counter_test_missions), 1)
        self.assertEqual(
            view.failed_counter_test_missions[0].name,
            "Disposition Audit B",
        )
        self.assertEqual(view.failed_counter_test_missions[0].counter_test_failed_count, 1)
        self.assertEqual(view.failed_counter_test_missions[0].counter_test_ready_count, 1)

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
        self.assertEqual(view.missions[0].new_finding_count, 1)
        self.assertEqual(view.missions[0].accepted_risk_count, 0)
        self.assertEqual(view.missions[0].false_positive_count, 0)
        dispositions = {item.status: item.count for item in view.finding_dispositions}
        self.assertEqual(dispositions["new"], 1)
        self.assertEqual(dispositions["accepted_risk"], 0)
        self.assertEqual(view.missions[0].preparation_status, "warning")
        self.assertEqual(view.missions[0].preparation_next_action, "Review 1 new finding(s).")
        self.assertEqual(view.activity_log_url, f"/activity?client_id={client_a.id}")
        self.assertEqual(view.export_inventory_url, f"/exports?client_id={client_a.id}")
        self.assertEqual(len(view.recent_activity_events), 1)
        self.assertEqual(view.recent_activity_events[0].mission_name, "Client A Audit")
        self.assertEqual(view.recent_activity_events[0].action, "scope.approved")

    def test_client_view_summarizes_finding_dispositions_by_client(self) -> None:
        store = JsonStore(clean_data_dir("web-ui-client-dispositions"))
        client_a = store.create_client(Client(name="Client A"))
        client_b = store.create_client(Client(name="Client B"))
        mission_a = store.create_mission(
            Mission(client_id=client_a.id, name="Client A Audit")
        )
        mission_b = store.create_mission(
            Mission(client_id=client_b.id, name="Client B Audit")
        )
        store.add_finding(
            mission_a.id,
            Finding(
                title="New finding",
                severity=Severity.LOW,
                affected_asset="new.example",
                category="manual",
                source_module="manual",
                proof="Observed manually.",
                risk="Risk needs review.",
                remediation="Apply correction.",
                counter_test="Repeat the check.",
                confidence=0.8,
            ),
        )
        store.add_finding(
            mission_a.id,
            Finding(
                title="Accepted risk",
                severity=Severity.LOW,
                affected_asset="accepted.example",
                category="manual",
                source_module="manual",
                proof="Observed manually.",
                risk="Risk accepted by owner.",
                remediation="Track exception.",
                counter_test="Confirm exception remains documented.",
                confidence=0.8,
                status=FindingStatus.ACCEPTED_RISK,
                metadata={"review_note": "Accepted by owner."},
            ),
        )
        store.add_finding(
            mission_a.id,
            Finding(
                title="Client A counter-test failed",
                severity=Severity.LOW,
                affected_asset="failed-a.example",
                category="manual",
                source_module="manual",
                proof="Observed manually.",
                risk="Risk still appears present.",
                remediation="Continue remediation.",
                counter_test="Repeat the check.",
                confidence=0.8,
                status=FindingStatus.COUNTER_TEST_FAILED,
                metadata={"review_note": "Still visible."},
            ),
        )
        store.add_finding(
            mission_b.id,
            Finding(
                title="Other client false positive",
                severity=Severity.MEDIUM,
                affected_asset="other.example",
                category="manual",
                source_module="manual",
                proof="Observed manually.",
                risk="No confirmed risk.",
                remediation="No remediation required.",
                counter_test="Repeat manual verification.",
                confidence=0.8,
                status=FindingStatus.FALSE_POSITIVE,
                metadata={"review_note": "Verified as benign."},
            ),
        )
        store.add_finding(
            mission_b.id,
            Finding(
                title="Other client counter-test passed",
                severity=Severity.LOW,
                affected_asset="passed-b.example",
                category="manual",
                source_module="manual",
                proof="Observed manually.",
                risk="Risk was corrected.",
                remediation="No further action.",
                counter_test="Already passed.",
                confidence=0.8,
                status=FindingStatus.COUNTER_TEST_PASSED,
                metadata={"review_note": "Corrected."},
            ),
        )

        view = build_client_view(store, client_a.id)
        dispositions = {item.status: item for item in view.finding_dispositions}
        counter_tests = {item.status: item for item in view.counter_test_summary}

        self.assertEqual(dispositions["new"].label, "New")
        self.assertEqual(dispositions["new"].count, 1)
        self.assertEqual(dispositions["accepted_risk"].count, 1)
        self.assertEqual(dispositions["false_positive"].count, 0)
        self.assertEqual(counter_tests["ready"].count, 1)
        self.assertEqual(counter_tests["passed"].count, 0)
        self.assertEqual(counter_tests["failed"].count, 1)
        self.assertEqual(len(view.failed_counter_test_missions), 1)
        self.assertEqual(
            view.failed_counter_test_missions[0].name,
            "Client A Audit",
        )
        self.assertEqual(view.failed_counter_test_missions[0].counter_test_failed_count, 1)
        self.assertEqual(view.failed_counter_test_missions[0].counter_test_passed_count, 0)

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
        self.assertEqual(blocked.next_action_label, "Open Setup")
        self.assertEqual(
            blocked.next_action_href,
            f"/missions/{blocked.mission_id}#mission-setup",
        )
        warning = view.preparation_items[1]
        self.assertEqual(warning.warning_count, 1)
        self.assertEqual(warning.next_action, "Review 1 new finding(s).")
        self.assertEqual(warning.next_action_label, "Review Findings")
        self.assertEqual(
            warning.next_action_href,
            f"/missions/{warning.mission_id}#findings",
        )
        ready = view.preparation_items[2]
        self.assertEqual(ready.next_action_label, "Open Reports")
        self.assertEqual(
            ready.next_action_href,
            f"/missions/{ready.mission_id}#reports",
        )

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
        self.assertEqual(view.activity_log_url, f"/activity?mission_id={mission.id}")
        self.assertEqual(view.mission.audit_template_id, "tpl_internal_hygiene")
        self.assertEqual(view.mission.audit_template_title, "Internal Network Hygiene")
        self.assertIsNotNone(view.template_guidance)
        self.assertEqual(view.template_guidance.title, "Internal Network Hygiene")
        self.assertEqual(
            view.template_guidance.recommended_checks,
            ["Nmap services", "SMB basic", "LDAP basic"],
        )
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
                metadata={"review_note": "Ready for counter-test."},
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
        store.add_finding(
            mission.id,
            Finding(
                title="Failed finding",
                severity=Severity.LOW,
                affected_asset="legacy.client.example",
                category="manual",
                source_module="manual",
                proof="Observed manually.",
                risk="Risk still appears present.",
                remediation="Continue the corrective action.",
                counter_test="Repeat the manual check after remediation.",
                confidence=0.8,
                status=FindingStatus.COUNTER_TEST_FAILED,
                metadata={"review_note": "Issue still visible."},
            ),
        )

        view = build_mission_view(store, mission.id)

        summary = {item.status: item for item in view.counter_test_summary}
        self.assertEqual(summary["ready"].count, 2)
        self.assertEqual(summary["passed"].count, 1)
        self.assertEqual(summary["failed"].count, 1)
        self.assertEqual(summary["failed"].label, "Failed")
        self.assertIn("needing remediation", summary["failed"].detail)
        self.assertEqual(len(view.counter_test_items), 2)
        self.assertEqual(view.counter_test_items[0].title, "Confirmed finding")
        self.assertEqual(view.counter_test_items[0].status, "confirmed")
        self.assertEqual(view.counter_test_items[0].review_note, "Ready for counter-test.")
        self.assertEqual(view.counter_test_items[1].title, "Failed finding")
        self.assertEqual(view.counter_test_items[1].review_note, "Issue still visible.")
        self.assertEqual(view.findings[0].related_remediations, [])
        self.assertIsNone(view.template_guidance)

    def test_mission_view_summarizes_finding_dispositions(self) -> None:
        store = JsonStore(clean_data_dir("web-ui-finding-dispositions"))
        client = store.create_client(Client(name="Client Dispositions"))
        mission = store.create_mission(
            Mission(client_id=client.id, name="Disposition Audit")
        )
        store.add_finding(
            mission.id,
            Finding(
                title="New finding",
                severity=Severity.LOW,
                affected_asset="new.example",
                category="manual",
                source_module="manual",
                proof="Observed manually.",
                risk="Risk needs review.",
                remediation="Apply correction.",
                counter_test="Repeat the check.",
                confidence=0.8,
            ),
        )
        store.add_finding(
            mission.id,
            Finding(
                title="Accepted risk",
                severity=Severity.LOW,
                affected_asset="accepted.example",
                category="manual",
                source_module="manual",
                proof="Observed manually.",
                risk="Risk accepted by owner.",
                remediation="Track exception.",
                counter_test="Confirm exception remains documented.",
                confidence=0.8,
                status=FindingStatus.ACCEPTED_RISK,
                metadata={"review_note": "Accepted by owner."},
            ),
        )
        store.add_finding(
            mission.id,
            Finding(
                title="False positive",
                severity=Severity.MEDIUM,
                affected_asset="false-positive.example",
                category="manual",
                source_module="manual",
                proof="Observed manually.",
                risk="No confirmed risk.",
                remediation="No remediation required.",
                counter_test="Repeat manual verification.",
                confidence=0.8,
                status=FindingStatus.FALSE_POSITIVE,
                metadata={"review_note": "Verified as benign."},
            ),
        )

        view = build_mission_view(store, mission.id)
        dispositions = {item.status: item for item in view.finding_dispositions}

        self.assertEqual(dispositions["new"].label, "New")
        self.assertEqual(dispositions["new"].count, 1)
        self.assertEqual(dispositions["accepted_risk"].count, 1)
        self.assertEqual(dispositions["false_positive"].count, 1)
        self.assertEqual(dispositions["confirmed"].count, 0)
        self.assertEqual(dispositions["counter_test_failed"].label, "Counter-test failed")

    def test_mission_rows_include_review_status_counts(self) -> None:
        store = JsonStore(clean_data_dir("web-ui-mission-row-review-counts"))
        client = store.create_client(Client(name="Client Review Counts"))
        mission = store.create_mission(
            Mission(client_id=client.id, name="Review Count Audit")
        )
        store.add_finding(
            mission.id,
            Finding(
                title="New finding",
                severity=Severity.LOW,
                affected_asset="new.example",
                category="manual",
                source_module="manual",
                proof="Observed manually.",
                risk="Risk needs review.",
                remediation="Apply correction.",
                counter_test="Repeat the check.",
                confidence=0.8,
            ),
        )
        store.add_finding(
            mission.id,
            Finding(
                title="Accepted risk",
                severity=Severity.LOW,
                affected_asset="accepted.example",
                category="manual",
                source_module="manual",
                proof="Observed manually.",
                risk="Risk accepted by owner.",
                remediation="Track exception.",
                counter_test="Confirm exception remains documented.",
                confidence=0.8,
                status=FindingStatus.ACCEPTED_RISK,
                metadata={"review_note": "Accepted by owner."},
            ),
        )
        store.add_finding(
            mission.id,
            Finding(
                title="False positive",
                severity=Severity.MEDIUM,
                affected_asset="false-positive.example",
                category="manual",
                source_module="manual",
                proof="Observed manually.",
                risk="No confirmed risk.",
                remediation="No remediation required.",
                counter_test="Repeat manual verification.",
                confidence=0.8,
                status=FindingStatus.FALSE_POSITIVE,
                metadata={"review_note": "Verified as benign."},
            ),
        )
        store.add_finding(
            mission.id,
            Finding(
                title="Counter-test passed",
                severity=Severity.LOW,
                affected_asset="passed.example",
                category="manual",
                source_module="manual",
                proof="Observed manually.",
                risk="Risk was corrected.",
                remediation="No further action.",
                counter_test="Already passed.",
                confidence=0.8,
                status=FindingStatus.COUNTER_TEST_PASSED,
                metadata={"review_note": "Corrected."},
            ),
        )
        store.add_finding(
            mission.id,
            Finding(
                title="Counter-test failed",
                severity=Severity.LOW,
                affected_asset="failed.example",
                category="manual",
                source_module="manual",
                proof="Observed manually.",
                risk="Risk still appears present.",
                remediation="Continue remediation.",
                counter_test="Repeat the check.",
                confidence=0.8,
                status=FindingStatus.COUNTER_TEST_FAILED,
                metadata={"review_note": "Still visible."},
            ),
        )

        dashboard = build_dashboard_view(store)
        client_view = build_client_view(store, client.id)

        self.assertEqual(dashboard.missions[0].new_finding_count, 1)
        self.assertEqual(dashboard.missions[0].accepted_risk_count, 1)
        self.assertEqual(dashboard.missions[0].false_positive_count, 1)
        self.assertEqual(dashboard.missions[0].counter_test_ready_count, 1)
        self.assertEqual(dashboard.missions[0].counter_test_passed_count, 1)
        self.assertEqual(dashboard.missions[0].counter_test_failed_count, 1)
        self.assertEqual(client_view.missions[0].new_finding_count, 1)
        self.assertEqual(client_view.missions[0].accepted_risk_count, 1)
        self.assertEqual(client_view.missions[0].false_positive_count, 1)
        self.assertEqual(client_view.missions[0].counter_test_ready_count, 1)
        self.assertEqual(client_view.missions[0].counter_test_passed_count, 1)
        self.assertEqual(client_view.missions[0].counter_test_failed_count, 1)

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
        self.assertGreater(view.mission_export.checked_files, 0)
        self.assertEqual(view.mission_export.missing_count, 0)
        self.assertEqual(view.mission_export.mismatched_count, 0)
        self.assertEqual(view.mission_export.unexpected_count, 0)
        self.assertFalse(view.mission_export.has_integrity_issues)

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
