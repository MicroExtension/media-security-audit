from pathlib import Path
import shutil
import unittest

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.models import Client, Finding, Mission, ReportFormat, Severity  # noqa: E402
from media_security_audit.storage import JsonStore  # noqa: E402
from media_security_audit.web_reports import (  # noqa: E402
    generated_report_file,
    generate_web_reports,
    list_generated_reports,
    mission_report_path,
)


def clean_dir(name: str) -> Path:
    path = Path(__file__).resolve().parents[1] / ".tmp-tests" / name
    if path.exists():
        shutil.rmtree(path)
    return path


class WebReportTests(unittest.TestCase):
    def test_generates_and_lists_reports(self) -> None:
        data_dir = clean_dir("web-report-data")
        reports_dir = clean_dir("web-report-output")
        store = JsonStore(data_dir)
        client = store.create_client(Client(name="Client X"))
        mission = store.create_mission(Mission(client_id=client.id, name="Audit"))
        store.add_finding(
            mission.id,
            Finding(
                title="Manual finding",
                severity=Severity.LOW,
                affected_asset="client.example",
                category="manual",
                source_module="manual",
                proof="Observed manually",
                risk="Risk pending review.",
                remediation="Apply remediation.",
                counter_test="Repeat the check.",
                confidence=0.8,
            ),
        )

        paths = generate_web_reports(store, mission.id, reports_dir)
        links = list_generated_reports(mission.id, reports_dir)

        self.assertEqual(len(paths), 4)
        self.assertTrue(all(path.exists() for path in paths))
        self.assertEqual([link.format for link in links], ["json", "markdown", "html", "pdf"])
        self.assertTrue(all(link.size_bytes > 0 for link in links))
        self.assertEqual(
            generated_report_file(reports_dir, mission.id, ReportFormat.HTML),
            mission_report_path(reports_dir, mission.id, ReportFormat.HTML),
        )
        self.assertEqual(
            generated_report_file(reports_dir, mission.id, ReportFormat.PDF),
            mission_report_path(reports_dir, mission.id, ReportFormat.PDF),
        )

    def test_missing_generated_report_file_raises_named_error(self) -> None:
        reports_dir = clean_dir("web-report-missing")

        with self.assertRaises(FileNotFoundError) as error:
            generated_report_file(reports_dir, "mission_missing", ReportFormat.JSON)

        self.assertIn("report not found: json", str(error.exception))


if __name__ == "__main__":
    unittest.main()
