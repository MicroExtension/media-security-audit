from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.findings import FindingEngine  # noqa: E402
from media_security_audit.models import Finding, Severity  # noqa: E402


def make_finding(source: str, severity: Severity = Severity.LOW) -> Finding:
    return Finding(
        title="Missing security header",
        severity=severity,
        affected_asset="https://example.invalid",
        category="http_headers",
        source_module=source,
        proof=f"Observed by {source}",
        risk="Missing headers can reduce browser-side protection.",
        remediation="Enable the missing security header.",
        counter_test="Repeat the HTTP request and confirm the header exists.",
        confidence=0.8,
    )


class FindingEngineTests(unittest.TestCase):
    def test_deduplicates_findings_and_merges_sources(self) -> None:
        engine = FindingEngine()

        first = engine.add(make_finding("http_headers", Severity.LOW))
        second = engine.add(make_finding("web_baseline", Severity.MEDIUM))

        findings = engine.list()

        self.assertIs(first, second)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].severity, Severity.MEDIUM)
        self.assertIn("http_headers", findings[0].sources)
        self.assertIn("web_baseline", findings[0].sources)
        self.assertIn("Additional evidence", findings[0].proof)


if __name__ == "__main__":
    unittest.main()

