from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.models import ScopeItem, ScopeType, Severity  # noqa: E402
from media_security_audit.scanners.http_headers import (  # noqa: E402
    HttpHeaderResponse,
    approved_http_targets,
    audit_http_headers,
    normalize_headers,
    validate_http_url,
)


class HttpHeaderTests(unittest.TestCase):
    def test_filters_approved_url_targets_only(self) -> None:
        scope = [
            ScopeItem(type=ScopeType.URL, value="https://example.invalid", approved=True),
            ScopeItem(type=ScopeType.DOMAIN, value="example.invalid", approved=True),
            ScopeItem(type=ScopeType.URL, value="https://draft.example.invalid"),
            ScopeItem(type=ScopeType.URL, value="https://excluded.example.invalid", excluded=True),
        ]

        self.assertEqual(approved_http_targets(scope), ["https://example.invalid"])

    def test_rejects_invalid_http_urls(self) -> None:
        for url in ["example.invalid", "ftp://example.invalid", "https://user:pass@example.invalid"]:
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    validate_http_url(url)

    def test_normalizes_headers_case_insensitively(self) -> None:
        normalized = normalize_headers({"Strict-Transport-Security": " max-age=31536000 "})

        self.assertEqual(normalized["strict-transport-security"], "max-age=31536000")

    def test_generates_findings_for_missing_security_headers(self) -> None:
        response = HttpHeaderResponse(
            url="https://example.invalid",
            status_code=200,
            headers={"Server": "nginx/1.24"},
        )

        findings = audit_http_headers(response)
        titles = {finding.title for finding in findings}

        self.assertIn("Missing HTTP Strict Transport Security header", titles)
        self.assertIn("Missing X-Content-Type-Options nosniff header", titles)
        self.assertIn("Missing clickjacking protection header", titles)
        self.assertIn("Missing Content-Security-Policy header", titles)
        self.assertIn("Server header exposes platform information", titles)
        self.assertTrue(any(finding.severity == Severity.MEDIUM for finding in findings))

    def test_accepts_reasonable_headers_without_missing_header_findings(self) -> None:
        response = HttpHeaderResponse(
            url="https://example.invalid",
            status_code=200,
            headers={
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
                "X-Content-Type-Options": "nosniff",
                "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'",
            },
        )

        self.assertEqual(audit_http_headers(response), [])


if __name__ == "__main__":
    unittest.main()

