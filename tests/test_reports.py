from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.models import ReportFormat  # noqa: E402
from media_security_audit.reports import render_html, render_json, render_markdown, write_report  # noqa: E402
from media_security_audit.sample_data import sample_findings, sample_mission  # noqa: E402


class ReportTests(unittest.TestCase):
    def test_renders_json_report(self) -> None:
        payload = json.loads(render_json(sample_mission(), sample_findings()))

        self.assertEqual(payload["summary"]["finding_count"], 2)
        self.assertEqual(payload["mission"]["id"], "mission_sample")

    def test_renders_markdown_report(self) -> None:
        markdown = render_markdown(sample_mission(), sample_findings())

        self.assertIn("# Security Audit Report", markdown)
        self.assertIn("Missing HTTP Strict Transport Security header", markdown)

    def test_renders_html_report(self) -> None:
        html = render_html(sample_mission(), sample_findings())

        self.assertIn("<!doctype html>", html)
        self.assertIn("Missing HTTP Strict Transport Security header", html)

    def test_writes_report_file(self) -> None:
        output_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / "report-output"
        output_dir.mkdir(parents=True, exist_ok=True)
        report = write_report(
            sample_mission(),
            sample_findings(),
            output_dir,
            ReportFormat.JSON,
        )

        self.assertTrue(Path(report.output_path or "").exists())
        self.assertEqual(report.finding_count, 2)


if __name__ == "__main__":
    unittest.main()
