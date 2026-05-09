from pathlib import Path
import shutil
import unittest

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.models import AuditType, Finding, ScopeType, Severity  # noqa: E402
from media_security_audit.storage import JsonStore  # noqa: E402
from media_security_audit.web_forms import (  # noqa: E402
    add_scope_from_form,
    create_client_from_form,
    create_mission_from_form,
    new_form_token,
    parse_checkbox,
    parse_urlencoded_form,
    update_finding_status_from_form,
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
            },
        )

        self.assertEqual(mission.audit_type, AuditType.EXTERNAL)
        self.assertEqual(mission.authorization_reference, "AUTH-001")

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
                "notes": " Validate with client ",
            },
        )

        self.assertEqual(updated.name, "Audit externe")
        self.assertEqual(updated.audit_type.value, "mixed")
        self.assertEqual(updated.authorization_reference, "AUTH-002")
        self.assertEqual(updated.notes, "Validate with client")
        self.assertEqual(updated.status.value, "ready_to_scan")

    def test_parse_checkbox(self) -> None:
        self.assertTrue(parse_checkbox({"approved": "on"}, "approved"))
        self.assertTrue(parse_checkbox({"approved": "true"}, "approved"))
        self.assertFalse(parse_checkbox({}, "approved"))

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
