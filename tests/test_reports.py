from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.models import (  # noqa: E402
    Finding,
    FindingStatus,
    ReportFormat,
    Severity,
)
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
        self.assertEqual(payload["summary"]["authorization"]["contact"], "Sample Sponsor")
        self.assertEqual(len(payload["remediation_plan"]), 2)
        self.assertEqual(payload["mission"]["id"], "mission_sample")
        self.assertEqual(payload["mission"]["evidence_retention_days"], 90)

    def test_renders_markdown_report(self) -> None:
        markdown = render_markdown(sample_mission(), sample_findings())

        self.assertIn("# Security Audit Report", markdown)
        self.assertIn("## Executive Summary", markdown)
        self.assertIn("## Remediation Plan", markdown)
        self.assertIn("Risk score: `13/100`", markdown)
        self.assertIn("Authorization contact: `Sample Sponsor`", markdown)
        self.assertIn("Evidence retention days: `90`", markdown)
        self.assertIn("Missing HTTP Strict Transport Security header", markdown)

    def test_renders_html_report(self) -> None:
        html = render_html(sample_mission(), sample_findings())

        self.assertIn("<!doctype html>", html)
        self.assertIn("Risk Overview", html)
        self.assertIn("Remediation Plan", html)
        self.assertIn("Sample Sponsor", html)
        self.assertIn("security@example.invalid", html)
        self.assertIn("Missing HTTP Strict Transport Security header", html)

    def test_builds_report_summary_and_remediation_plan(self) -> None:
        summary = build_report_summary(sample_mission(), sample_findings())
        plan = remediation_plan(sample_findings())

        self.assertTrue(summary["authorization_present"])
        self.assertEqual(summary["authorization"]["evidence_retention_days"], "90")
        self.assertEqual(summary["scope"]["approved_targets"], ["domain:example.invalid"])
        self.assertEqual(plan[0]["severity"], "medium")

    def test_reports_include_reviewed_disposition_notes(self) -> None:
        findings = sample_findings() + [
            Finding(
                title="Accepted legacy TLS exception",
                severity=Severity.LOW,
                affected_asset="legacy.example.invalid",
                category="tls",
                source_module="manual",
                proof="Legacy endpoint still requires TLS exception.",
                risk="Residual compatibility risk remains.",
                remediation="Plan service replacement.",
                counter_test="Confirm exception is still documented.",
                confidence=0.8,
                status=FindingStatus.ACCEPTED_RISK,
                metadata={"review_note": "Accepted by the client risk owner."},
            ),
            Finding(
                title="False positive web banner",
                severity=Severity.MEDIUM,
                affected_asset="https://example.invalid",
                category="http_headers",
                source_module="manual",
                proof="Scanner matched a generic banner.",
                risk="No exploitable condition was confirmed.",
                remediation="No remediation required.",
                counter_test="Repeat manual verification.",
                confidence=0.7,
                status=FindingStatus.FALSE_POSITIVE,
                metadata={"review_note": "Banner belongs to the upstream WAF."},
            ),
        ]

        payload = json.loads(render_json(sample_mission(), findings))
        markdown = render_markdown(sample_mission(), findings)
        html = render_html(sample_mission(), findings)

        self.assertEqual(payload["summary"]["status_counts"]["accepted_risk"], 1)
        self.assertEqual(payload["summary"]["status_counts"]["false_positive"], 1)
        self.assertEqual(payload["summary"]["active_finding_count"], 3)
        self.assertEqual(len(payload["summary"]["disposition_notes"]), 2)
        self.assertIn("## Finding Dispositions", markdown)
        self.assertIn("- Accepted risk: 1", markdown)
        self.assertIn("Accepted by the client risk owner.", markdown)
        self.assertIn("Banner belongs to the upstream WAF.", markdown)
        self.assertIn("**Review note**", markdown)
        self.assertIn("Finding Dispositions", html)
        self.assertIn("Review note", html)
        self.assertIn("Accepted by the client risk owner.", html)

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
