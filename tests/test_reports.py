from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.models import ReportFormat  # noqa: E402
from media_security_audit.reports import (  # noqa: E402
    build_report_summary,
    render_html,
    render_json,
    render_markdown,
    remediation_plan,
    write_report,
)
from media_security_audit.sample_data import sample_findings, sample_mission  # noqa: E402


class ReportTests(unittest.TestCase):
    def test_renders_json_report(self) -> None:
        payload = json.loads(render_json(sample_mission(), sample_findings()))

        self.assertEqual(payload["summary"]["finding_count"], 2)
        self.assertEqual(payload["summary"]["active_finding_count"], 2)
        self.assertEqual(payload["summary"]["risk_score"], 13)
        self.assertEqual(payload["summary"]["risk_level"], "low")
        self.assertEqual(payload["summary"]["scope"]["approved_count"], 1)
        self.assertEqual(len(payload["remediation_plan"]), 2)
        self.assertEqual(payload["mission"]["id"], "mission_sample")

    def test_renders_markdown_report(self) -> None:
        markdown = render_markdown(sample_mission(), sample_findings())

        self.assertIn("# Security Audit Report", markdown)
        self.assertIn("## Executive Summary", markdown)
        self.assertIn("## Remediation Plan", markdown)
        self.assertIn("Risk score: `13/100`", markdown)
        self.assertIn("Missing HTTP Strict Transport Security header", markdown)

    def test_renders_html_report(self) -> None:
        html = render_html(sample_mission(), sample_findings())

        self.assertIn("<!doctype html>", html)
        self.assertIn("Risk Overview", html)
        self.assertIn("Remediation Plan", html)
        self.assertIn("Missing HTTP Strict Transport Security header", html)

    def test_builds_report_summary_and_remediation_plan(self) -> None:
        summary = build_report_summary(sample_mission(), sample_findings())
        plan = remediation_plan(sample_findings())

        self.assertTrue(summary["authorization_present"])
        self.assertEqual(summary["scope"]["approved_targets"], ["domain:example.invalid"])
        self.assertEqual(plan[0]["severity"], "medium")

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
