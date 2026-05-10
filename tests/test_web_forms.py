from pathlib import Path
import shutil
import unittest

import sys

from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.models import (  # noqa: E402
    AuditCheck,
    AuditType,
    Finding,
    FindingStatus,
    ScopeType,
    Severity,
)
from media_security_audit.storage import JsonStore  # noqa: E402
from media_security_audit.web_forms import (  # noqa: E402
    add_manual_finding_from_form,
    add_scope_from_form,
    create_client_from_form,
    create_mission_from_form,
    new_form_token,
    parse_checkbox,
    parse_confidence,
    parse_urlencoded_form,
    update_finding_status_from_form,
    update_manual_finding_from_form,
    update_mission_checks_from_form,
    update_mission_from_form,
    update_scope_from_form,
    validate_form_token,
)


def clean_data_dir(name: str) -> Path:
    data_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / name
    if data_dir.exists():
        shutil.rmtree(data_dir)
    return data_dir


class WebFormTests(unittest.TestCase):
    def test_parse_urlencoded_form_keeps_last_value_and_blanks(self) -> None:
        form = parse_urlencoded_form(b"name=Client+X&reference=&name=Client+Y")

        self.assertEqual(form["name"], "Client Y")
        self.assertEqual(form["reference"], "")

    def test_create_client_from_form(self) -> None:
        store = JsonStore(clean_data_dir("web-form-client"))

        client = create_client_from_form(
            store,
            {
                "name": " Client X ",
                "reference": " CX ",
                "notes": "",
            },
        )

        self.assertEqual(client.name, "Client X")
        self.assertEqual(client.internal_reference, "CX")
        self.assertIsNone(client.notes)
        self.assertEqual(store.get_client(client.id).name, "Client X")

    def test_create_mission_from_form(self) -> None:
        store = JsonStore(clean_data_dir("web-form-mission"))
        client = create_client_from_form(store, {"name": "Client X"})

        mission = create_mission_from_form(
            store,
            {
                "client_id": client.id,
                "name": "Audit externe",
                "audit_type": "external",
                "authorization_reference": "AUTH-001",
                "authorization_contact": " Sponsor Client ",
                "authorization_date": "2026-05-10",
                "authorization_expires_at": "2026-06-10",
                "emergency_contact": " astreinte@example.invalid ",
                "report_recipients": " direction@example.invalid ",
                "evidence_retention_days": "90",
            },
        )

        self.assertEqual(mission.audit_type, AuditType.EXTERNAL)
        self.assertEqual(mission.authorization_reference, "AUTH-001")
        self.assertEqual(mission.authorization_contact, "Sponsor Client")
        self.assertEqual(mission.authorization_date.isoformat(), "2026-05-10")
        self.assertEqual(mission.authorization_expires_at.isoformat(), "2026-06-10")
        self.assertEqual(mission.emergency_contact, "astreinte@example.invalid")
        self.assertEqual(mission.report_recipients, "direction@example.invalid")
        self.assertEqual(mission.evidence_retention_days, 90)
        self.assertIsNone(mission.audit_template_id)

    def test_create_mission_from_template_sets_audit_type_and_checks(self) -> None:
        store = JsonStore(clean_data_dir("web-form-mission-template"))
        client = create_client_from_form(store, {"name": "Client Template"})

        mission = create_mission_from_form(
            store,
            {
                "client_id": client.id,
                "name": "Web Mail Hygiene",
                "audit_template_id": "tpl_web_mail_hygiene",
                "audit_type": "mixed",
            },
        )

        self.assertEqual(mission.audit_template_id, "tpl_web_mail_hygiene")
        self.assertEqual(mission.audit_type, AuditType.EXTERNAL)
        self.assertEqual(mission.selected_checks, [AuditCheck.HTTP_HEADERS, AuditCheck.DNS_MAIL])

    def test_create_mission_rejects_unknown_template(self) -> None:
        store = JsonStore(clean_data_dir("web-form-mission-template-missing"))
        client = create_client_from_form(store, {"name": "Client Template"})

        with self.assertRaises(ValueError) as error:
            create_mission_from_form(
                store,
                {
                    "client_id": client.id,
                    "name": "Unknown Template",
                    "audit_template_id": "tpl_missing",
                    "audit_type": "external",
                },
            )

        self.assertIn("audit template not found", str(error.exception))

    def test_add_scope_from_form(self) -> None:
        store = JsonStore(clean_data_dir("web-form-scope"))
        client = create_client_from_form(store, {"name": "Client X"})
        mission = create_mission_from_form(
            store,
            {
                "client_id": client.id,
                "name": "Audit externe",
                "audit_type": "external",
                "authorization_reference": "AUTH-001",
            },
        )

        updated = add_scope_from_form(
            store,
            mission.id,
            {
                "scope_type": "domain",
                "value": "client.example",
                "environment": "external",
                "approved": "on",
            },
        )

        self.assertEqual(updated.scope[0].type, ScopeType.DOMAIN)
        self.assertTrue(updated.scope[0].approved)
        self.assertEqual(updated.status.value, "ready_to_scan")

    def test_add_scope_rejects_approved_and_excluded_item(self) -> None:
        store = JsonStore(clean_data_dir("web-form-invalid-scope"))
        client = create_client_from_form(store, {"name": "Client X"})
        mission = create_mission_from_form(
            store,
            {
                "client_id": client.id,
                "name": "Audit externe",
                "audit_type": "external",
                "authorization_reference": "AUTH-001",
            },
        )

        with self.assertRaises(ValueError):
            add_scope_from_form(
                store,
                mission.id,
                {
                    "scope_type": "domain",
                    "value": "client.example",
                    "approved": "on",
                    "excluded": "on",
                },
            )

    def test_update_scope_from_form_recomputes_status(self) -> None:
        store = JsonStore(clean_data_dir("web-form-scope-update"))
        client = create_client_from_form(store, {"name": "Client X"})
        mission = create_mission_from_form(
            store,
            {
                "client_id": client.id,
                "name": "Audit externe",
                "audit_type": "external",
                "authorization_reference": "AUTH-001",
            },
        )
        scoped = add_scope_from_form(
            store,
            mission.id,
            {
                "scope_type": "domain",
                "value": "client.example",
                "environment": "external",
                "approved": "on",
            },
        )

        updated = update_scope_from_form(
            store,
            mission.id,
            scoped.scope[0].id,
            {
                "scope_type": "url",
                "value": "https://client.example",
                "environment": "external",
                "excluded": "on",
                "notes": " Out of scope ",
            },
        )

        self.assertEqual(updated.scope[0].type, ScopeType.URL)
        self.assertEqual(updated.scope[0].value, "https://client.example")
        self.assertFalse(updated.scope[0].approved)
        self.assertTrue(updated.scope[0].excluded)
        self.assertEqual(updated.scope[0].notes, "Out of scope")
        self.assertEqual(updated.status.value, "authorized")

    def test_update_scope_from_form_rejects_invalid_state(self) -> None:
        store = JsonStore(clean_data_dir("web-form-invalid-scope-update"))
        client = create_client_from_form(store, {"name": "Client X"})
        mission = create_mission_from_form(
            store,
            {
                "client_id": client.id,
                "name": "Audit externe",
                "audit_type": "external",
            },
        )
        scoped = add_scope_from_form(
            store,
            mission.id,
            {
                "scope_type": "ip",
                "value": "192.0.2.10",
                "approved": "on",
            },
        )

        with self.assertRaises(ValueError):
            update_scope_from_form(
                store,
                mission.id,
                scoped.scope[0].id,
                {
                    "scope_type": "ip",
                    "value": "not an ip",
                    "approved": "on",
                },
            )

        with self.assertRaises(ValueError):
            update_scope_from_form(
                store,
                mission.id,
                scoped.scope[0].id,
                {
                    "scope_type": "ip",
                    "value": "192.0.2.10",
                    "approved": "on",
                    "excluded": "on",
                },
            )

    def test_add_manual_finding_from_form(self) -> None:
        store = JsonStore(clean_data_dir("web-form-manual-finding"))
        client = create_client_from_form(store, {"name": "Client X"})
        mission = create_mission_from_form(
            store,
            {
                "client_id": client.id,
                "name": "Audit externe",
                "audit_type": "external",
            },
        )

        finding = add_manual_finding_from_form(
            store,
            mission.id,
            {
                "title": " Administrative interface exposed ",
                "severity": "medium",
                "affected_asset": "https://admin.client.example",
                "category": "",
                "proof": "Admin login page observed.",
                "risk": "Attack surface is increased.",
                "remediation": "Restrict access to trusted sources.",
                "counter_test": "Open the URL again from the audited network.",
                "confidence": "0.7",
            },
        )

        self.assertEqual(finding.title, "Administrative interface exposed")
        self.assertEqual(finding.severity, Severity.MEDIUM)
        self.assertEqual(finding.category, "manual")
        self.assertEqual(finding.source_module, "manual")
        self.assertEqual(finding.confidence, 0.7)
        self.assertEqual(len(store.list_findings(mission.id)), 1)

    def test_add_manual_finding_requires_structured_fields(self) -> None:
        store = JsonStore(clean_data_dir("web-form-invalid-manual-finding"))
        client = create_client_from_form(store, {"name": "Client X"})
        mission = create_mission_from_form(
            store,
            {
                "client_id": client.id,
                "name": "Audit externe",
                "audit_type": "external",
            },
        )

        with self.assertRaises(ValueError):
            add_manual_finding_from_form(
                store,
                mission.id,
                {
                    "title": "",
                    "severity": "low",
                    "affected_asset": "client.example",
                    "proof": "Observed manually.",
                    "risk": "Risk pending review.",
                    "remediation": "Apply remediation.",
                    "counter_test": "Repeat the check.",
                },
            )

    def test_update_manual_finding_from_form_preserves_review_state(self) -> None:
        store = JsonStore(clean_data_dir("web-form-manual-finding-update"))
        client = create_client_from_form(store, {"name": "Client X"})
        mission = create_mission_from_form(
            store,
            {
                "client_id": client.id,
                "name": "Audit externe",
                "audit_type": "external",
            },
        )
        finding = add_manual_finding_from_form(
            store,
            mission.id,
            {
                "title": "Old title",
                "severity": "low",
                "affected_asset": "client.example",
                "proof": "Initial proof.",
                "risk": "Initial risk.",
                "remediation": "Initial remediation.",
                "counter_test": "Initial counter-test.",
            },
        )
        store.update_finding_status(mission.id, finding.id, FindingStatus.CONFIRMED, "Validated")

        updated = update_manual_finding_from_form(
            store,
            mission.id,
            finding.id,
            {
                "title": "Updated finding",
                "severity": "high",
                "affected_asset": "admin.client.example",
                "category": "manual_review",
                "proof": "Updated proof.",
                "risk": "Updated risk.",
                "remediation": "Updated remediation.",
                "counter_test": "Updated counter-test.",
                "confidence": "0.9",
            },
        )

        self.assertEqual(updated.title, "Updated finding")
        self.assertEqual(updated.severity, Severity.HIGH)
        self.assertEqual(updated.status, FindingStatus.CONFIRMED)
        self.assertEqual(updated.metadata["review_note"], "Validated")
        self.assertIn("edited_at", updated.metadata)
        self.assertEqual(updated.confidence, 0.9)

    def test_update_manual_finding_rejects_scanner_findings(self) -> None:
        store = JsonStore(clean_data_dir("web-form-scanner-finding-update"))
        client = create_client_from_form(store, {"name": "Client X"})
        mission = create_mission_from_form(
            store,
            {
                "client_id": client.id,
                "name": "Audit externe",
                "audit_type": "external",
            },
        )
        finding = store.add_finding(
            mission.id,
            Finding(
                title="Scanner finding",
                severity=Severity.LOW,
                affected_asset="client.example",
                category="network",
                source_module="nmap",
                proof="tcp/80 open",
                risk="Risk pending review.",
                remediation="Apply remediation.",
                counter_test="Repeat the approved check.",
                confidence=0.8,
            ),
        )

        with self.assertRaises(ValueError):
            update_manual_finding_from_form(
                store,
                mission.id,
                finding.id,
                {
                    "title": "Updated finding",
                    "severity": "low",
                    "affected_asset": "client.example",
                    "proof": "Updated proof.",
                    "risk": "Updated risk.",
                    "remediation": "Updated remediation.",
                    "counter_test": "Updated counter-test.",
                },
            )

    def test_update_mission_from_form_recomputes_status(self) -> None:
        store = JsonStore(clean_data_dir("web-form-mission-update"))
        client = create_client_from_form(store, {"name": "Client X"})
        mission = create_mission_from_form(
            store,
            {
                "client_id": client.id,
                "name": "Audit draft",
                "audit_type": "external",
            },
        )
        add_scope_from_form(
            store,
            mission.id,
            {
                "scope_type": "domain",
                "value": "client.example",
                "environment": "external",
                "approved": "on",
            },
        )

        updated = update_mission_from_form(
            store,
            mission.id,
            {
                "name": " Audit externe ",
                "audit_type": "mixed",
                "authorization_reference": " AUTH-002 ",
                "authorization_contact": " DSI ",
                "authorization_date": "2026-05-10",
                "authorization_expires_at": "2026-05-31",
                "emergency_contact": " security@example.invalid ",
                "report_recipients": " rss@example.invalid ",
                "evidence_retention_days": "45",
                "notes": " Validate with client ",
            },
        )

        self.assertEqual(updated.name, "Audit externe")
        self.assertEqual(updated.audit_type.value, "mixed")
        self.assertEqual(updated.authorization_reference, "AUTH-002")
        self.assertEqual(updated.authorization_contact, "DSI")
        self.assertEqual(updated.authorization_date.isoformat(), "2026-05-10")
        self.assertEqual(updated.authorization_expires_at.isoformat(), "2026-05-31")
        self.assertEqual(updated.emergency_contact, "security@example.invalid")
        self.assertEqual(updated.report_recipients, "rss@example.invalid")
        self.assertEqual(updated.evidence_retention_days, 45)
        self.assertEqual(updated.notes, "Validate with client")
        self.assertEqual(updated.status.value, "ready_to_scan")

    def test_update_mission_from_form_rejects_invalid_authorization_details(self) -> None:
        store = JsonStore(clean_data_dir("web-form-invalid-auth-details"))
        client = create_client_from_form(store, {"name": "Client X"})
        mission = create_mission_from_form(
            store,
            {
                "client_id": client.id,
                "name": "Audit draft",
                "audit_type": "external",
            },
        )

        with self.assertRaises(ValueError):
            update_mission_from_form(
                store,
                mission.id,
                {
                    "name": "Audit externe",
                    "audit_type": "external",
                    "authorization_date": "10/05/2026",
                },
            )

        with self.assertRaises(ValidationError):
            update_mission_from_form(
                store,
                mission.id,
                {
                    "name": "Audit externe",
                    "audit_type": "external",
                    "evidence_retention_days": "-1",
                },
            )

    def test_update_mission_checks_from_form(self) -> None:
        store = JsonStore(clean_data_dir("web-form-check-selection"))
        client = create_client_from_form(store, {"name": "Client X"})
        mission = create_mission_from_form(
            store,
            {
                "client_id": client.id,
                "name": "Audit externe",
                "audit_type": "external",
            },
        )

        updated = update_mission_checks_from_form(
            store,
            mission.id,
            {
                "check_nmap": "on",
                "check_dns_mail": "on",
            },
        )

        self.assertEqual(updated.selected_checks, [AuditCheck.NMAP, AuditCheck.DNS_MAIL])

        cleared = update_mission_checks_from_form(store, mission.id, {})

        self.assertEqual(cleared.selected_checks, [])

    def test_parse_checkbox(self) -> None:
        self.assertTrue(parse_checkbox({"approved": "on"}, "approved"))
        self.assertTrue(parse_checkbox({"approved": "true"}, "approved"))
        self.assertFalse(parse_checkbox({}, "approved"))

    def test_parse_confidence(self) -> None:
        self.assertEqual(parse_confidence(None), 0.8)
        self.assertEqual(parse_confidence("0.4"), 0.4)
        with self.assertRaises(ValueError):
            parse_confidence("high")

    def test_form_token_validation(self) -> None:
        token = new_form_token()

        validate_form_token({"_csrf": token}, token)
        with self.assertRaises(ValueError):
            validate_form_token({"_csrf": "wrong"}, token)
        with self.assertRaises(ValueError):
            validate_form_token({}, token)

    def test_update_finding_status_from_form(self) -> None:
        store = JsonStore(clean_data_dir("web-form-finding-status"))
        client = create_client_from_form(store, {"name": "Client X"})
        mission = create_mission_from_form(
            store,
            {
                "client_id": client.id,
                "name": "Audit externe",
                "audit_type": "external",
            },
        )
        finding = store.add_finding(
            mission.id,
            Finding(
                title="Manual finding",
                severity=Severity.LOW,
                affected_asset="client.example",
                category="manual",
                source_module="manual",
                proof="Observed manually",
                risk="Risk is pending review.",
                remediation="Apply remediation.",
                counter_test="Repeat the check.",
                confidence=0.8,
            ),
        )

        updated = update_finding_status_from_form(
            store,
            mission.id,
            finding.id,
            {
                "status": "confirmed",
                "review_note": "Looks valid",
            },
        )

        self.assertEqual(updated.status.value, "confirmed")
        self.assertEqual(updated.metadata["review_note"], "Looks valid")

        cleared = update_finding_status_from_form(
            store,
            mission.id,
            finding.id,
            {
                "status": "confirmed",
                "review_note": "",
            },
        )

        self.assertNotIn("review_note", cleared.metadata)


if __name__ == "__main__":
    unittest.main()
