import csv
import json
import re
import shutil
import unittest
from datetime import date, datetime, timezone
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
    build_pilot_final_handoff_checklist_export,
    build_pilot_final_handoff_checklist_json_export,
    build_pilot_handoff_summary_export,
    build_pilot_handoff_summary_json_export,
    build_pilot_readiness_json_export,
    build_pilot_readiness_items,
    build_pilot_real_condition_export,
    build_pilot_real_condition_json_export,
    build_pilot_runbook_json_export,
    build_pilot_runbook_view,
    format_pilot_acceptance_markdown,
    format_pilot_real_condition_markdown,
    format_pilot_readiness_markdown,
    format_pilot_runbook_markdown,
)
from media_security_audit.web_reports import generate_web_reports  # noqa: E402
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
    def test_web_app_binds_fastapi_annotation_types(self) -> None:
        web = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web.py"
        ).read_text(encoding="utf-8")

        self.assertIn("globals().update", web)
        self.assertIn('"Request": Request', web)
        self.assertIn('"HTTPBasicCredentials": HTTPBasicCredentials', web)

    def test_mission_template_accepts_localized_confidence_input(self) -> None:
        template = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_templates"
            / "mission.html"
        ).read_text(encoding="utf-8")

        self.assertIn('name="confidence" inputmode="decimal"', template)
        self.assertIn('pattern="[0-1]([,.][0-9]+)?"', template)
        self.assertNotIn('name="confidence" type="number"', template)

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
        self.assertIn('class="brand-mark"', template)
        self.assertIn('class="topbar-utilities"', template)
        self.assertIn('class="topbar-pill"', template)
        self.assertIn('class="topbar-icon"', template)
        self.assertIn('aria-label="Operator utilities"', template)
        self.assertIn('role="status"', template)
        self.assertIn('aria-live="polite"', template)
        self.assertIn('role="alert"', template)
        self.assertIn('aria-label="Workspace metadata"', template)

        self.assertIn(">Overview</a>", template)
        self.assertIn('href="/clients"', template)
        self.assertIn(">Clients</a>", template)
        self.assertIn('href="/operator"', template)
        self.assertIn(">Start</a>", template)
        self.assertIn('href="/audits"', template)
        self.assertIn(">Audits</a>", template)
        self.assertIn('href="/exports"', template)
        self.assertIn(">Exports</a>", template)
        self.assertIn('href="/wizard"', template)
        self.assertIn(">New Audit</a>", template)
        self.assertIn('href="/vulnerabilities"', template)
        self.assertIn(">CVE Catalog</a>", template)
        self.assertIn('href="/test-readiness"', template)
        self.assertIn(">Test VM</a>", template)
        self.assertIn('href="/pilot"', template)
        self.assertIn(">Pilot</a>", template)

        for prefix in [
            "/operator",
            "/clients",
            "/audits",
            "/wizard",
            "/vulnerabilities",
            "/activity",
            "/exports",
            "/templates",
            "/remediations",
            "/test-readiness",
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
        self.assertIn(".service-run-summary", css)
        self.assertIn(".vulnerability-summary", css)
        self.assertIn(".vulnerability-import", css)
        self.assertIn(".quick-read-panel", css)
        self.assertIn(".quick-read-grid", css)
        self.assertIn(".handoff-panel", css)
        self.assertIn(".handoff-grid", css)
        self.assertIn(".handoff-status", css)
        self.assertIn(".mission-focus", css)
        self.assertIn(".mission-focus-grid", css)
        self.assertIn(".mission-focus-actions", css)
        self.assertIn(".catalog-hero", css)
        self.assertIn(".catalog-card", css)
        self.assertIn(".scan-progress-overlay", css)
        self.assertIn(".scan-progress-track", css)
        self.assertIn(".operator-note", css)
        self.assertIn(".compact-create-layout", css)
        self.assertIn(".audit-status-strip", css)
        self.assertIn(".audit-card-grid", css)
        self.assertIn(".credential-guardrail", css)
        self.assertIn(".console-hero", css)
        self.assertIn(".console-phase-nav", css)
        self.assertIn(".console-card-grid", css)
        self.assertIn(".operator-hero", css)
        self.assertIn(".operator-flow", css)
        self.assertIn(".operator-action-grid", css)
        self.assertIn(".operator-session-grid", css)
        self.assertIn(".operator-ops-grid", css)
        self.assertIn(".directory-hero", css)
        self.assertIn(".directory-command-bar", css)
        self.assertIn(".directory-search", css)
        self.assertIn(".directory-shortcuts", css)
        self.assertIn(".delivery-command-bar", css)
        self.assertIn(".delivery-toggle", css)
        self.assertIn(".remediation-entry-card", css)
        self.assertIn("color-scheme: dark", css)
        self.assertIn(".brand-mark", css)
        self.assertIn(".topbar-utilities", css)
        self.assertIn(".topbar-pill", css)
        self.assertIn(".topbar-icon", css)
        self.assertIn("Dark operator shell inspired by modern security dashboards", css)
        self.assertIn("var(--accent-soft)", css)

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
            "audits.html",
            "client.html",
            "clients.html",
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
            "technician-workflow",
            "onboarding",
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
            "missions",
            "clients",
        ]:
            self.assertIn(f'href="#{anchor}"', template)
            self.assertIn(f'id="{anchor}"', template)

        for counter in [
            "view.technician_workflow_steps|length",
            "view.onboarding_ready_count",
            "view.onboarding_total_count",
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
        self.assertIn("Technician Workflow", template)
        self.assertIn('aria-label="Technician workflow actions"', template)
        self.assertIn('aria-label="Technician workflow steps"', template)
        self.assertIn("view.technician_workflow_steps", template)
        self.assertIn("step.status", template)
        self.assertIn("step.detail", template)
        self.assertIn("step.action_href", template)
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
        self.assertIn('href="/wizard"', template)
        self.assertIn("New Guided Audit", template)
        self.assertIn("view.onboarding_steps", template)
        self.assertIn("view.onboarding_next_action_href", template)
        self.assertIn("step.action_href", template)

    def test_dashboard_template_syncs_template_audit_type(self) -> None:
        template_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_templates"
            / "dashboard.html"
        )
        template = template_path.read_text(encoding="utf-8")

        self.assertIn("data-template-audit-select", template)
        self.assertIn('data-audit-type="{{ template.audit_type }}"', template)
        self.assertIn("data-audit-type-select", template)
        self.assertIn("selectedOption.dataset.auditType", template)
        self.assertIn('templateSelect.addEventListener("change", syncAuditType)', template)

    def test_operator_template_exposes_simplified_start_workflow(self) -> None:
        template_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_templates"
            / "operator.html"
        )
        css_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_static"
            / "app.css"
        )
        web_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web.py"
        )
        dashboard_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_templates"
            / "dashboard.html"
        )
        template = template_path.read_text(encoding="utf-8")
        css = css_path.read_text(encoding="utf-8")
        web = web_path.read_text(encoding="utf-8")
        dashboard = dashboard_path.read_text(encoding="utf-8")

        self.assertIn('@app.get("/operator"', web)
        self.assertIn('"operator.html"', web)
        self.assertIn("build_dashboard_view(store)", web)
        self.assertIn("Start A Security Audit", template)
        self.assertIn('aria-label="Operator start page"', template)
        self.assertIn('aria-label="Operator workflow"', template)
        self.assertIn('aria-label="Operator next actions"', template)
        self.assertIn('aria-label="Operator active sessions"', template)
        self.assertIn('aria-label="Operator operations center"', template)
        self.assertIn('aria-label="Operator safety guardrails"', template)
        self.assertIn('href="/clients#new-client"', template)
        self.assertIn('href="/wizard"', template)
        self.assertIn('href="/wizard#wizard-scope"', template)
        self.assertIn('href="/wizard#wizard-checks"', template)
        self.assertIn('href="/audits"', template)
        self.assertIn('href="/exports"', template)
        self.assertIn('href="/test-readiness"', template)
        self.assertIn('href="/vulnerabilities"', template)
        self.assertIn('href="/remediations"', template)
        self.assertIn("view.technician_workflow_steps", template)
        self.assertIn("view.missions[:6]", template)
        self.assertIn("mission.preparation_action_href", template)
        self.assertIn('/missions/{{ mission.id }}/console', template)
        self.assertIn('/missions/{{ mission.id }}/session', template)
        self.assertIn("brute-force testing stay outside the V1", template)
        self.assertIn('href="/operator"', dashboard)

        for css_class in [
            ".operator-hero",
            ".operator-flow",
            ".operator-action-grid",
            ".operator-session-grid",
            ".operator-ops-grid",
            ".operator-guardrail",
        ]:
            self.assertIn(css_class, css)

    def test_clients_template_exposes_dedicated_client_workspace(self) -> None:
        template_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_templates"
            / "clients.html"
        )
        web_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web.py"
        )
        template = template_path.read_text(encoding="utf-8")
        web = web_path.read_text(encoding="utf-8")

        self.assertIn('@app.get("/clients"', web)
        self.assertIn('"clients.html"', web)
        self.assertIn("Customer workspace", template)
        self.assertIn("client-directory-hero", template)
        self.assertIn('aria-label="Client workspace summary"', template)
        self.assertIn('aria-label="Actions rapides clients"', template)
        self.assertIn("data-client-search", template)
        self.assertIn("data-client-row", template)
        self.assertIn("data-client-visible-count", template)
        self.assertIn('id="new-client"', template)
        self.assertIn('aria-label="Create client"', template)
        self.assertIn("operator-note", template)
        self.assertIn("Client page purpose", template)
        self.assertIn('id="client-list"', template)
        self.assertIn('<caption class="sr-only">Clients</caption>', template)
        self.assertIn("client.next_action_href", template)

    def test_audits_template_exposes_dedicated_audit_workspace(self) -> None:
        template_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_templates"
            / "audits.html"
        )
        web_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web.py"
        )
        template = template_path.read_text(encoding="utf-8")
        web = web_path.read_text(encoding="utf-8")

        self.assertIn('@app.get("/audits"', web)
        self.assertIn('"audits.html"', web)
        self.assertIn("Audit tasks", template)
        self.assertIn("audit-directory-hero", template)
        self.assertIn('aria-label="Audit workspace summary"', template)
        self.assertIn("audit-status-strip", template)
        self.assertIn('aria-label="Recherche et filtres audits"', template)
        self.assertIn("data-audit-search", template)
        self.assertIn("data-audit-row", template)
        self.assertIn("data-audit-card", template)
        self.assertIn("data-audit-visible-count", template)
        self.assertIn('href="#ready-audits"', template)
        self.assertIn('href="#review-audits"', template)
        self.assertIn('href="#blocked-audits"', template)
        self.assertIn('id="quick-mission"', template)
        self.assertIn('aria-label="Create quick mission"', template)
        self.assertIn("Recommended path", template)
        self.assertIn('id="all-audits"', template)
        self.assertIn('<caption class="sr-only">Audits</caption>', template)
        self.assertIn("mission.preparation_action_href", template)
        self.assertIn('/missions/{{ item.mission_id }}/console', template)
        self.assertIn('/missions/{{ mission.id }}/console', template)

    def test_wizard_template_exposes_guided_audit_flow(self) -> None:
        template_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_templates"
            / "wizard.html"
        )
        css_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_static"
            / "app.css"
        )
        web_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web.py"
        )
        template = template_path.read_text(encoding="utf-8")
        css = css_path.read_text(encoding="utf-8")
        web = web_path.read_text(encoding="utf-8")

        self.assertIn('@app.get("/wizard"', web)
        self.assertIn('@app.post("/wizard"', web)
        self.assertIn('f"/missions/{mission.id}/console"', web)
        self.assertIn("create_guided_audit_from_form", web)
        self.assertIn("CHECK_SCOPE_REQUIREMENTS", web)
        self.assertIn("CHECK_SCOPE_TYPES", web)
        self.assertIn("CHECK_USE_CASES", web)
        self.assertIn('"use_case": CHECK_USE_CASES[check]', web)
        self.assertIn('"target_requirement": CHECK_SCOPE_REQUIREMENTS[check]', web)
        self.assertIn('"required_types": [', web)
        self.assertIn("scope_type.value for scope_type in CHECK_SCOPE_TYPES[check]", web)
        self.assertIn("wizard.audit_created", web)
        self.assertIn('@app.post("/missions/{mission_id}/scan-runs"', web)
        self.assertIn('/missions/{mission_id}/roadmap/{export_format}', web)
        self.assertIn("build_mission_roadmap_export", web)
        self.assertIn("run_web_scan_check_from_form", web)
        self.assertIn("scan.web_executed", web)
        self.assertIn("vulnerability.correlated", web)
        self.assertIn('/missions/{mission_id}/vulnerabilities/correlate', web)
        self.assertIn("vulnerability.catalog_imported", web)
        self.assertIn('/missions/{mission_id}/vulnerabilities/catalog', web)
        self.assertIn('@app.get("/vulnerabilities"', web)
        self.assertIn('@app.post("/vulnerabilities/refresh-kev"', web)
        self.assertIn('@app.post("/vulnerabilities/catalog"', web)
        self.assertIn("build_vulnerability_catalog_view", web)
        self.assertIn("refresh_cisa_kev_catalog", web)
        self.assertIn("parse_vulnerability_catalog", web)
        self.assertIn("save_vulnerability_catalog", web)
        self.assertIn("#run-monitor", web)
        self.assertIn("#scan-plan", web)
        self.assertIn("#vulnerabilities", web)
        self.assertIn('aria-label="Create guided audit"', template)
        self.assertIn('id="wizard-client"', template)
        self.assertIn('id="wizard-mission"', template)
        self.assertIn('id="wizard-scope"', template)
        self.assertIn('id="wizard-checks"', template)
        self.assertIn('id="wizard-credentials"', template)
        self.assertIn('id="wizard-review"', template)
        self.assertIn('id="wizard-summary"', template)
        self.assertIn('href="#wizard-credentials"', template)
        self.assertIn('href="#wizard-review"', template)
        self.assertIn('aria-label="Guided audit snapshot"', template)
        self.assertIn('aria-live="polite"', template)
        self.assertIn('aria-label="Audit creation progress"', template)
        self.assertIn('aria-label="Guided audit navigation"', template)
        self.assertIn('aria-label="Service selection guidance"', template)
        self.assertIn("data-wizard-step", template)
        self.assertIn("data-wizard-progress", template)
        self.assertIn("data-wizard-previous", template)
        self.assertIn("data-wizard-next", template)
        self.assertIn("data-wizard-submit", template)
        self.assertIn("Creer Un Audit Guide", template)
        self.assertIn("Renseigne seulement ce qui est utile", template)
        self.assertIn("wizard-intro", template)
        self.assertIn("Qui audite-t-on ?", template)
        self.assertIn("Quel perimetre ?", template)
        self.assertIn("Quels services ?", template)
        self.assertIn("Creation puis console", template)
        self.assertIn("Precedent", template)
        self.assertIn("Suivant", template)
        self.assertIn("Creer L'audit", template)
        self.assertIn("wizard-mode-grid", template)
        self.assertIn("data-wizard-mode-option", template)
        self.assertIn("Audit interne", template)
        self.assertIn("Audit externe", template)
        self.assertIn("syncModeButtons", template)
        self.assertIn("modeButtons.forEach", template)
        self.assertIn("aria-label=\"Choisir le mode d'audit\"", template)
        self.assertIn("Selectionne le type d'analyse", template)
        self.assertIn("Cibles Autorisees", template)
        self.assertIn("Services A Tester", template)
        self.assertIn("Aucun brute force n'est lance depuis cet assistant.", template)
        self.assertIn("Validation", template)
        self.assertIn("wizard-target-guidance", template)
        self.assertIn('aria-label="Guide des cibles"', template)
        self.assertIn("CIDR, IP ou nom d'hote pour Nmap, SMB et inventaire LAN.", template)
        self.assertIn("Domaines publics pour DNS/Mail, TLS et exposition Internet.", template)
        self.assertIn("URL HTTPS completes pour les en-tetes HTTP et le TLS Web.", template)
        self.assertIn(
            "Controleurs de domaine ou hotes LDAP pour l'audit annuaire.",
            template,
        )
        self.assertIn(".wizard-target-guidance", css)
        self.assertIn("wizard-service-grid", template)
        self.assertIn("wizard-service-card", template)
        self.assertIn("wizard-service-label", template)
        self.assertIn("wizard-service-coverage", template)
        self.assertIn("wizard-coverage-list", template)
        self.assertIn("wizard-coverage-item", template)
        self.assertIn('aria-label="Selected service target coverage"', template)
        self.assertIn("data-wizard-coverage-list", template)
        self.assertIn("data-wizard-coverage-summary", template)
        self.assertIn("data-wizard-required-types", template)
        self.assertIn("data-wizard-check-label", template)
        self.assertIn("wizard-review-grid", template)
        self.assertIn("wizard-creation-checklist", template)
        self.assertIn('aria-label="Audit creation checklist"', template)
        self.assertIn('data-wizard-gate="client"', template)
        self.assertIn('data-wizard-gate="mission"', template)
        self.assertIn('data-wizard-gate="scope"', template)
        self.assertIn('data-wizard-gate="checks"', template)
        self.assertIn('data-wizard-gate="credentials"', template)
        self.assertIn("data-wizard-gate-status", template)
        self.assertIn("data-wizard-gate-detail", template)
        self.assertIn("Client pret", template)
        self.assertIn("Mission autorisee", template)
        self.assertIn("Perimetre approuve", template)
        self.assertIn("Services couverts", template)
        self.assertIn("Garde-fous identifiants", template)
        self.assertIn("Aucun brute force n'est lance depuis cet assistant.", template)
        self.assertIn("Toute validation active devra", template)
        self.assertIn("Preparer une revue de jeu d'identifiants", template)
        self.assertIn("data-wizard-credential-requested", template)
        self.assertIn("data-wizard-credential-guardrails", template)
        self.assertIn("data-wizard-credential-field", template)
        self.assertIn("data-wizard-review-credentials", template)
        self.assertIn("wizard-field-trial", template)
        self.assertIn('aria-label="Field trial readiness"', template)
        self.assertIn("Preparation Du Test Reel", template)
        self.assertIn("Avant les controles actifs", template)
        self.assertIn("Autorisation conservee", template)
        self.assertIn("Perimetre verifie", template)
        self.assertIn("Outils verifies", template)
        self.assertIn("Sorties pretes", template)
        self.assertIn("Arret connu", template)
        self.assertIn("Fenetre client validee", template)
        self.assertIn("wizard-review-status", template)
        self.assertIn("data-wizard-review-target-list", template)
        self.assertIn("data-wizard-review-check-list", template)
        self.assertIn("check.use_case", template)
        self.assertIn("check.target_requirement", template)
        self.assertIn("Non-destructive plan, explicit execution later", template)

        for field in [
            'name="client_id"',
            'name="client_name"',
            'name="mission_name"',
            'name="authorization_reference"',
            'name="internal_targets"',
            'name="external_domains"',
            'name="web_urls"',
            'name="ad_servers"',
            'name="scope_approved"',
            'name="credential_review_requested"',
            'name="credential_dataset_name"',
            'name="credential_dataset_source"',
            'name="credential_record_count"',
            'name="credential_scope_notes"',
            'name="credential_guardrails_confirmed"',
        ]:
            self.assertIn(field, template)

        self.assertIn("data-wizard-template-select", template)
        self.assertIn("data-wizard-audit-type-select", template)
        self.assertIn("data-wizard-client-select", template)
        self.assertIn("data-wizard-client-name", template)
        self.assertIn("data-wizard-mission-name", template)
        self.assertIn("data-wizard-authorization-reference", template)
        self.assertIn("data-wizard-scope-approved", template)
        self.assertIn("data-wizard-target", template)
        self.assertIn("data-wizard-check", template)
        self.assertIn("data-wizard-summary-status", template)
        self.assertIn("data-wizard-summary-target-list", template)
        self.assertIn("data-wizard-summary-check-list", template)
        self.assertIn("Le perimetre autorise est confirme", template)
        self.assertIn("Choisis un client existant ou renseigne un nouveau client.", template)
        self.assertIn("Ajoute au moins une cible dans le perimetre autorise.", template)
        self.assertIn("Coche les services, ajoute les cibles compatibles et confirme le perimetre.", template)
        self.assertIn("Confirme les garde-fous identifiants ou laisse la revue des identifiants desactivee.", template)
        self.assertIn("Pret a creer. Les controles actifs resteront separes", template)
        self.assertIn("const credentialRequested = () =>", template)
        self.assertIn("const credentialReady = () =>", template)
        self.assertIn("const credentialLabel = () =>", template)
        self.assertIn("const updateSnapshot = () =>", template)
        self.assertIn("const validateStep = (index, showMessage = false) =>", template)
        self.assertIn("const setStep = (index) =>", template)
        self.assertIn("const firstInvalidStep = () =>", template)
        self.assertIn("const setGate = (key, ready, detail) =>", template)
        self.assertIn("const updateCreationChecklist = (state, snapshot) =>", template)
        self.assertIn("updateCreationChecklist(state", template)
        self.assertIn("const selectedCheckDetails = () =>", template)
        self.assertIn("const scopeTypesForTargetLine = (input, value) =>", template)
        self.assertIn("const availableScopeTypes = () =>", template)
        self.assertIn("const serviceCoverage = () =>", template)
        self.assertIn("const targetActionForCheck = (check) =>", template)
        self.assertIn("return { field: \"web_urls\", label: \"Ajouter une URL\" }", template)
        self.assertIn("return { field: \"external_domains\", label: \"Ajouter un domaine\" }", template)
        self.assertIn("return { field: \"ad_servers\", label: \"Ajouter un serveur AD/LDAP\" }", template)
        self.assertIn("return { field: \"internal_targets\", label: \"Ajouter hote/IP/CIDR\" }", template)
        self.assertIn("const coverageReady = () =>", template)
        self.assertIn("coverage.every((check) => check.ready)", template)
        self.assertIn("coverageReady()", template)
        self.assertIn("const renderServiceCoverage = () =>", template)
        self.assertIn("data-wizard-target-action", template)
        self.assertIn("button.addEventListener(\"click\", () => focusTargetField(action.field))", template)
        self.assertIn("const focusTargetField = (fieldName) =>", template)
        self.assertIn("setStep(2)", template)
        self.assertIn("field.focus()", template)
        self.assertIn("renderServiceCoverage();", template)
        self.assertIn("renderPills(summaryTargetList", template)
        self.assertIn("renderPills(summaryCheckList", template)
        self.assertIn("renderPills(reviewTargetList", template)
        self.assertIn("renderPills(reviewCheckList", template)
        self.assertIn("templateSelect.addEventListener(\"change\", syncTemplate)", template)
        self.assertIn("nextButton.addEventListener(\"click\"", template)
        self.assertIn("previousButton.addEventListener(\"click\"", template)
        self.assertIn("document.querySelector(\".wizard-form\").addEventListener(\"submit\"", template)
        self.assertIn(".wizard-form", css)
        self.assertIn(".page-lead", css)
        self.assertIn(".wizard-intro", css)
        self.assertIn(".wizard-shell", css)
        self.assertIn(".wizard-main", css)
        self.assertIn(".wizard-progress", css)
        self.assertIn(".wizard-step-help", css)
        self.assertIn(".wizard-mode-grid", css)
        self.assertIn(".wizard-mode-card", css)
        self.assertIn(".wizard-mode-card.is-active", css)
        self.assertIn(".wizard-summary", css)
        self.assertIn(".wizard-summary-grid", css)
        self.assertIn(".wizard-pill", css)
        self.assertIn(".wizard-step", css)
        self.assertIn(".wizard-step[hidden]", css)
        self.assertIn(".wizard-step-message", css)
        self.assertIn(".wizard-service-grid", css)
        self.assertIn(".wizard-service-card", css)
        self.assertIn(".wizard-service-label", css)
        self.assertIn(".wizard-service-coverage", css)
        self.assertIn(".wizard-coverage-list", css)
        self.assertIn(".wizard-coverage-item", css)
        self.assertIn(".wizard-coverage-status", css)
        self.assertIn(".wizard-coverage-action", css)
        self.assertIn(".wizard-confirmation", css)
        self.assertIn(".wizard-creation-checklist", css)
        self.assertIn(".wizard-gate", css)
        self.assertIn(".wizard-gate.is-ready", css)
        self.assertIn(".wizard-gate.is-missing", css)
        self.assertIn(".wizard-gate-status", css)
        self.assertIn(".wizard-field-trial", css)
        self.assertIn(".credential-guardrail", css)
        self.assertIn(".wizard-review-grid", css)
        self.assertIn(".wizard-nav", css)

    def test_test_readiness_template_exposes_vm_smoke_test_flow(self) -> None:
        template_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_templates"
            / "test_readiness.html"
        )
        css_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_static"
            / "app.css"
        )
        web_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web.py"
        )
        template = template_path.read_text(encoding="utf-8")
        css = css_path.read_text(encoding="utf-8")
        web = web_path.read_text(encoding="utf-8")

        self.assertIn('@app.get("/test-readiness"', web)
        self.assertIn('"test_readiness.html"', web)
        self.assertIn("VM Test Readiness", template)
        self.assertIn('aria-label="VM test readiness shortcuts"', template)
        self.assertIn('aria-label="VM update commands"', template)
        self.assertIn('aria-label="VM smoke test commands"', template)
        self.assertIn('aria-label="VM UI smoke checklist"', template)
        self.assertIn("git pull --ff-only", template)
        self.assertIn("bash scripts/debian-vm-update.sh", template)
        self.assertIn("bash scripts/debian-vm-status.sh", template)
        self.assertIn("bash scripts/debian-vm-ui-smoke-test.sh", template)
        self.assertIn("reports/test-readiness", template)
        self.assertIn("ssh -L 8080:127.0.0.1:8080", template)
        self.assertIn("http://127.0.0.1:8080/test-readiness", template)
        self.assertIn("No scanner command is launched by this page.", template)
        self.assertIn("Create Guided Audit", template)
        self.assertIn("Open Audit Console", template)
        self.assertIn("Generate Reports", template)
        self.assertIn("Credential validation and any brute-force style workflow remain blocked", template)
        self.assertIn('href="/clients#new-client"', template)
        self.assertIn('href="/wizard"', template)
        self.assertIn('href="/audits"', template)
        self.assertIn('href="/exports"', template)
        self.assertIn(".test-command-grid", css)
        self.assertIn(".test-command-card", css)
        self.assertIn(".test-checklist-grid", css)
        self.assertIn(".test-checklist-card", css)
        self.assertIn(".test-safety-note", css)
        self.assertIn(".test-feedback-list", css)

    def test_vulnerability_catalog_template_exposes_catalog_workflow(self) -> None:
        template_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_templates"
            / "vulnerabilities.html"
        )
        template = template_path.read_text(encoding="utf-8")

        self.assertIn("CVE / KEV Catalog", template)
        self.assertIn('action="/vulnerabilities/refresh-kev"', template)
        self.assertIn('aria-label="Refresh CISA KEV catalog"', template)
        self.assertIn('action="/vulnerabilities/catalog"', template)
        self.assertIn('aria-label="Import global vulnerability catalog"', template)
        self.assertIn("view.summary.advisory_count", template)
        self.assertIn("view.summary.known_exploited_count", template)
        self.assertIn("view.summary.update_source", template)
        self.assertIn("view.severity_rows", template)
        self.assertIn("view.rows", template)
        self.assertIn("item.remediation", template)
        self.assertIn("item.counter_test", template)

    def test_mission_template_exposes_scan_progress_feedback(self) -> None:
        template_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_templates"
            / "mission.html"
        )
        template = template_path.read_text(encoding="utf-8")

        self.assertIn("data-scan-run-form", template)
        self.assertIn("data-scan-run-label", template)
        self.assertIn("data-scan-progress", template)
        self.assertIn("data-scan-progress-title", template)
        self.assertIn("data-scan-progress-bar", template)
        self.assertIn("data-scan-progress-step", template)
        self.assertIn("Authorization confirmed", template)
        self.assertIn("Scan running", template)
        self.assertIn("Findings importing", template)
        self.assertIn('form.addEventListener("submit"', template)

    def test_mission_console_template_exposes_operator_flow(self) -> None:
        template_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_templates"
            / "mission_console.html"
        )
        css_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_static"
            / "app.css"
        )
        web_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web.py"
        )
        template = template_path.read_text(encoding="utf-8")
        css = css_path.read_text(encoding="utf-8")
        web = web_path.read_text(encoding="utf-8")

        self.assertIn('@app.get(\n        "/missions/{mission_id}/console"', web)
        self.assertIn('"mission_console.html"', web)
        self.assertIn("Console D'audit", template)
        self.assertIn('/missions/{{ view.mission.id }}/session', template)
        self.assertIn("Tableau de session", template)
        self.assertIn("view.session_dashboard.progress_percent", template)
        self.assertIn('aria-label="Audit console summary"', template)
        self.assertIn('aria-label="Audit console phases"', template)
        self.assertIn('id="console-prepare"', template)
        self.assertIn('id="console-launch"', template)
        self.assertIn('id="console-analyze"', template)
        self.assertIn('id="console-deliver"', template)
        self.assertIn("Lancement detaille", template)
        self.assertIn("Mission complete", template)
        self.assertIn("Preparation", template)
        self.assertIn("Centre De Lancement", template)
        self.assertIn("Restitution", template)
        self.assertIn("view.go_no_go.decision", template)
        self.assertIn("view.cockpit.next_action_label", template)
        self.assertIn("view.scan_launch.ready_count", template)
        self.assertIn("view.cockpit.services", template)
        self.assertIn("view.vulnerability_matches", template)
        self.assertIn("view.report_delivery.items", template)
        self.assertIn('aria-label="Selected service launch cards"', template)
        self.assertIn('aria-label="Priority vulnerability candidates"', template)
        self.assertIn('aria-label="Delivery checklist"', template)
        self.assertIn(".console-hero", css)
        self.assertIn(".console-phase-nav", css)
        self.assertIn(".console-status-panel", css)
        self.assertIn(".console-card-grid", css)

    def test_session_dashboard_template_exposes_analysis_progress(self) -> None:
        template_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_templates"
            / "session_dashboard.html"
        )
        css_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_static"
            / "app.css"
        )
        web_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web.py"
        )
        mission_template = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_templates"
            / "mission.html"
        ).read_text(encoding="utf-8")
        template = template_path.read_text(encoding="utf-8")
        css = css_path.read_text(encoding="utf-8")
        web = web_path.read_text(encoding="utf-8")

        self.assertIn('@app.get(\n        "/missions/{mission_id}/session"', web)
        self.assertIn('"session_dashboard.html"', web)
        self.assertIn("Tableau De Session", template)
        self.assertIn('aria-label="Analysis session status"', template)
        self.assertIn('aria-label="Analysis session progress"', template)
        self.assertIn('aria-label="Analysis session counters"', template)
        self.assertIn('aria-label="Phases de la session"', template)
        self.assertIn('aria-label="Analysis session progress steps"', template)
        self.assertIn('aria-label="Selected session services"', template)
        self.assertIn('aria-label="Approved session targets"', template)
        self.assertIn('<caption class="sr-only">Analysis session run dashboard</caption>', template)
        self.assertIn("view.session_dashboard.progress_percent", template)
        self.assertIn("view.session_dashboard.current_phase", template)
        self.assertIn("view.session_dashboard.selected_service_count", template)
        self.assertIn("view.session_dashboard.completed_service_count", template)
        self.assertIn("view.session_dashboard.vulnerability_match_count", template)
        self.assertIn("Preparation", template)
        self.assertIn("Decouverte", template)
        self.assertIn("Analyse", template)
        self.assertIn("Livrables PDF et JSON", template)
        self.assertIn("Explication CVE et CVSS", template)
        self.assertIn("Suivi remediation", template)
        self.assertIn('/missions/{{ view.mission.id }}/session', mission_template)
        self.assertIn(".session-hero", css)
        self.assertIn(".session-phase-lane", css)
        self.assertIn(".session-phase-item", css)
        self.assertIn(".session-progress-track", css)
        self.assertIn(".session-step-grid", css)
        self.assertIn(".session-service-list", css)
        self.assertIn(".session-remediation-grid", css)

    def test_client_template_exposes_preparation_action_links(self) -> None:
        template_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_templates"
            / "client.html"
        )
        template = template_path.read_text(encoding="utf-8")

        self.assertIn("client-detail-hero", template)
        self.assertIn('aria-label="Client summary"', template)
        self.assertIn('aria-label="Recherche missions client"', template)
        self.assertIn("data-client-mission-search", template)
        self.assertIn("data-client-mission-row", template)
        self.assertIn("data-client-mission-visible-count", template)
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

        self.assertIn("delivery-hero", template)
        self.assertIn("Centre de livraison", template)
        self.assertIn('aria-label="Actions rapides exports"', template)
        self.assertIn('aria-label="Mission export shortcuts"', template)
        self.assertIn('href="#export-filters"', template)
        self.assertIn('href="#handoff-readiness"', template)
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
        self.assertIn('summary["handoff_ready"]', template)
        self.assertIn('summary["handoff_attention"]', template)
        self.assertIn('id="handoff-readiness"', template)
        self.assertIn('aria-label="Mission export handoff readiness"', template)
        self.assertIn("item.handoff_status", template)
        self.assertIn("item.handoff_detail", template)
        self.assertIn("item.handoff_action", template)
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
        self.assertIn("/missions/{{ item.mission_id }}/export-verification/markdown", template)
        self.assertIn("/missions/{{ item.mission_id }}#reports", template)
        self.assertIn("/exports?{{ toggle_query }}", template)

    def test_remediation_template_exposes_operator_library_workflow(self) -> None:
        template_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_templates"
            / "remediations.html"
        )
        template = template_path.read_text(encoding="utf-8")

        self.assertIn("remediation-hero", template)
        self.assertIn("Base de remédiation", template)
        self.assertIn('aria-label="Remediation summary"', template)
        self.assertIn('aria-label="Recherche remédiations"', template)
        self.assertIn("data-remediation-search", template)
        self.assertIn("data-remediation-row", template)
        self.assertIn("data-remediation-visible-count", template)
        self.assertIn("data-remediation-search-empty", template)
        self.assertIn('aria-label="Remediation shortcuts"', template)
        self.assertIn('href="#remediation-filters"', template)
        self.assertIn('href="#remediation-entries"', template)
        self.assertIn('href="#remediation-exports"', template)
        self.assertIn('aria-label="Filter remediation library"', template)
        self.assertIn("entry.remediation", template)
        self.assertIn("entry.counter_test", template)
        self.assertIn("view.export_links", template)

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
        self.assertIn("view.vm_operations", template)
        self.assertIn("view.smoke_test_items", template)
        self.assertIn("view.real_condition_items", template)
        self.assertIn("view.sections", template)
        self.assertIn("view.acceptance_items", template)
        self.assertIn("view.readiness_items", template)
        self.assertIn("view.attention_items", template)
        self.assertIn("view.readiness_rollup", template)
        self.assertIn("view.handoff_decision", template)
        self.assertIn("view.evidence_files", template)
        self.assertIn('aria-label="Pilot runbook summary"', template)
        self.assertIn('aria-label="Pilot readiness rollup"', template)
        self.assertIn("view.readiness_rollup.status", template)
        self.assertIn("view.readiness_rollup.ready", template)
        self.assertIn("view.readiness_rollup.warning", template)
        self.assertIn("view.readiness_rollup.blocked", template)
        self.assertIn('id="pilot-handoff-decision"', template)
        self.assertIn('aria-label="Pilot handoff decision actions"', template)
        self.assertIn('aria-label="Pilot go no-go actions"', template)
        self.assertIn("view.handoff_decision.status", template)
        self.assertIn("view.handoff_decision.title", template)
        self.assertIn("view.handoff_decision.detail", template)
        self.assertIn("view.handoff_decision.action_href", template)
        self.assertIn("view.handoff_decision.action_label", template)
        self.assertIn("Decision Review", template)
        self.assertIn("Open Checklist", template)
        self.assertIn("Download Bundle", template)
        self.assertIn("Verify Bundle", template)
        self.assertIn('aria-label="Pilot evidence file categories"', template)
        self.assertIn("view.evidence_automation_file_count", template)
        self.assertIn("view.evidence_human_file_count", template)
        self.assertIn("view.evidence_manifest_file_count", template)
        self.assertIn("view.evidence_archive_file_count", template)
        self.assertIn("view.evidence_total_size_bytes", template)
        self.assertIn("view.evidence_archive_total_size_bytes", template)
        self.assertIn("Evidence Bytes", template)
        self.assertIn("Archive Bytes", template)
        self.assertIn('aria-label="Pilot runbook shortcuts"', template)
        self.assertIn('href="#pilot-handoff-decision"', template)
        self.assertIn('href="#pilot-vm-operations"', template)
        self.assertIn('href="#pilot-smoke-test"', template)
        self.assertIn('href="#pilot-real-condition"', template)
        self.assertIn('id="pilot-vm-operations"', template)
        self.assertIn('aria-label="Pilot VM operation links"', template)
        self.assertIn('aria-label="Pilot VM operation commands"', template)
        self.assertIn("VM Pilot Operations", template)
        self.assertIn("operation.label", template)
        self.assertIn("operation.command", template)
        self.assertIn("operation.detail", template)
        self.assertIn("operation.review_href", template)
        self.assertIn('id="pilot-smoke-test"', template)
        self.assertIn('aria-label="Pilot smoke test links"', template)
        self.assertIn('aria-label="Pilot V1 smoke test checklist"', template)
        self.assertIn("item.action", template)
        self.assertIn("item.expected_result", template)
        self.assertIn("item.evidence", template)
        self.assertIn("V1 Smoke Test", template)
        self.assertIn('id="pilot-real-condition"', template)
        self.assertIn('aria-label="Pilot real condition trial links"', template)
        self.assertIn('aria-label="Pilot real condition checklist"', template)
        self.assertIn("Real Condition Trial", template)
        self.assertIn("view.real_condition_items", template)
        self.assertIn("item.technician_action", template)
        self.assertIn("item.pause_condition", template)
        self.assertIn('href="/pilot/real-condition.md"', template)
        self.assertIn('href="/pilot/real-condition.json"', template)
        self.assertIn('id="pilot-attention"', template)
        self.assertIn('aria-label="Pilot attention links"', template)
        self.assertIn('id="pilot-bundle"', template)
        self.assertIn('aria-label="Pilot evidence bundle links"', template)
        self.assertIn('<caption class="sr-only">Pilot evidence bundle files</caption>', template)
        self.assertIn("<th>Review</th>", template)
        self.assertIn("item.review_order", template)
        self.assertIn("<th>Purpose</th>", template)
        self.assertIn("item.purpose", template)
        self.assertIn("<th>Category</th>", template)
        self.assertIn("item.category", template)
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
        self.assertIn('href="/pilot/final-handoff-checklist.md"', template)
        self.assertIn('href="/pilot/final-handoff-checklist.json"', template)
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
        self.assertEqual(view.handoff_decision.status, "warning")
        self.assertEqual(view.handoff_decision.title, "Readiness review required")
        self.assertEqual(view.handoff_decision.action_label, "Review System")
        self.assertEqual(view.handoff_decision.action_href, "/system")
        self.assertEqual(
            [operation.label for operation in view.vm_operations],
            ["Update", "Preflight", "Start", "Status", "Readiness", "Closeout"],
        )
        self.assertEqual(
            view.vm_operations[0].command,
            "cd ~/media-security-audit && git pull --ff-only",
        )
        self.assertEqual(
            view.vm_operations[-1].command,
            "bash scripts/debian-vm-pilot-closeout.sh",
        )
        self.assertEqual(
            [item.path for item in view.evidence_files],
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
                "pilot-real-condition.md",
                "pilot-real-condition.json",
                "pilot-delivery-receipt.md",
                "pilot-delivery-receipt.json",
                "pilot-final-handoff-checklist.md",
                "pilot-final-handoff-checklist.json",
            ],
        )
        self.assertEqual(view.evidence_automation_file_count, 10)
        self.assertEqual(view.evidence_human_file_count, 9)
        self.assertEqual(view.evidence_manifest_file_count, 1)
        self.assertEqual(view.evidence_archive_file_count, 20)
        self.assertEqual(
            view.evidence_archive_file_count,
            len(view.evidence_files) + view.evidence_manifest_file_count,
        )
        self.assertEqual(
            view.evidence_total_size_bytes,
            sum(item.size_bytes for item in view.evidence_files),
        )
        self.assertGreater(view.evidence_total_size_bytes, 0)
        self.assertGreater(
            view.evidence_archive_total_size_bytes,
            view.evidence_total_size_bytes,
        )
        public_manifest = build_pilot_evidence_manifest([], view)
        self.assertEqual(
            view.evidence_archive_total_size_bytes,
            view.evidence_total_size_bytes
            + len(public_manifest.content.encode("utf-8")),
        )
        self.assertEqual(view.evidence_files[0].kind, "Human-readable Markdown")
        self.assertEqual(view.evidence_files[0].review_order, 1)
        self.assertEqual(
            view.evidence_files[0].purpose,
            "Compact handoff state and next actions.",
        )
        self.assertEqual(view.evidence_files[1].kind, "Automation JSON")
        self.assertEqual(view.evidence_files[1].category, "automation")
        self.assertEqual(view.evidence_files[1].review_order, 2)
        self.assertEqual(
            view.evidence_files[1].purpose,
            "Machine-readable handoff state.",
        )
        self.assertEqual(view.evidence_files[-1].path, "pilot-final-handoff-checklist.json")
        self.assertEqual(view.evidence_files[-1].review_order, 19)
        self.assertEqual(
            view.evidence_files[-1].purpose,
            "Machine-readable final handoff checklist.",
        )
        self.assertEqual(
            [item.review_order for item in view.evidence_files],
            list(range(1, 20)),
        )
        self.assertEqual(
            len([item for item in view.evidence_files if item.category == "automation"]),
            10,
        )
        self.assertEqual(
            len([item for item in view.evidence_files if item.category == "human"]),
            9,
        )
        self.assertTrue(all(len(item.sha256_short) == 12 for item in view.evidence_files))
        acceptance_titles = [item.title for item in view.acceptance_items]
        self.assertIn("Appliance status reviewed", acceptance_titles)
        self.assertIn("Workspace backup created", acceptance_titles)

        markdown = format_pilot_runbook_markdown(view)
        self.assertIn("# Pilot Runbook", markdown)
        self.assertIn("## VM Operations", markdown)
        self.assertIn("cd ~/media-security-audit && git pull --ff-only", markdown)
        self.assertIn("bash scripts/debian-vm-preflight.sh", markdown)
        self.assertIn("bash scripts/debian-vm-pilot-closeout.sh", markdown)
        self.assertIn("## V1 Smoke Test", markdown)
        self.assertIn("Open local web UI", markdown)
        self.assertIn("Generate report outputs", markdown)
        self.assertIn("## Real Condition Trial", markdown)
        self.assertIn("Confirm written authorization and customer window", markdown)
        self.assertIn("Run one guarded service at a time", markdown)
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

        runbook_payload = build_pilot_runbook_json_export(view).payload
        self.assertEqual(runbook_payload["schema_version"], 4)
        self.assertEqual(len(runbook_payload["vm_operations"]), 6)
        self.assertEqual(runbook_payload["smoke_test_item_count"], 6)
        self.assertEqual(runbook_payload["real_condition_item_count"], 8)
        self.assertEqual(
            runbook_payload["smoke_test_items"][0]["title"],
            "Open local web UI",
        )
        self.assertEqual(
            runbook_payload["real_condition_items"][0]["title"],
            "Confirm written authorization and customer window",
        )
        self.assertEqual(
            runbook_payload["real_condition_items"][4]["title"],
            "Run one guarded service at a time",
        )
        self.assertEqual(
            runbook_payload["vm_operations"][0]["command"],
            "cd ~/media-security-audit && git pull --ff-only",
        )
        real_condition_markdown = format_pilot_real_condition_markdown(view)
        self.assertTrue(
            real_condition_markdown.startswith(
                "# Pilot Real Condition Trial Checklist\n"
            )
        )
        self.assertIn("Confirm written authorization and customer window", real_condition_markdown)
        self.assertIn("Run one guarded service at a time", real_condition_markdown)
        real_condition_export = build_pilot_real_condition_export(view)
        self.assertEqual(real_condition_export.filename, "pilot-real-condition.md")
        self.assertEqual(real_condition_export.content, real_condition_markdown)
        real_condition_json = build_pilot_real_condition_json_export(view)
        self.assertEqual(real_condition_json.filename, "pilot-real-condition.json")
        self.assertEqual(real_condition_json.media_type, "application/json")
        self.assertEqual(real_condition_json.payload["schema_version"], 1)
        self.assertEqual(real_condition_json.payload["item_count"], 8)
        self.assertEqual(
            real_condition_json.payload["items"][0]["title"],
            "Confirm written authorization and customer window",
        )

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
        self.assertEqual(len(view.vm_operations), 6)
        self.assertEqual(len(view.smoke_test_items), 6)
        self.assertEqual(len(view.real_condition_items), 8)
        self.assertEqual(len(view.acceptance_items), 11)
        self.assertEqual(view.readiness_items, [])
        self.assertEqual(view.attention_items, [])
        self.assertEqual(view.readiness_rollup.warning, 0)
        self.assertEqual(len(view.evidence_files), 19)

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
        self.assertIn("- Handoff decision: `warning`", handoff_summary.content)
        self.assertIn("- Handoff action: `Review Attention`", handoff_summary.content)
        self.assertIn("- Attention items: `1`", handoff_summary.content)
        self.assertIn("- Automation files: `10`", handoff_summary.content)
        self.assertIn("- Human-readable files: `9`", handoff_summary.content)
        self.assertIn("- Manifest files: `1`", handoff_summary.content)
        self.assertIn("pilot-bundle-index.md", handoff_summary.content)
        self.assertIn("pilot-delivery-receipt.md", handoff_summary.content)
        self.assertIn("pilot-handoff-summary.json", handoff_summary.content)
        self.assertIn("pilot-readiness.json", handoff_summary.content)
        self.assertIn("pilot-attention.md", handoff_summary.content)
        self.assertIn("pilot-final-handoff-checklist.md", handoff_summary.content)
        self.assertIn("pilot-final-handoff-checklist.json", handoff_summary.content)
        self.assertIn("pilot-real-condition.md", handoff_summary.content)
        self.assertIn("pilot-real-condition.json", handoff_summary.content)
        self.assertIn("| File | Category | Kind | Review | Purpose |", handoff_summary.content)
        self.assertIn(
            "| pilot-runbook.md | human | Human-readable Markdown | 12 | Technician workflow. |",
            handoff_summary.content,
        )
        self.assertIn(
            "| manifest.json | manifest | Manifest JSON | 20 | File checksums for integrity review. |",
            handoff_summary.content,
        )
        handoff_json = build_pilot_handoff_summary_json_export(items)
        handoff_payload = json.loads(handoff_json.content)
        self.assertEqual(handoff_json.filename, "pilot-handoff-summary.json")
        self.assertEqual(handoff_json.media_type, "application/json")
        self.assertEqual(handoff_payload, handoff_json.payload)
        self.assertEqual(handoff_payload["schema_version"], 6)
        self.assertEqual(handoff_payload["handoff_type"], "pilot")
        self.assertEqual(handoff_payload["handoff_decision"]["status"], "warning")
        self.assertEqual(
            handoff_payload["handoff_decision"]["action_href"],
            "#pilot-attention",
        )
        self.assertEqual(handoff_payload["context"], "Client Pilot")
        self.assertEqual(handoff_payload["source"], "Pilot Runbook")
        self.assertEqual(handoff_payload["automation_file_count"], 10)
        self.assertEqual(handoff_payload["human_file_count"], 9)
        self.assertEqual(handoff_payload["manifest_file_count"], 1)
        self.assertEqual(handoff_payload["handoff_file_count"], 19)
        self.assertEqual(
            handoff_payload["handoff_file_details"][0],
            {
                "category": "human",
                "kind": "Human-readable Markdown",
                "path": "pilot-runbook.md",
                "purpose": "Technician workflow.",
                "review_order": 12,
            },
        )
        self.assertEqual(
            handoff_payload["handoff_file_details"][-1],
            {
                "category": "manifest",
                "kind": "Manifest JSON",
                "path": "manifest.json",
                "purpose": "File checksums for integrity review.",
                "review_order": 20,
            },
        )
        self.assertEqual(handoff_payload["readiness"]["status"], "warning")
        self.assertEqual(handoff_payload["readiness"]["warning"], 1)
        self.assertEqual(handoff_payload["next_action_count"], 1)
        self.assertEqual(handoff_payload["attention_items"][0]["label"], "Workspace backup")
        self.assertEqual(handoff_payload["attention_items"][0]["status"], "warning")
        self.assertIn("pilot-attention.json", handoff_payload["handoff_files"])
        self.assertIn("pilot-bundle-index.json", handoff_payload["handoff_files"])
        self.assertIn("pilot-bundle-inventory.json", handoff_payload["handoff_files"])
        self.assertIn("pilot-handoff-summary.json", handoff_payload["handoff_files"])
        self.assertIn("pilot-final-handoff-checklist.json", handoff_payload["handoff_files"])
        self.assertIn("pilot-readiness.json", handoff_payload["handoff_files"])
        self.assertIn("pilot-real-condition.json", handoff_payload["handoff_files"])
        self.assertIn("pilot-real-condition.md", handoff_payload["handoff_files"])
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
        self.assertIn("pilot-final-handoff-checklist.json", bundle_index.content)
        self.assertIn("pilot-handoff-summary.json", bundle_index.content)
        self.assertIn("pilot-delivery-receipt.md", bundle_index.content)
        self.assertIn("pilot-readiness.json", bundle_index.content)
        self.assertIn("pilot-real-condition.md", bundle_index.content)
        self.assertIn("pilot-real-condition.json", bundle_index.content)
        self.assertIn("- Automation files: `10`", bundle_index.content)
        self.assertIn("- Human-readable files: `9`", bundle_index.content)
        self.assertIn("- Manifest files: `1`", bundle_index.content)
        self.assertIn("| File | Category | Kind | Review | Purpose |", bundle_index.content)
        self.assertIn(
            "| manifest.json | manifest | Manifest JSON | 20 | File checksums",
            bundle_index.content,
        )
        bundle_index_json = build_pilot_bundle_index_json_export(items)
        bundle_index_payload = json.loads(bundle_index_json.content)
        self.assertEqual(bundle_index_json.filename, "pilot-bundle-index.json")
        self.assertEqual(bundle_index_json.media_type, "application/json")
        self.assertEqual(bundle_index_payload, bundle_index_json.payload)
        self.assertEqual(bundle_index_payload["schema_version"], 5)
        self.assertEqual(bundle_index_payload["index_type"], "pilot_evidence")
        self.assertEqual(bundle_index_payload["bundle_file_count"], 19)
        self.assertEqual(bundle_index_payload["automation_file_count"], 10)
        self.assertEqual(bundle_index_payload["human_file_count"], 9)
        self.assertEqual(bundle_index_payload["manifest_file_count"], 1)
        self.assertEqual(bundle_index_payload["review_step_count"], 20)
        self.assertEqual(bundle_index_payload["review_order"][3]["path"], "pilot-bundle-index.json")
        self.assertEqual(bundle_index_payload["review_order"][3]["category"], "automation")
        self.assertEqual(
            bundle_index_payload["review_order"][3]["kind"],
            "Automation JSON",
        )
        self.assertEqual(
            bundle_index_payload["review_order"][4]["path"],
            "pilot-bundle-inventory.json",
        )
        self.assertEqual(
            bundle_index_payload["review_order"][19]["kind"],
            "Manifest JSON",
        )
        inventory_csv = build_pilot_bundle_inventory_csv_export(items)
        inventory_rows = list(csv.DictReader(StringIO(inventory_csv.content)))
        self.assertEqual(inventory_csv.filename, "pilot-bundle-inventory.csv")
        self.assertEqual(inventory_csv.media_type, "text/csv; charset=utf-8")
        self.assertEqual(
            inventory_csv.content.splitlines()[0],
            "review_order,path,category,kind,size_bytes,sha256,sha256_short",
        )
        self.assertEqual(inventory_rows[0]["path"], "pilot-handoff-summary.md")
        self.assertEqual(inventory_rows[0]["category"], "human")
        self.assertEqual(inventory_rows[0]["kind"], "Human-readable Markdown")
        self.assertEqual(inventory_rows[0]["review_order"], "1")
        self.assertEqual(inventory_rows[1]["path"], "pilot-handoff-summary.json")
        self.assertEqual(inventory_rows[1]["category"], "automation")
        self.assertEqual(inventory_rows[1]["kind"], "Automation JSON")
        self.assertEqual(inventory_rows[1]["review_order"], "2")
        self.assertEqual(inventory_rows[-1]["path"], "pilot-final-handoff-checklist.json")
        self.assertEqual(inventory_rows[-1]["review_order"], "19")
        self.assertEqual(len(inventory_rows[0]["sha256_short"]), 12)
        inventory_json = build_pilot_bundle_inventory_json_export(items)
        inventory_payload = json.loads(inventory_json.content)
        self.assertEqual(inventory_json.filename, "pilot-bundle-inventory.json")
        self.assertEqual(inventory_json.media_type, "application/json")
        self.assertEqual(inventory_payload, inventory_json.payload)
        self.assertEqual(inventory_payload["schema_version"], 5)
        self.assertEqual(inventory_payload["bundle_type"], "pilot_evidence")
        self.assertEqual(inventory_payload["expected_file_count"], 19)
        self.assertEqual(inventory_payload["evidence_file_count"], 19)
        self.assertEqual(inventory_payload["manifest_file_count"], 1)
        self.assertEqual(inventory_payload["archive_file_count"], 20)
        self.assertEqual(inventory_payload["automation_file_count"], 10)
        self.assertEqual(inventory_payload["human_file_count"], 9)
        self.assertEqual(
            inventory_payload["evidence_total_size_bytes"],
            view.evidence_total_size_bytes,
        )
        self.assertEqual(
            inventory_payload["archive_total_size_bytes"],
            view.evidence_archive_total_size_bytes,
        )
        self.assertEqual(inventory_payload["files"][0]["path"], "pilot-handoff-summary.md")
        self.assertEqual(inventory_payload["files"][0]["category"], "human")
        self.assertEqual(inventory_payload["files"][0]["kind"], "Human-readable Markdown")
        self.assertEqual(inventory_payload["files"][0]["review_order"], 1)
        self.assertEqual(inventory_payload["files"][1]["path"], "pilot-handoff-summary.json")
        self.assertEqual(inventory_payload["files"][1]["category"], "automation")
        self.assertEqual(inventory_payload["files"][1]["review_order"], 2)
        self.assertEqual(inventory_payload["files"][-1]["path"], "pilot-final-handoff-checklist.json")
        self.assertEqual(inventory_payload["files"][-1]["review_order"], 19)
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
        self.assertIn("- Automation files: `10`", delivery_receipt.content)
        self.assertIn("- Human-readable files: `9`", delivery_receipt.content)
        self.assertIn("- Manifest files: `1`", delivery_receipt.content)
        self.assertIn("pilot-acceptance-checklist.json", delivery_receipt.content)
        self.assertIn("pilot-delivery-receipt.json", delivery_receipt.content)
        self.assertIn("pilot-final-handoff-checklist.md", delivery_receipt.content)
        self.assertIn("pilot-real-condition.md", delivery_receipt.content)
        self.assertIn("pilot-real-condition.json", delivery_receipt.content)
        self.assertIn("| File | Category | Kind | Review | Purpose |", delivery_receipt.content)
        self.assertIn(
            "| pilot-handoff-summary.md | human | Human-readable Markdown | 1 | Compact handoff state and next actions. |",
            delivery_receipt.content,
        )
        self.assertIn(
            "| manifest.json | manifest | Manifest JSON | 20 | File checksums for integrity review. |",
            delivery_receipt.content,
        )
        self.assertIn("Client representative:", delivery_receipt.content)
        self.assertIn("Remaining attention items reviewed", delivery_receipt.content)
        delivery_json = build_pilot_delivery_receipt_json_export(items)
        delivery_payload = json.loads(delivery_json.content)
        self.assertEqual(delivery_json.filename, "pilot-delivery-receipt.json")
        self.assertEqual(delivery_json.media_type, "application/json")
        self.assertEqual(delivery_payload, delivery_json.payload)
        self.assertEqual(delivery_payload["schema_version"], 5)
        self.assertEqual(delivery_payload["delivery_type"], "pilot")
        self.assertEqual(delivery_payload["automation_file_count"], 10)
        self.assertEqual(delivery_payload["human_file_count"], 9)
        self.assertEqual(delivery_payload["manifest_file_count"], 1)
        self.assertEqual(delivery_payload["delivered_file_count"], 19)
        self.assertEqual(
            delivery_payload["delivered_file_details"][0],
            {
                "category": "human",
                "kind": "Human-readable Markdown",
                "path": "pilot-handoff-summary.md",
                "purpose": "Compact handoff state and next actions.",
                "review_order": 1,
            },
        )
        self.assertEqual(
            delivery_payload["delivered_file_details"][-1],
            {
                "category": "manifest",
                "kind": "Manifest JSON",
                "path": "manifest.json",
                "purpose": "File checksums for integrity review.",
                "review_order": 20,
            },
        )
        self.assertEqual(delivery_payload["readiness"]["status"], "warning")
        self.assertEqual(delivery_payload["attention_items"], 1)
        self.assertIn("pilot-attention.json", delivery_payload["delivered_files"])
        self.assertIn("pilot-acceptance-checklist.json", delivery_payload["delivered_files"])
        self.assertIn("pilot-bundle-index.json", delivery_payload["delivered_files"])
        self.assertIn("pilot-bundle-inventory.json", delivery_payload["delivered_files"])
        self.assertIn("pilot-final-handoff-checklist.json", delivery_payload["delivered_files"])
        self.assertIn("pilot-real-condition.json", delivery_payload["delivered_files"])
        self.assertIn("pilot-real-condition.md", delivery_payload["delivered_files"])
        self.assertIn("pilot-runbook.json", delivery_payload["delivered_files"])
        self.assertIn("client_representative", delivery_payload["sign_off_fields"])
        final_checklist = build_pilot_final_handoff_checklist_export(items)
        self.assertEqual(final_checklist.filename, "pilot-final-handoff-checklist.md")
        self.assertEqual(final_checklist.media_type, "text/markdown; charset=utf-8")
        self.assertIn("# Pilot Final Handoff Checklist", final_checklist.content)
        self.assertIn("- Handoff decision: `warning`", final_checklist.content)
        self.assertIn("- Readiness status: `warning`", final_checklist.content)
        self.assertIn("- Attention checklist items: `3`", final_checklist.content)
        self.assertIn("- Manual checklist items: `4`", final_checklist.content)
        self.assertIn("| Verify bundle manifest | manual |", final_checklist.content)
        final_checklist_json = build_pilot_final_handoff_checklist_json_export(items)
        final_checklist_payload = json.loads(final_checklist_json.content)
        self.assertEqual(
            final_checklist_json.filename,
            "pilot-final-handoff-checklist.json",
        )
        self.assertEqual(final_checklist_json.media_type, "application/json")
        self.assertEqual(final_checklist_payload, final_checklist_json.payload)
        self.assertEqual(final_checklist_payload["schema_version"], 1)
        self.assertEqual(
            final_checklist_payload["checklist_type"],
            "pilot_final_handoff",
        )
        self.assertEqual(final_checklist_payload["item_count"], 7)
        self.assertEqual(final_checklist_payload["attention_item_count"], 3)
        self.assertEqual(final_checklist_payload["manual_item_count"], 4)
        self.assertEqual(final_checklist_payload["handoff_decision"]["status"], "warning")
        self.assertEqual(final_checklist_payload["readiness"]["status"], "warning")
        self.assertEqual(
            final_checklist_payload["items"][0]["id"],
            "review_handoff_decision",
        )
        self.assertEqual(
            final_checklist_payload["items"][-1]["id"],
            "archive_evidence",
        )
        readiness_json = build_pilot_readiness_json_export(items)
        readiness_payload = json.loads(readiness_json.content)
        self.assertEqual(readiness_json.filename, "pilot-readiness.json")
        self.assertEqual(readiness_json.media_type, "application/json")
        self.assertEqual(readiness_payload["schema_version"], 2)
        self.assertEqual(readiness_payload["handoff_decision"]["status"], "warning")
        self.assertEqual(
            readiness_payload["handoff_decision"]["action_label"],
            "Review Attention",
        )
        self.assertEqual(readiness_payload["rollup"]["status"], "warning")
        self.assertEqual(readiness_payload["rollup"]["attention_items"], 1)
        self.assertEqual(readiness_payload["items"][0]["label"], "Web authentication")
        runbook_json = build_pilot_runbook_json_export(view)
        runbook_payload = json.loads(runbook_json.content)
        self.assertEqual(runbook_json.filename, "pilot-runbook.json")
        self.assertEqual(runbook_json.media_type, "application/json")
        self.assertEqual(runbook_payload, runbook_json.payload)
        self.assertEqual(runbook_payload["schema_version"], 4)
        self.assertEqual(runbook_payload["runbook_type"], "pilot")
        self.assertEqual(runbook_payload["smoke_test_item_count"], 6)
        self.assertEqual(runbook_payload["real_condition_item_count"], 8)
        self.assertEqual(runbook_payload["handoff_decision"]["status"], "warning")
        self.assertEqual(runbook_payload["sections"][0]["title"], "Setup")
        self.assertEqual(runbook_payload["readiness"]["status"], "warning")

        markdown = format_pilot_readiness_markdown(items)
        self.assertIn("# Pilot Readiness Summary", markdown)
        self.assertIn("- Handoff decision: `warning`", markdown)
        self.assertIn("- Handoff action: `Review Attention`", markdown)
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
        self.assertIn('@app.get("/pilot/real-condition.md"', web)
        self.assertIn("def pilot_real_condition_markdown(", web)
        self.assertIn("build_pilot_real_condition_export()", web)
        self.assertIn('@app.get("/pilot/real-condition.json"', web)
        self.assertIn("def pilot_real_condition_json(", web)
        self.assertIn("build_pilot_real_condition_json_export()", web)
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
        self.assertIn('@app.get("/pilot/final-handoff-checklist.md"', web)
        self.assertIn("def pilot_final_handoff_checklist_markdown(", web)
        self.assertIn("build_pilot_final_handoff_checklist_export(readiness_items)", web)
        self.assertIn('@app.get("/pilot/final-handoff-checklist.json"', web)
        self.assertIn("def pilot_final_handoff_checklist_json(", web)
        self.assertIn("build_pilot_final_handoff_checklist_json_export(readiness_items)", web)
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
                    "pilot-final-handoff-checklist.json",
                    "pilot-final-handoff-checklist.md",
                    "pilot-handoff-summary.json",
                    "pilot-handoff-summary.md",
                    "pilot-readiness.json",
                    "pilot-readiness.md",
                    "pilot-real-condition.json",
                    "pilot-real-condition.md",
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
            self.assertIn("- Schema version: `8`", verification.content)
            self.assertIn("- Readiness status: `ready`", verification.content)
            self.assertIn("- File count: `19`", verification.content)
            self.assertIn("- Automation files: `10`", verification.content)
            self.assertIn("- Human-readable files: `9`", verification.content)
            self.assertIn("- Manifest files: `1`", verification.content)
            self.assertIn("- Review files: `20`", verification.content)
            self.assertIn(
                "| File | Category | Kind | Review | Purpose | Bytes | SHA-256 |",
                verification.content,
            )
            self.assertIn(
                "| pilot-acceptance-checklist.json | automation | Automation JSON | 11 | Machine-readable beta acceptance checklist.",
                verification.content,
            )
            handoff_row = (
                "| pilot-handoff-summary.md | human | Human-readable Markdown | 1 | "
                "Compact handoff state and next actions."
            )
            acceptance_row = (
                "| pilot-acceptance-checklist.json | automation | Automation JSON | 11 | "
                "Machine-readable beta acceptance checklist."
            )
            delivery_row = (
                "| pilot-delivery-receipt.json | automation | Automation JSON | 17 | "
                "Machine-readable delivery receipt."
            )
            real_condition_row = (
                "| pilot-real-condition.json | automation | Automation JSON | 15 | "
                "Machine-readable real-condition trial checklist."
            )
            final_checklist_row = (
                "| pilot-final-handoff-checklist.json | automation | Automation JSON | 19 | "
                "Machine-readable final handoff checklist."
            )
            self.assertLess(
                verification.content.index(handoff_row),
                verification.content.index(acceptance_row),
            )
            self.assertLess(
                verification.content.index(acceptance_row),
                verification.content.index(real_condition_row),
            )
            self.assertLess(
                verification.content.index(real_condition_row),
                verification.content.index(delivery_row),
            )
            self.assertLess(
                verification.content.index(delivery_row),
                verification.content.index(final_checklist_row),
            )
            self.assertIn("## Review Order", verification.content)
            self.assertIn("1. `pilot-handoff-summary.md`", verification.content)
            self.assertIn("2. `pilot-handoff-summary.json`", verification.content)
            self.assertIn("4. `pilot-bundle-index.json`", verification.content)
            self.assertIn("5. `pilot-bundle-inventory.json`", verification.content)
            self.assertIn("7. `pilot-attention.json`", verification.content)
            self.assertIn("11. `pilot-acceptance-checklist.json`", verification.content)
            self.assertIn("13. `pilot-runbook.json`", verification.content)
            self.assertIn("15. `pilot-real-condition.json`", verification.content)
            self.assertIn("17. `pilot-delivery-receipt.json`", verification.content)
            self.assertIn("18. `pilot-final-handoff-checklist.md`", verification.content)
            self.assertIn("19. `pilot-final-handoff-checklist.json`", verification.content)
            self.assertIn("20. `manifest.json`", verification.content)
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
            self.assertEqual(verification_payload["schema_version"], 3)
            self.assertEqual(verification_payload["verification_type"], "pilot_evidence")
            self.assertEqual(verification_payload["manifest_schema_version"], 8)
            self.assertEqual(verification_payload["file_count"], 19)
            self.assertEqual(verification_payload["automation_file_count"], 10)
            self.assertEqual(verification_payload["human_file_count"], 9)
            self.assertEqual(verification_payload["manifest_file_count"], 1)
            self.assertEqual(verification_payload["review_file_count"], 20)
            self.assertIn("pilot-runbook.json", verification_payload["automation_files"])
            self.assertIn("pilot-real-condition.json", verification_payload["automation_files"])
            self.assertIn(
                "pilot-final-handoff-checklist.json",
                verification_payload["automation_files"],
            )
            self.assertIn("pilot-runbook.md", verification_payload["human_files"])
            self.assertIn("pilot-real-condition.md", verification_payload["human_files"])
            self.assertIn(
                "pilot-final-handoff-checklist.md",
                verification_payload["human_files"],
            )
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
                "pilot-real-condition.json",
            )
            self.assertEqual(
                verification_payload["review_order"][16],
                "pilot-delivery-receipt.json",
            )
            self.assertEqual(
                verification_payload["review_order"][18],
                "pilot-final-handoff-checklist.json",
            )
            self.assertEqual(verification_payload["checks"][0]["id"], "download_bundle")
            self.assertEqual(verification_payload["checks"][0]["status"], "manual")
            self.assertEqual(
                verification_payload["files"][0]["path"],
                "pilot-acceptance-checklist.json",
            )
            self.assertEqual(verification_payload["files"][0]["category"], "automation")
            self.assertEqual(verification_payload["files"][0]["kind"], "Automation JSON")
            self.assertEqual(verification_payload["files"][0]["review_order"], 11)
            self.assertEqual(
                verification_payload["files"][0]["purpose"],
                "Machine-readable beta acceptance checklist.",
            )
            self.assertEqual(manifest["schema_version"], 8)
            self.assertEqual(manifest["automation_file_count"], 10)
            self.assertEqual(manifest["human_file_count"], 9)
            self.assertEqual(manifest["manifest_file_count"], 1)
            self.assertEqual(manifest["review_file_count"], 20)
            self.assertEqual(
                manifest["automation_files"],
                [
                    "pilot-acceptance-checklist.json",
                    "pilot-attention.json",
                    "pilot-bundle-index.json",
                    "pilot-bundle-inventory.json",
                    "pilot-delivery-receipt.json",
                    "pilot-final-handoff-checklist.json",
                    "pilot-handoff-summary.json",
                    "pilot-readiness.json",
                    "pilot-real-condition.json",
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
                    "pilot-final-handoff-checklist.md",
                    "pilot-handoff-summary.md",
                    "pilot-readiness.md",
                    "pilot-real-condition.md",
                    "pilot-runbook.md",
                ],
            )
            self.assertEqual(manifest["bundle_type"], "pilot_evidence")
            self.assertEqual(manifest["context"], "Client Pilot")
            self.assertEqual(manifest["file_count"], 19)
            self.assertEqual(manifest["source"], "Pilot Runbook")
            self.assertEqual(manifest["files"][0]["category"], "automation")
            self.assertEqual(manifest["files"][0]["kind"], "Automation JSON")
            self.assertEqual(manifest["files"][0]["review_order"], 11)
            self.assertEqual(
                manifest["files"][0]["purpose"],
                "Machine-readable beta acceptance checklist.",
            )
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
                    "pilot-real-condition.md",
                    "pilot-real-condition.json",
                    "pilot-delivery-receipt.md",
                    "pilot-delivery-receipt.json",
                    "pilot-final-handoff-checklist.md",
                    "pilot-final-handoff-checklist.json",
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
                    "pilot-final-handoff-checklist.json",
                    "pilot-final-handoff-checklist.md",
                    "pilot-handoff-summary.json",
                    "pilot-handoff-summary.md",
                    "pilot-readiness.json",
                    "pilot-readiness.md",
                    "pilot-real-condition.json",
                    "pilot-real-condition.md",
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
                "# Pilot Real Condition Trial Checklist",
                archive.read("pilot-real-condition.md").decode("utf-8"),
            )
            archived_real_condition = json.loads(
                archive.read("pilot-real-condition.json").decode("utf-8")
            )
            self.assertEqual(archived_real_condition["real_condition_type"], "pilot")
            self.assertEqual(archived_real_condition["item_count"], 8)
            archived_index_markdown = archive.read(
                "pilot-bundle-index.md"
            ).decode("utf-8")
            self.assertIn("# Pilot Evidence Bundle Index", archived_index_markdown)
            self.assertIn(
                "| File | Category | Kind | Review | Purpose |",
                archived_index_markdown,
            )
            self.assertIn(
                "| manifest.json | manifest | Manifest JSON | 20 | File checksums",
                archived_index_markdown,
            )
            archived_index = json.loads(
                archive.read("pilot-bundle-index.json").decode("utf-8")
            )
            self.assertEqual(archived_index["index_type"], "pilot_evidence")
            self.assertEqual(archived_index["bundle_file_count"], 19)
            self.assertEqual(archived_index["schema_version"], 5)
            self.assertEqual(archived_index["automation_file_count"], 10)
            self.assertEqual(archived_index["human_file_count"], 9)
            self.assertEqual(archived_index["manifest_file_count"], 1)
            self.assertEqual(archived_index["review_order"][19]["category"], "manifest")
            self.assertEqual(archived_index["review_order"][19]["kind"], "Manifest JSON")
            archived_inventory = json.loads(
                archive.read("pilot-bundle-inventory.json").decode("utf-8")
            )
            self.assertEqual(archived_inventory["bundle_type"], "pilot_evidence")
            self.assertEqual(archived_inventory["expected_file_count"], 19)
            self.assertEqual(archived_inventory["schema_version"], 5)
            self.assertEqual(archived_inventory["automation_file_count"], 10)
            self.assertEqual(archived_inventory["human_file_count"], 9)
            self.assertEqual(archived_inventory["evidence_file_count"], 19)
            self.assertEqual(archived_inventory["manifest_file_count"], 1)
            self.assertEqual(archived_inventory["archive_file_count"], 20)
            self.assertGreater(
                archived_inventory["archive_total_size_bytes"],
                archived_inventory["evidence_total_size_bytes"],
            )
            self.assertEqual(
                archived_inventory["files"][0]["path"],
                "pilot-handoff-summary.md",
            )
            self.assertEqual(archived_inventory["files"][0]["category"], "human")
            self.assertEqual(
                archived_inventory["files"][0]["kind"],
                "Human-readable Markdown",
            )
            self.assertEqual(archived_inventory["files"][0]["review_order"], 1)
            archived_delivery_markdown = archive.read(
                "pilot-delivery-receipt.md"
            ).decode("utf-8")
            self.assertIn("# Pilot Delivery Receipt", archived_delivery_markdown)
            self.assertIn("- Automation files: `10`", archived_delivery_markdown)
            self.assertIn("| File | Category | Kind | Review | Purpose |", archived_delivery_markdown)
            self.assertIn(
                "| manifest.json | manifest | Manifest JSON | 20 | File checksums for integrity review. |",
                archived_delivery_markdown,
            )
            archived_delivery = json.loads(
                archive.read("pilot-delivery-receipt.json").decode("utf-8")
            )
            self.assertEqual(archived_delivery["delivery_type"], "pilot")
            self.assertEqual(archived_delivery["schema_version"], 5)
            self.assertEqual(archived_delivery["automation_file_count"], 10)
            self.assertEqual(archived_delivery["human_file_count"], 9)
            self.assertEqual(archived_delivery["manifest_file_count"], 1)
            self.assertEqual(archived_delivery["delivered_file_count"], 19)
            self.assertEqual(
                archived_delivery["delivered_file_details"][-1]["category"],
                "manifest",
            )
            self.assertEqual(
                archived_delivery["delivered_file_details"][-1]["kind"],
                "Manifest JSON",
            )
            self.assertEqual(archived_delivery["readiness"]["status"], "ready")
            archived_handoff_markdown = archive.read(
                "pilot-handoff-summary.md"
            ).decode("utf-8")
            self.assertIn("# Pilot Handoff Summary", archived_handoff_markdown)
            self.assertIn("- Automation files: `10`", archived_handoff_markdown)
            self.assertIn("| File | Category | Kind | Review | Purpose |", archived_handoff_markdown)
            self.assertIn(
                "| manifest.json | manifest | Manifest JSON | 20 | File checksums for integrity review. |",
                archived_handoff_markdown,
            )
            archived_handoff = json.loads(
                archive.read("pilot-handoff-summary.json").decode("utf-8")
            )
            self.assertEqual(archived_handoff["handoff_type"], "pilot")
            self.assertEqual(archived_handoff["schema_version"], 6)
            self.assertEqual(archived_handoff["handoff_decision"]["status"], "ready")
            self.assertEqual(archived_handoff["automation_file_count"], 10)
            self.assertEqual(archived_handoff["human_file_count"], 9)
            self.assertEqual(archived_handoff["manifest_file_count"], 1)
            self.assertEqual(archived_handoff["handoff_file_count"], 19)
            self.assertEqual(
                archived_handoff["handoff_file_details"][-1]["category"],
                "manifest",
            )
            self.assertEqual(
                archived_handoff["handoff_file_details"][-1]["kind"],
                "Manifest JSON",
            )
            self.assertEqual(archived_handoff["readiness"]["status"], "ready")
            archived_readiness = json.loads(
                archive.read("pilot-readiness.json").decode("utf-8")
            )
            self.assertEqual(archived_readiness["schema_version"], 2)
            self.assertEqual(archived_readiness["handoff_decision"]["status"], "ready")
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
            self.assertEqual(archived_runbook["schema_version"], 4)
            self.assertEqual(archived_runbook["smoke_test_item_count"], 6)
            self.assertEqual(archived_runbook["real_condition_item_count"], 8)
            self.assertEqual(archived_runbook["handoff_decision"]["status"], "ready")
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
        css_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_static"
            / "app.css"
        )
        template = template_path.read_text(encoding="utf-8")
        css = css_path.read_text(encoding="utf-8")

        for anchor in [
            "mission-go-no-go",
            "mission-cockpit",
            "service-readiness",
            "action-roadmap",
            "mission-readiness",
            "scan-launch",
            "scan-plan",
            "run-monitor",
            "vulnerabilities",
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
            "view.go_no_go.decision",
            "view.cockpit.ready_step_count",
            "view.cockpit.total_step_count",
            "view.cockpit.selected_check_count",
            "view.cockpit.ready_check_count",
            "view.cockpit.blocked_check_count",
            "view.action_roadmap|length",
            "view.readiness_items|length",
            "view.scan_launch.ready_count",
            "view.scan_plans|length",
            "view.scan_runs|length",
            "view.vulnerability_matches|length",
            "view.check_selection|length",
            "view.reports|length",
            "view.activity_events|length",
            "view.scope|length",
            "view.counter_test_items|length",
            "view.findings|length",
        ]:
            self.assertIn(f"{{{{ {counter} }}}}", template)

        self.assertIn("Open Console", template)
        self.assertIn('/missions/{{ view.mission.id }}/console', template)
        self.assertIn("mission-detail-hero", template)
        self.assertIn('aria-label="Mission summary"', template)
        self.assertIn("Tableau de session", template)
        self.assertIn("Technician Cockpit", template)
        self.assertIn("Mission Go/No-Go", template)
        self.assertIn("Mission Focus", template)
        self.assertIn('aria-label="Mission focus"', template)
        self.assertIn("view.cockpit.next_action", template)
        self.assertIn("view.cockpit.next_action_href", template)
        self.assertIn("view.cockpit.next_action_label", template)
        self.assertIn("view.scan_launch.ready_count", template)
        self.assertIn("view.customer_handoff.ready_count", template)
        self.assertIn("view.customer_handoff.total_count", template)
        self.assertIn("mission-focus-grid", template)
        self.assertIn("mission-focus-actions", template)
        self.assertIn(".detail-hero", css)
        self.assertIn(".client-detail-hero", css)
        self.assertIn(".mission-detail-hero", css)
        self.assertIn("view.go_no_go.status", template)
        self.assertIn("view.go_no_go.detail", template)
        self.assertIn("view.go_no_go.action_href", template)
        self.assertIn("view.go_no_go.action_label", template)
        self.assertIn("view.go_no_go.ready_count", template)
        self.assertIn("view.go_no_go.total_count", template)
        self.assertIn("view.go_no_go.items", template)
        self.assertIn('aria-label="Mission go/no-go checklist"', template)
        self.assertIn("mission-go-no-go-grid", template)
        self.assertIn("Scan Launch Center", template)
        self.assertIn("view.scan_launch.status", template)
        self.assertIn("view.scan_launch.detail", template)
        self.assertIn("view.scan_launch.action_href", template)
        self.assertIn("view.scan_launch.ready_services", template)
        self.assertIn("view.scan_launch.blocked_services", template)
        self.assertIn("view.scan_launch.checklist", template)
        self.assertIn('aria-label="Scan launch services"', template)
        self.assertIn("<caption class=\"sr-only\">Service pre-launch checklist</caption>", template)
        self.assertIn("check-target-guidance", template)
        self.assertIn("check.target_status", template)
        self.assertIn("check.target_requirement", template)
        self.assertIn("check.target_summary", template)
        self.assertIn("check.matching_scope_count", template)
        self.assertIn("item.command_count", template)
        self.assertIn("item.action_label", template)
        self.assertIn("Each ready check still requires explicit authorization confirmation", template)
        self.assertIn("live-trial-guardrails", template)
        self.assertIn('aria-label="Live trial guardrails"', template)
        self.assertIn("Live Trial Guardrails", template)
        self.assertIn("Run inside the approved customer window", template)
        self.assertIn("Keep this page open so the Run Monitor", template)
        self.assertIn("Pause if the customer reports impact", template)
        self.assertIn("Generate PDF, JSON, and package exports", template)
        self.assertIn("view.scan_run_outcome.status", template)
        self.assertIn("view.scan_run_outcome.title", template)
        self.assertIn("view.scan_run_outcome.detail", template)
        self.assertIn("view.scan_run_outcome.run_count", template)
        self.assertIn("view.scan_run_outcome.finding_count", template)
        self.assertIn("view.scan_run_outcome.evidence_count", template)
        self.assertIn("view.scan_run_outcome.action_href", template)
        self.assertIn("view.scan_run_outcome.action_label", template)
        self.assertIn("run-outcome-summary", template)
        self.assertIn("Run monitor control center", template)
        self.assertIn("Centre de suivi des tests lances", template)
        self.assertIn('aria-label="Run monitor metrics"', template)
        self.assertIn('aria-label="Run monitor filters"', template)
        self.assertIn("data-run-search", template)
        self.assertIn("data-run-filter", template)
        self.assertIn("data-run-card", template)
        self.assertIn("data-run-table-row", template)
        self.assertIn("data-run-visible-count", template)
        self.assertIn("data-run-empty", template)
        self.assertIn("data-run-status", template)
        self.assertIn("data-run-has-findings", template)
        self.assertIn("data-run-search-text", template)
        self.assertIn("Relancer un service pret", template)
        self.assertIn(".run-monitor-panel", css)
        self.assertIn(".run-monitor-controls", css)
        self.assertIn(".run-filter.is-active", css)
        self.assertIn(".run-monitor-summary-grid", css)
        self.assertIn('aria-label="Scan run follow-up cards"', template)
        self.assertIn("run-monitor-grid", template)
        self.assertIn("run-monitor-card", template)
        self.assertIn("run.status_title", template)
        self.assertIn("run.summary", template)
        self.assertIn("run.evidence_summary", template)
        self.assertIn("run.action_href", template)
        self.assertIn("No run recorded yet", template)
        self.assertIn("Mission Roadmap", template)
        self.assertIn("Mission quick read", template)
        self.assertIn("view.quick_read.decision", template)
        self.assertIn("view.quick_read.immediate_action", template)
        self.assertIn("view.quick_read.priority_focus", template)
        self.assertIn("view.quick_read.next_counter_test", template)
        self.assertIn("view.quick_read.action_href", template)
        self.assertIn("quick-read-panel", template)
        self.assertIn("quick-read-grid", template)
        self.assertIn("view.action_roadmap", template)
        self.assertIn('aria-label="Mission action roadmap"', template)
        self.assertIn('aria-label="Mission roadmap exports"', template)
        self.assertIn('/missions/{{ view.mission.id }}/roadmap/markdown', template)
        self.assertIn('/missions/{{ view.mission.id }}/roadmap/json', template)
        self.assertIn("action-step-{{ step.status }}", template)
        self.assertIn("step.action_href", template)
        self.assertIn("view.cockpit.steps", template)
        self.assertIn("view.cockpit.services", template)
        self.assertIn("Service readiness center", template)
        self.assertIn("Centre de preparation des services", template)
        self.assertIn('aria-label="Service readiness center"', template)
        self.assertIn('aria-label="Service readiness metrics"', template)
        self.assertIn('aria-label="Service readiness filters"', template)
        self.assertIn('aria-label="Service execution guard"', template)
        self.assertIn("data-service-search", template)
        self.assertIn("data-service-filter", template)
        self.assertIn("data-service-row", template)
        self.assertIn("data-service-grid", template)
        self.assertIn("data-service-visible-count", template)
        self.assertIn("data-service-empty", template)
        self.assertIn("data-service-status", template)
        self.assertIn("data-service-selected", template)
        self.assertIn("data-service-search-text", template)
        self.assertIn("Garde-fou execution", template)
        self.assertIn("Un service pret ne lance rien automatiquement.", template)
        self.assertIn(".service-readiness-panel", css)
        self.assertIn(".service-readiness-controls", css)
        self.assertIn(".service-filter.is-active", css)
        self.assertIn(".service-readiness-guard", css)
        self.assertIn("service.run_status", template)
        self.assertIn("service.run_detail", template)
        self.assertIn("service-run-summary", template)
        self.assertIn('aria-label="Technician cockpit metrics"', template)
        self.assertIn('aria-label="Mission workflow cockpit"', template)
        self.assertIn('aria-label="Selected service cockpit"', template)
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
        self.assertIn('action="/missions/{{ view.mission.id }}/scan-runs"', template)
        self.assertIn('name="check" value="{{ plan.check }}"', template)
        self.assertIn('name="execute_confirm"', template)
        self.assertIn("prelaunch-decision", template)
        self.assertIn("Ready for guarded launch", template)
        self.assertIn("Written authorization is recorded for this mission.", template)
        self.assertIn("Approved scope contains target(s) matching this service.", template)
        self.assertIn("will run exactly as listed above", template)
        self.assertIn("Execution may contact target systems", template)
        self.assertIn("I confirm written authorization, approved scope", template)
        self.assertIn("Run {{ plan.label }}", template)
        self.assertIn("Launch blocked", template)
        self.assertIn("Review readiness blockers", template)
        self.assertIn(".live-trial-guardrails", css)
        self.assertIn(".prelaunch-decision", css)
        self.assertIn(".prelaunch-blocked", css)
        self.assertIn("Guarded execution", template)
        self.assertIn("CLI and web executions", template)
        self.assertIn("Known Vulnerability Correlation", template)
        self.assertIn("view.report_delivery.status", template)
        self.assertIn("view.report_delivery.detail", template)
        self.assertIn("view.report_delivery.ready_count", template)
        self.assertIn("view.report_delivery.total_count", template)
        self.assertIn("view.report_delivery.items", template)
        self.assertIn("Report delivery checklist", template)
        self.assertIn("report-delivery-summary", template)
        self.assertIn("Customer handoff summary", template)
        self.assertIn("view.customer_handoff.status", template)
        self.assertIn("view.customer_handoff.title", template)
        self.assertIn("view.customer_handoff.detail", template)
        self.assertIn("view.customer_handoff.items", template)
        self.assertIn("view.customer_handoff.ready_count", template)
        self.assertIn("view.customer_handoff.total_count", template)
        self.assertIn("handoff-panel", template)
        self.assertIn("handoff-grid", template)
        self.assertIn("view.scope_intake.status", template)
        self.assertIn("view.scope_intake.detail", template)
        self.assertIn("view.scope_intake.approved_count", template)
        self.assertIn("view.scope_intake.draft_count", template)
        self.assertIn("view.scope_intake.excluded_count", template)
        self.assertIn("view.scope_intake.items", template)
        self.assertIn("Scope intake guide", template)
        self.assertIn("scope-intake-summary", template)
        self.assertIn("scope-intake-grid", template)
        self.assertIn("view.vulnerability_catalog_count", template)
        self.assertIn("view.vulnerability_summary.status", template)
        self.assertIn("view.vulnerability_summary.detail", template)
        self.assertIn("view.vulnerability_summary.match_count", template)
        self.assertIn("view.vulnerability_summary.known_exploited_count", template)
        self.assertIn("view.vulnerability_summary.critical_or_high_count", template)
        self.assertIn("view.vulnerability_summary.stored_candidate_count", template)
        self.assertIn("vulnerability-summary", template)
        self.assertIn("view.vulnerability_review_items", template)
        self.assertIn("CVE/KEV review checklist", template)
        self.assertIn("vulnerability-review-grid", template)
        self.assertIn("Import reviewed CVE/KEV catalog", template)
        self.assertIn('name="catalog_json"', template)
        self.assertIn('aria-label="Import vulnerability catalog"', template)
        self.assertIn('action="/missions/{{ view.mission.id }}/vulnerabilities/catalog"', template)
        self.assertIn('aria-label="CVE/KEV candidate review cards"', template)
        self.assertIn("vulnerability-card-grid", template)
        self.assertIn("item.priority_label", template)
        self.assertIn("item.priority_reason", template)
        self.assertIn("item.risk", template)
        self.assertIn("item.counter_test", template)
        self.assertIn("item.validation_steps", template)
        self.assertIn("Validation checklist before storing the finding", template)
        self.assertIn("Store Candidate Findings", template)
        self.assertIn(
            'action="/missions/{{ view.mission.id }}/vulnerabilities/correlate"',
            template,
        )
        self.assertIn('aria-label="Mission export integrity details"', template)
        self.assertIn("view.mission_export.checked_files", template)
        self.assertIn("view.mission_export.missing_count", template)
        self.assertIn("view.mission_export.mismatched_count", template)
        self.assertIn("view.mission_export.unexpected_count", template)
        self.assertIn("view.mission_export.has_integrity_issues", template)
        self.assertIn("view.mission_export.handoff_status", template)
        self.assertIn("view.mission_export.handoff_action", template)
        self.assertIn("view.mission_export.handoff_detail", template)
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
        self.assertEqual(view.onboarding_ready_count, 6)
        self.assertEqual(view.onboarding_total_count, 6)
        self.assertEqual(
            [step.label for step in view.technician_workflow_steps],
            [
                "1. Create audit",
                "2. Authorize scope",
                "3. Select services",
                "4. Launch guarded checks",
                "5. Review findings",
                "6. Reports and handoff",
            ],
        )
        workflow = {step.label: step for step in view.technician_workflow_steps}
        self.assertEqual(workflow["1. Create audit"].status, "ready")
        self.assertEqual(workflow["2. Authorize scope"].status, "ready")
        self.assertEqual(workflow["3. Select services"].status, "ready")
        self.assertEqual(workflow["4. Launch guarded checks"].status, "warning")
        self.assertEqual(workflow["5. Review findings"].status, "ready")
        self.assertEqual(workflow["6. Reports and handoff"].status, "ready")
        self.assertEqual(workflow["1. Create audit"].action_href, "/wizard")
        self.assertEqual(workflow["6. Reports and handoff"].action_href, "/pilot")
        onboarding = {item.label: item for item in view.onboarding_steps}
        self.assertEqual(onboarding["Client record"].status, "ready")
        self.assertEqual(onboarding["Mission setup"].status, "ready")
        self.assertEqual(onboarding["Authorization"].status, "ready")
        self.assertEqual(onboarding["Approved scope"].status, "ready")
        self.assertEqual(onboarding["Check selection"].status, "ready")
        self.assertEqual(onboarding["Finding review"].status, "ready")
        self.assertEqual(
            view.onboarding_next_action,
            "Pilot workflow is ready for evidence handoff review.",
        )
        self.assertEqual(view.onboarding_next_action_label, "Open Pilot")
        self.assertEqual(view.onboarding_next_action_href, "/pilot")
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

    def test_dashboard_onboarding_guides_empty_and_partial_workspaces(self) -> None:
        empty_store = JsonStore(clean_data_dir("web-ui-dashboard-onboarding-empty"))
        empty_view = build_dashboard_view(empty_store)

        self.assertEqual(empty_view.onboarding_ready_count, 0)
        self.assertEqual(empty_view.onboarding_total_count, 6)
        self.assertEqual(empty_view.onboarding_next_action_label, "Create Client")
        self.assertEqual(empty_view.onboarding_next_action_href, "#new-client")
        empty_steps = {item.label: item for item in empty_view.onboarding_steps}
        self.assertEqual(empty_steps["Client record"].status, "warning")
        self.assertEqual(empty_steps["Mission setup"].status, "blocked")
        self.assertEqual(empty_steps["Finding review"].status, "blocked")
        empty_workflow = {item.label: item for item in empty_view.technician_workflow_steps}
        self.assertEqual(empty_workflow["1. Create audit"].status, "blocked")
        self.assertEqual(empty_workflow["1. Create audit"].action_href, "/wizard")
        self.assertEqual(empty_workflow["2. Authorize scope"].status, "blocked")
        self.assertEqual(empty_workflow["4. Launch guarded checks"].status, "blocked")

        store = JsonStore(clean_data_dir("web-ui-dashboard-onboarding-partial"))
        client = store.create_client(Client(name="Client Onboarding"))
        mission = store.create_mission(Mission(client_id=client.id, name="Pilot"))

        view = build_dashboard_view(store)
        steps = {item.label: item for item in view.onboarding_steps}

        self.assertEqual(view.onboarding_ready_count, 2)
        self.assertEqual(view.onboarding_next_action_label, "Review Setup")
        self.assertEqual(
            view.onboarding_next_action_href,
            f"/missions/{mission.id}#mission-setup",
        )
        self.assertEqual(steps["Client record"].status, "ready")
        self.assertEqual(steps["Mission setup"].status, "ready")
        self.assertEqual(steps["Authorization"].status, "warning")
        self.assertEqual(steps["Approved scope"].status, "blocked")
        self.assertEqual(steps["Check selection"].status, "blocked")
        self.assertEqual(steps["Finding review"].status, "blocked")
        workflow = {item.label: item for item in view.technician_workflow_steps}
        self.assertEqual(workflow["1. Create audit"].status, "ready")
        self.assertEqual(workflow["2. Authorize scope"].status, "blocked")
        self.assertEqual(workflow["2. Authorize scope"].action_href, f"/missions/{mission.id}#mission-setup")
        self.assertEqual(workflow["3. Select services"].status, "blocked")

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
                audit_type=AuditType.INTERNAL,
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
        store.add_scan_run(
            ScanRun(
                mission_id=mission.id,
                check=AuditCheck.NMAP,
                status=ScanRunStatus.COMPLETED,
                started_at=datetime(2026, 5, 10, 9, 30, tzinfo=timezone.utc),
                command_count=1,
                finding_count=2,
                evidence_paths=["runs/mission/evidence/nmap.xml"],
            )
        )

        view = build_mission_view(store, mission.id)

        self.assertEqual(view.mission.client_name, "Client Y")
        self.assertEqual(view.session_dashboard.mode, "internal")
        self.assertEqual(view.session_dashboard.status, "warning")
        self.assertGreaterEqual(view.session_dashboard.progress_percent, 35)
        self.assertLess(view.session_dashboard.progress_percent, 100)
        self.assertEqual(view.session_dashboard.selected_service_count, 3)
        self.assertEqual(view.session_dashboard.completed_service_count, 1)
        self.assertEqual(view.session_dashboard.failed_service_count, 0)
        self.assertEqual(view.session_dashboard.run_count, 1)
        self.assertEqual(view.session_dashboard.finding_count, 1)
        self.assertEqual(view.session_dashboard.report_count, 0)
        self.assertIn("unknown:ip:192.0.2.10", view.session_dashboard.target_summary)
        self.assertIn("Nmap", view.session_dashboard.selected_services)
        self.assertIn("Execution", [step.label for step in view.session_dashboard.steps])
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
        self.assertEqual(view.quick_read.status, "warning")
        self.assertEqual(view.quick_read.decision, "Action prioritaire requise")
        self.assertEqual(view.quick_read.immediate_action, "Restrict access to trusted sources.")
        self.assertIn("Open administrative service", view.quick_read.priority_focus)
        self.assertEqual(view.quick_read.next_counter_test, "Run the approved Nmap plan again.")
        self.assertEqual(view.quick_read.action_label, "Review Findings")
        self.assertEqual(view.quick_read.action_href, "#findings")
        self.assertEqual(view.scope[0].status, "approved")
        self.assertEqual(view.findings[0].severity, "high")
        self.assertEqual(view.findings[0].review_note, "")
        self.assertEqual(view.findings[0].related_remediations[0].id, "rem_rdp_restrict_exposure")
        self.assertEqual(view.reports, [])
        self.assertIsNone(view.mission_export)
        self.assertEqual(view.customer_handoff.status, "warning")
        self.assertEqual(view.customer_handoff.title, "Customer handoff needs review")
        self.assertEqual(view.customer_handoff.ready_count, 2)
        self.assertEqual(view.customer_handoff.total_count, 5)
        handoff_items = {item.label: item for item in view.customer_handoff.items}
        self.assertEqual(handoff_items["Customer PDF"].status, "missing")
        self.assertEqual(handoff_items["JSON tracking"].status, "missing")
        self.assertEqual(handoff_items["Mission package"].status, "missing")
        self.assertEqual(handoff_items["Recipients"].status, "ready")
        self.assertEqual(handoff_items["Recipients"].detail, "direction@example.invalid")
        self.assertEqual(handoff_items["Evidence retention"].status, "ready")
        self.assertEqual(handoff_items["Evidence retention"].detail, "60 day(s) recorded.")
        self.assertEqual(len(view.readiness_items), 5)
        self.assertEqual(view.cockpit.status, "warning")
        self.assertEqual(view.cockpit.next_action, "Review 1 new finding(s).")
        self.assertEqual(view.cockpit.next_action_label, "Review Findings")
        self.assertEqual(view.cockpit.next_action_href, "#findings")
        self.assertEqual(view.cockpit.ready_step_count, 3)
        self.assertEqual(view.cockpit.total_step_count, 5)
        self.assertEqual(view.cockpit.approved_scope_count, 1)
        self.assertEqual(view.cockpit.selected_check_count, 3)
        self.assertEqual(view.cockpit.ready_check_count, 1)
        self.assertEqual(view.cockpit.blocked_check_count, 2)
        self.assertEqual(view.cockpit.report_count, 0)
        self.assertEqual(view.cockpit.handoff_status, "missing")
        self.assertEqual(view.scan_launch.status, "ready")
        self.assertEqual(view.scan_launch.ready_count, 1)
        self.assertEqual(view.scan_launch.blocked_count, 2)
        self.assertEqual(view.scan_launch.run_count, 1)
        self.assertEqual(view.scan_launch.ready_services, ["Nmap"])
        self.assertEqual(view.scan_launch.blocked_services, ["HTTP Headers", "DNS/Mail"])
        self.assertEqual(view.scan_launch.action_label, "Open Ready Checks")
        self.assertEqual(view.scan_launch.action_href, "#scan-plan")
        self.assertEqual(
            [(item.label, item.status, item.command_count) for item in view.scan_launch.checklist],
            [
                ("Nmap", "ready", 1),
                ("HTTP Headers", "blocked", 0),
                ("DNS/Mail", "blocked", 0),
            ],
        )
        self.assertEqual(
            view.scan_launch.checklist[0].detail,
            "Commands are visible and explicit confirmation remains required.",
        )
        self.assertEqual(view.scan_launch.checklist[0].action_label, "Review Commands")
        self.assertEqual(view.scan_launch.checklist[1].action_href, "#mission-readiness")
        self.assertEqual(
            [step.label for step in view.cockpit.steps],
            ["Authorization", "Périmètre", "Services", "Lancement", "Constats", "Livrables"],
        )
        self.assertEqual(
            [step.label for step in view.action_roadmap],
            [
                "Authorization",
                "Targets and services",
                "Guarded launch",
                "CVE/KEV review",
                "Reports and handoff",
            ],
        )
        self.assertEqual(
            [step.status for step in view.action_roadmap],
            ["ready", "ready", "ready", "missing", "blocked"],
        )
        self.assertEqual(view.action_roadmap[2].action_href, "#run-monitor")
        self.assertIn("1 run(s) recorded", view.action_roadmap[2].detail)
        self.assertEqual(view.action_roadmap[4].action_href, "#reports")
        self.assertEqual(view.check_selection[0].value, "nmap")
        self.assertTrue(view.check_selection[0].selected)
        self.assertEqual(view.scan_plans[0].label, "Nmap")
        self.assertEqual(view.scan_plans[0].status, "ready")
        service_statuses = {service.value: service.status for service in view.cockpit.services}
        service_run_statuses = {
            service.value: service.run_status for service in view.cockpit.services
        }
        service_run_details = {
            service.value: service.run_detail for service in view.cockpit.services
        }
        self.assertEqual(service_statuses["nmap"], "ready")
        self.assertEqual(service_run_statuses["nmap"], "completed")
        self.assertIn("1 commande(s)", service_run_details["nmap"])
        self.assertIn("2 constat(s)", service_run_details["nmap"])
        self.assertEqual(service_statuses["http_headers"], "blocked")
        self.assertEqual(service_statuses["dns_mail"], "blocked")
        self.assertEqual(service_statuses["tls"], "none")
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
        by_check = {item.value: item for item in view.check_selection}
        self.assertEqual(by_check["dns_mail"].target_status, "blocked")
        self.assertEqual(by_check["dns_mail"].matching_scope_count, 0)
        self.assertIn("approved domain scope", by_check["dns_mail"].target_requirement)
        self.assertIn("Add approved domain scope", by_check["dns_mail"].target_summary)
        self.assertEqual([plan.label for plan in view.scan_plans], ["DNS/Mail"])

    def test_mission_view_shows_check_target_guidance(self) -> None:
        store = JsonStore(clean_data_dir("web-ui-check-target-guidance"))
        client = store.create_client(Client(name="Client Check Targets"))
        mission = store.create_mission(
            Mission(
                client_id=client.id,
                name="Target Audit",
                selected_checks=[AuditCheck.HTTP_HEADERS, AuditCheck.SMB],
            )
        )
        store.add_scope_item(
            mission.id,
            ScopeItem(type=ScopeType.URL, value="https://portal.example.test", approved=True),
        )
        store.add_scope_item(
            mission.id,
            ScopeItem(type=ScopeType.HOST, value="fs01.example.test", approved=True),
        )

        view = build_mission_view(store, mission.id)
        by_check = {item.value: item for item in view.check_selection}

        self.assertEqual(by_check["http_headers"].target_status, "ready")
        self.assertEqual(by_check["http_headers"].matching_scope_count, 1)
        self.assertIn("https://portal.example.test", by_check["http_headers"].target_summary)
        self.assertEqual(by_check["smb"].target_status, "ready")
        self.assertEqual(by_check["smb"].matching_scope_count, 1)
        self.assertIn("fs01.example.test", by_check["smb"].target_summary)
        self.assertEqual(by_check["dns_mail"].target_status, "missing")
        self.assertIn("Add approved domain scope", by_check["dns_mail"].target_summary)

    def test_mission_view_shows_scope_intake_guidance(self) -> None:
        store = JsonStore(clean_data_dir("web-ui-scope-intake"))
        client = store.create_client(Client(name="Client Scope Intake"))
        mission = store.create_mission(
            Mission(
                client_id=client.id,
                name="Scope Intake Audit",
                selected_checks=[
                    AuditCheck.HTTP_HEADERS,
                    AuditCheck.DNS_MAIL,
                    AuditCheck.SMB,
                ],
            )
        )
        store.add_scope_item(
            mission.id,
            ScopeItem(
                type=ScopeType.URL,
                value="https://portal.example.test",
                approved=True,
            ),
        )
        store.add_scope_item(
            mission.id,
            ScopeItem(type=ScopeType.HOST, value="fs01.example.test"),
        )

        view = build_mission_view(store, mission.id)
        items = {item.scope_type: item for item in view.scope_intake.items}

        self.assertEqual(view.scope_intake.status, "warning")
        self.assertEqual(view.scope_intake.approved_count, 1)
        self.assertEqual(view.scope_intake.draft_count, 1)
        self.assertEqual(view.scope_intake.excluded_count, 0)
        self.assertEqual(items["url"].status, "ready")
        self.assertEqual(items["url"].matching_scope_count, 1)
        self.assertIn("HTTP headers", items["url"].services)
        self.assertEqual(items["domain"].status, "blocked")
        self.assertIn("DNS/Mail", items["domain"].services)
        self.assertIn("SMB basic", items["domain"].services)
        self.assertEqual(items["host"].status, "blocked")
        self.assertIn("SMB basic", items["host"].services)
        self.assertEqual(items["cidr"].status, "missing")

    def test_mission_view_includes_scan_runs(self) -> None:
        store = JsonStore(clean_data_dir("web-ui-runs"))
        client = store.create_client(Client(name="Client Runs"))
        mission = store.create_mission(Mission(client_id=client.id, name="Run Audit"))
        store.add_finding(
            mission.id,
            Finding(
                title="Missing security header",
                severity=Severity.MEDIUM,
                affected_asset="https://example.test",
                category="http",
                source_module="http_headers",
                proof="X-Frame-Options is missing.",
                risk="Clickjacking protection is reduced.",
                remediation="Add a frame-ancestors CSP or X-Frame-Options header.",
                counter_test="Re-run the HTTP headers check.",
                confidence=0.8,
            ),
        )
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
        self.assertEqual(view.scan_runs[0].label, "HTTP headers")
        self.assertEqual(view.scan_runs[0].status_title, "Findings imported")
        self.assertEqual(view.scan_runs[0].evidence_summary, "1 evidence file(s)")
        self.assertEqual(view.scan_runs[0].action_label, "Review Findings")
        self.assertEqual(view.scan_runs[0].action_href, "#findings")
        self.assertIn(
            "HTTP headers completed with 2 finding(s)",
            view.scan_runs[0].summary,
        )
        self.assertEqual(view.scan_run_outcome.status, "completed")
        self.assertEqual(view.scan_run_outcome.title, "Latest run: HTTP headers")
        self.assertIn(
            "1 command(s), 2 finding(s), 1 evidence file(s)",
            view.scan_run_outcome.detail,
        )
        self.assertEqual(view.scan_run_outcome.run_count, 1)
        self.assertEqual(view.scan_run_outcome.finding_count, 1)
        self.assertEqual(view.scan_run_outcome.evidence_count, 1)
        self.assertEqual(view.scan_run_outcome.action_label, "Review Findings")
        self.assertEqual(view.scan_run_outcome.action_href, "#findings")

    def test_mission_view_summarizes_missing_scan_runs(self) -> None:
        store = JsonStore(clean_data_dir("web-ui-runs-missing"))
        client = store.create_client(Client(name="Client Missing Runs"))
        mission = store.create_mission(Mission(client_id=client.id, name="Run Audit"))

        view = build_mission_view(store, mission.id)

        self.assertEqual(view.scan_run_outcome.status, "missing")
        self.assertEqual(view.scan_run_outcome.title, "No run recorded yet")
        self.assertEqual(view.scan_run_outcome.action_label, "Open Scan Plan")
        self.assertEqual(view.scan_run_outcome.action_href, "#scan-plan")
        self.assertEqual(view.scan_run_outcome.run_count, 0)
        self.assertEqual(view.scan_run_outcome.finding_count, 0)
        self.assertEqual(view.scan_run_outcome.evidence_count, 0)

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

    def test_mission_view_summarizes_missing_report_delivery(self) -> None:
        store = JsonStore(clean_data_dir("web-ui-report-delivery-missing-data"))
        reports_dir = clean_data_dir("web-ui-report-delivery-missing-reports")
        client = store.create_client(Client(name="Client Reports"))
        mission = store.create_mission(Mission(client_id=client.id, name="Report Audit"))

        view = build_mission_view(store, mission.id, reports_dir=reports_dir)
        items = {item.label: item for item in view.report_delivery.items}

        self.assertEqual(view.report_delivery.status, "missing")
        self.assertEqual(view.report_delivery.ready_count, 0)
        self.assertEqual(view.report_delivery.total_count, 6)
        self.assertEqual(view.report_delivery.action_label, "Generate Reports")
        self.assertEqual(items["PDF customer report"].status, "missing")
        self.assertEqual(items["Mission ZIP package"].status, "missing")
        handoff_items = {item.label: item for item in view.customer_handoff.items}
        self.assertEqual(view.customer_handoff.status, "missing")
        self.assertEqual(view.customer_handoff.title, "Customer handoff not ready")
        self.assertEqual(view.customer_handoff.ready_count, 0)
        self.assertEqual(view.customer_handoff.total_count, 5)
        self.assertEqual(view.customer_handoff.action_label, "Generate Reports")
        self.assertEqual(handoff_items["Customer PDF"].status, "missing")
        self.assertEqual(handoff_items["JSON tracking"].status, "missing")
        self.assertEqual(handoff_items["Mission package"].status, "missing")
        self.assertEqual(handoff_items["Recipients"].status, "missing")
        self.assertEqual(handoff_items["Evidence retention"].status, "missing")

    def test_mission_view_summarizes_ready_report_delivery(self) -> None:
        store = JsonStore(clean_data_dir("web-ui-report-delivery-ready-data"))
        reports_dir = clean_data_dir("web-ui-report-delivery-ready-reports")
        client = store.create_client(Client(name="Client Reports Ready"))
        mission = store.create_mission(
            Mission(
                client_id=client.id,
                name="Report Audit",
                authorization_reference="AUTH-REPORT",
                report_recipients="client-report@example.invalid",
                evidence_retention_days=90,
            )
        )
        generate_authorization_brief(store, mission.id, reports_dir)
        generate_web_reports(store, mission.id, reports_dir)
        generate_mission_export(store, mission.id, reports_dir)

        view = build_mission_view(store, mission.id, reports_dir=reports_dir)
        items = {item.label: item for item in view.report_delivery.items}

        self.assertEqual(view.report_delivery.status, "ready")
        self.assertEqual(view.report_delivery.ready_count, 6)
        self.assertEqual(view.report_delivery.total_count, 6)
        self.assertEqual(view.report_delivery.action_label, "Download Package")
        self.assertEqual(items["Authorization brief"].status, "ready")
        self.assertEqual(items["PDF customer report"].status, "ready")
        self.assertEqual(items["Mission ZIP package"].status, "ready")
        handoff_items = {item.label: item for item in view.customer_handoff.items}
        self.assertEqual(view.customer_handoff.status, "ready")
        self.assertEqual(view.customer_handoff.title, "Customer handoff ready")
        self.assertEqual(view.customer_handoff.ready_count, 5)
        self.assertEqual(view.customer_handoff.total_count, 5)
        self.assertEqual(view.customer_handoff.action_label, "Download Package")
        self.assertEqual(handoff_items["Customer PDF"].status, "ready")
        self.assertEqual(handoff_items["JSON tracking"].status, "ready")
        self.assertEqual(handoff_items["Mission package"].status, "ready")
        self.assertEqual(handoff_items["Recipients"].detail, "client-report@example.invalid")
        self.assertEqual(handoff_items["Evidence retention"].detail, "90 day(s) recorded.")

    def test_mission_view_go_no_go_blocks_missing_authorization_and_reports(self) -> None:
        store = JsonStore(clean_data_dir("web-ui-go-no-go-blocked-data"))
        reports_dir = clean_data_dir("web-ui-go-no-go-blocked-reports")
        client = store.create_client(Client(name="Client Go No-Go Blocked"))
        mission = store.create_mission(
            Mission(
                client_id=client.id,
                name="Blocked Handoff",
                selected_checks=[AuditCheck.HTTP_HEADERS],
            )
        )
        store.add_scope_item(
            mission.id,
            ScopeItem(
                type=ScopeType.URL,
                value="https://blocked.example",
                approved=True,
            ),
        )

        view = build_mission_view(store, mission.id, reports_dir=reports_dir)
        items = {item.label: item for item in view.go_no_go.items}

        self.assertEqual(view.go_no_go.status, "blocked")
        self.assertEqual(view.go_no_go.decision, "No-Go")
        self.assertEqual(view.go_no_go.ready_count, 1)
        self.assertEqual(view.go_no_go.total_count, 6)
        self.assertEqual(view.go_no_go.action_label, "Update Setup")
        self.assertEqual(view.go_no_go.action_href, "#mission-setup")
        self.assertEqual(items["Authorization"].status, "blocked")
        self.assertEqual(items["Scope and services"].status, "ready")
        self.assertEqual(items["Report delivery"].status, "blocked")

    def test_mission_view_go_no_go_warns_when_only_cve_catalog_is_missing(self) -> None:
        store = JsonStore(clean_data_dir("web-ui-go-no-go-warning-data"))
        reports_dir = clean_data_dir("web-ui-go-no-go-warning-reports")
        client = store.create_client(Client(name="Client Go No-Go Warning"))
        mission = store.create_mission(
            Mission(
                client_id=client.id,
                name="Pilot Handoff",
                authorization_reference="AUTH-GO",
                selected_checks=[AuditCheck.HTTP_HEADERS],
            )
        )
        store.add_scope_item(
            mission.id,
            ScopeItem(
                type=ScopeType.URL,
                value="https://pilot.example",
                approved=True,
            ),
        )
        store.add_finding(
            mission.id,
            Finding(
                title="Missing HTTP security header",
                severity=Severity.MEDIUM,
                affected_asset="https://pilot.example",
                category="http",
                source_module="http_headers",
                proof="Strict-Transport-Security header missing",
                risk="The browser has less protection against downgrade scenarios.",
                remediation="Enable HSTS on the web server.",
                counter_test="Run the approved HTTP header plan again.",
                confidence=0.8,
                status=FindingStatus.CONFIRMED,
            ),
        )
        store.add_scan_run(
            ScanRun(
                mission_id=mission.id,
                check=AuditCheck.HTTP_HEADERS,
                status=ScanRunStatus.COMPLETED,
                started_at=datetime(2026, 6, 15, 9, 0, tzinfo=timezone.utc),
                command_count=1,
                finding_count=1,
                evidence_paths=["runs/mission/http_headers.json"],
            )
        )
        generate_authorization_brief(store, mission.id, reports_dir)
        generate_web_reports(store, mission.id, reports_dir)
        generate_mission_export(store, mission.id, reports_dir)

        view = build_mission_view(store, mission.id, reports_dir=reports_dir)
        items = {item.label: item for item in view.go_no_go.items}

        self.assertEqual(view.go_no_go.status, "warning")
        self.assertEqual(view.go_no_go.decision, "Review")
        self.assertEqual(view.go_no_go.ready_count, 5)
        self.assertEqual(view.go_no_go.total_count, 6)
        self.assertEqual(view.go_no_go.action_label, "Import Catalog")
        self.assertEqual(view.go_no_go.action_href, "#vulnerabilities")
        self.assertEqual(items["Authorization"].status, "ready")
        self.assertEqual(items["Scope and services"].status, "ready")
        self.assertEqual(items["Scan evidence"].status, "ready")
        self.assertEqual(items["CVE/KEV review"].status, "warning")
        self.assertEqual(items["Finding review"].status, "ready")
        self.assertEqual(items["Report delivery"].status, "ready")

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
