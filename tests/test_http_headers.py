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
    content_security_policy_is_permissive,
    http_header_evidence,
    normalize_headers,
    parse_hsts_max_age,
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
        self.assertIn("Missing Referrer-Policy header", titles)
        self.assertIn("Missing Permissions-Policy header", titles)
        self.assertIn("Server header exposes platform information", titles)
        self.assertTrue(any(finding.severity == Severity.MEDIUM for finding in findings))
        self.assertTrue(all(finding.metadata["http_method"] == "HEAD" for finding in findings))

    def test_accepts_reasonable_headers_without_missing_header_findings(self) -> None:
        response = HttpHeaderResponse(
            url="https://example.invalid",
            status_code=200,
            headers={
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
                "X-Content-Type-Options": "nosniff",
                "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'",
                "Referrer-Policy": "strict-origin-when-cross-origin",
                "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
            },
        )

        self.assertEqual(audit_http_headers(response), [])

    def test_flags_short_hsts_and_permissive_csp(self) -> None:
        response = HttpHeaderResponse(
            url="https://example.invalid",
            status_code=200,
            headers={
                "Strict-Transport-Security": "max-age=300",
                "X-Content-Type-Options": "nosniff",
                "Content-Security-Policy": "default-src *; script-src 'unsafe-inline'",
                "X-Frame-Options": "DENY",
                "Referrer-Policy": "strict-origin-when-cross-origin",
                "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
            },
        )

        titles = {finding.title for finding in audit_http_headers(response)}

        self.assertIn("HTTP Strict Transport Security max-age is too low", titles)
        self.assertIn("Content-Security-Policy appears permissive", titles)
        self.assertEqual(parse_hsts_max_age("max-age=300; includeSubDomains"), 300)
        self.assertTrue(content_security_policy_is_permissive("default-src *"))

    def test_flags_clear_text_http_targets(self) -> None:
        response = HttpHeaderResponse(
            url="http://example.invalid",
            status_code=200,
            headers={
                "X-Content-Type-Options": "nosniff",
                "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'",
                "Referrer-Policy": "strict-origin-when-cross-origin",
                "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
            },
        )

        findings = audit_http_headers(response)

        self.assertEqual(findings[0].title, "HTTP endpoint is not protected by HTTPS")
        self.assertEqual(findings[0].severity, Severity.MEDIUM)

    def test_formats_http_header_evidence_payload(self) -> None:
        response = HttpHeaderResponse(
            url="https://example.invalid",
            status_code=200,
            headers={"X-Content-Type-Options": "nosniff"},
            method="GET",
        )

        payload = http_header_evidence(response)

        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["url"], "https://example.invalid")
        self.assertEqual(payload["status_code"], 200)
        self.assertEqual(payload["method"], "GET")
        self.assertEqual(payload["headers"], {"X-Content-Type-Options": "nosniff"})


if __name__ == "__main__":
    unittest.main()

