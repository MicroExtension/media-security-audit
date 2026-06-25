from pathlib import Path
import json
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.models import ReportFormat  # noqa: E402
from media_security_audit.remediation_library import (  # noqa: E402
    filter_remediations,
    list_remediations,
    remediation_categories,
)
from media_security_audit.web_remediations import (  # noqa: E402
    build_remediation_library_export,
    build_remediation_library_view,
)


class RemediationLibraryTests(unittest.TestCase):
    def test_remediation_template_exposes_shortcut_anchors(self) -> None:
        template_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_templates"
            / "remediations.html"
        )
        template = template_path.read_text(encoding="utf-8")

        for anchor in [
            "remediation-filters",
            "remediation-entries",
            "remediation-exports",
        ]:
            self.assertIn(f'href="#{anchor}"', template)
            self.assertIn(f'id="{anchor}"', template)

        for counter in [
            "view.categories | length",
            "view.total_count",
            "view.export_links|length",
        ]:
            self.assertIn(f"{{{{ {counter} }}}}", template)

    def test_builtin_entries_are_structured_for_reports(self) -> None:
        entries = list_remediations()
        ids = [entry.id for entry in entries]

        self.assertGreaterEqual(len(entries), 8)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("rem_http_csp_baseline", ids)
        self.assertIn("rem_http_referrer_policy", ids)
        self.assertIn("rem_http_permissions_policy", ids)
        self.assertTrue(all(entry.title.strip() for entry in entries))
        self.assertTrue(all(entry.risk.strip() for entry in entries))
        self.assertTrue(all(entry.remediation.strip() for entry in entries))
        self.assertTrue(all(entry.counter_test.strip() for entry in entries))
        self.assertTrue(all(entry.applies_to for entry in entries))

    def test_filters_by_category_and_query(self) -> None:
        dns_entries = filter_remediations(category="dns_mail")
        rdp_entries = filter_remediations(query="rdp")

        self.assertTrue(dns_entries)
        self.assertTrue(all(entry.category == "dns_mail" for entry in dns_entries))
        self.assertEqual([entry.id for entry in rdp_entries], ["rem_rdp_restrict_exposure"])

    def test_builds_web_view(self) -> None:
        view = build_remediation_library_view(query="SMB", category="smb")

        self.assertEqual(view.selected_category, "smb")
        self.assertEqual(view.query, "SMB")
        self.assertEqual(view.total_count, 2)
        self.assertIn("smb", remediation_categories())
        self.assertTrue(all(entry.category == "smb" for entry in view.entries))
        self.assertEqual(
            view.export_links[0].url,
            "/remediations/export/json?q=SMB&category=smb",
        )

    def test_exports_filtered_library_as_json_markdown_and_html(self) -> None:
        json_export = build_remediation_library_export(
            ReportFormat.JSON,
            query="SMB",
            category="smb",
        )
        markdown_export = build_remediation_library_export(
            ReportFormat.MARKDOWN,
            query="SMB",
            category="smb",
        )
        html_export = build_remediation_library_export(
            ReportFormat.HTML,
            query="SMB",
            category="smb",
        )

        payload = json.loads(json_export.content)
        self.assertEqual(json_export.filename, "remediation-library-smb-filtered.json")
        self.assertEqual(json_export.media_type, "application/json")
        self.assertEqual(payload["category"], "smb")
        self.assertEqual(payload["count"], 2)
        self.assertEqual(markdown_export.filename, "remediation-library-smb-filtered.md")
        self.assertIn("# Remediation Library", markdown_export.content)
        self.assertIn("Require SMB Signing Where Appropriate", markdown_export.content)
        self.assertEqual(html_export.filename, "remediation-library-smb-filtered.html")
        self.assertIn("<!doctype html>", html_export.content)
        self.assertIn("Disable SMBv1", html_export.content)

    def test_rejects_pdf_remediation_library_export(self) -> None:
        with self.assertRaises(ValueError) as error:
            build_remediation_library_export(ReportFormat.PDF)

        self.assertIn("unsupported remediation export format: pdf", str(error.exception))


if __name__ == "__main__":
    unittest.main()
