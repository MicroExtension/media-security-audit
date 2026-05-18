from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.audit_templates import (  # noqa: E402
    filter_audit_templates,
    get_audit_template,
    list_audit_templates,
)
from media_security_audit.models import AuditCheck, AuditType  # noqa: E402
from media_security_audit.web_audit_templates import build_audit_template_library_view  # noqa: E402


class AuditTemplateTests(unittest.TestCase):
    def test_template_page_exposes_shortcut_anchors(self) -> None:
        template_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_templates"
            / "audit_templates.html"
        )
        template = template_path.read_text(encoding="utf-8")

        for anchor in ["template-filters", "template-library"]:
            self.assertIn(f'href="#{anchor}"', template)
            self.assertIn(f'id="{anchor}"', template)

        for counter in ["view.audit_types | length", "view.total_count"]:
            self.assertIn(f"{{{{ {counter} }}}}", template)

    def test_builtin_templates_are_structured_for_repeatable_audits(self) -> None:
        templates = list_audit_templates()
        ids = [template.id for template in templates]

        self.assertGreaterEqual(len(templates), 4)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(template.title.strip() for template in templates))
        self.assertTrue(all(template.summary.strip() for template in templates))
        self.assertTrue(all(template.recommended_checks for template in templates))
        self.assertTrue(all(template.scope_guidance for template in templates))
        self.assertTrue(all(template.authorization_requirements for template in templates))
        self.assertTrue(all(template.deliverables for template in templates))

    def test_filters_by_audit_type_and_query(self) -> None:
        external_templates = filter_audit_templates(audit_type=AuditType.EXTERNAL)
        mail_templates = filter_audit_templates(query="mail")

        self.assertTrue(external_templates)
        self.assertTrue(
            all(template.audit_type is AuditType.EXTERNAL for template in external_templates)
        )
        self.assertIn("tpl_web_mail_hygiene", [template.id for template in mail_templates])
        self.assertEqual(get_audit_template("tpl_external_perimeter").title, "External Perimeter Review")
        self.assertIsNone(get_audit_template("tpl_missing"))

    def test_builds_web_view_with_check_labels(self) -> None:
        view = build_audit_template_library_view(query="internal", audit_type="internal")

        self.assertEqual(view.selected_audit_type, "internal")
        self.assertEqual(view.query, "internal")
        self.assertEqual(view.total_count, 1)
        self.assertEqual(view.templates[0].id, "tpl_internal_hygiene")
        self.assertEqual(view.templates[0].recommended_checks, ["Nmap services"])
        self.assertIn(AuditCheck.NMAP.value, [check.value for check in AuditCheck])


if __name__ == "__main__":
    unittest.main()
