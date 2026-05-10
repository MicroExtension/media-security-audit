from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.remediation_library import (  # noqa: E402
    filter_remediations,
    list_remediations,
    remediation_categories,
)
from media_security_audit.web_remediations import build_remediation_library_view  # noqa: E402


class RemediationLibraryTests(unittest.TestCase):
    def test_builtin_entries_are_structured_for_reports(self) -> None:
        entries = list_remediations()
        ids = [entry.id for entry in entries]

        self.assertGreaterEqual(len(entries), 8)
        self.assertEqual(len(ids), len(set(ids)))
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


if __name__ == "__main__":
    unittest.main()
