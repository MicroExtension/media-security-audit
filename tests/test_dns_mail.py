from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.models import ScopeItem, ScopeType, Severity  # noqa: E402
from media_security_audit.scanners.dns_mail import (  # noqa: E402
    approved_dns_domains,
    audit_dns_mail_domain,
    dns_mail_query_plan,
    validate_domain,
    validate_selector,
)


class DnsMailTests(unittest.TestCase):
    def test_filters_approved_domain_targets_only(self) -> None:
        scope = [
            ScopeItem(type=ScopeType.DOMAIN, value="Example.Invalid", approved=True),
            ScopeItem(type=ScopeType.URL, value="https://example.invalid", approved=True),
            ScopeItem(type=ScopeType.DOMAIN, value="draft.invalid"),
            ScopeItem(type=ScopeType.DOMAIN, value="excluded.invalid", excluded=True),
        ]

        self.assertEqual(approved_dns_domains(scope), ["example.invalid"])

    def test_builds_dns_mail_query_plan(self) -> None:
        queries = dns_mail_query_plan(["example.invalid"], ["default", "selector1"])

        self.assertEqual(
            queries,
            [
                "TXT example.invalid",
                "TXT _dmarc.example.invalid",
                "TXT default._domainkey.example.invalid",
                "TXT selector1._domainkey.example.invalid",
            ],
        )

    def test_rejects_invalid_domain_and_selector_values(self) -> None:
        for domain in ["example invalid", "https://example.invalid", "-example.invalid", "localhost"]:
            with self.subTest(domain=domain):
                with self.assertRaises(ValueError):
                    validate_domain(domain)

        for selector in ["", "selector one", "-default", "a.b"]:
            with self.subTest(selector=selector):
                with self.assertRaises(ValueError):
                    validate_selector(selector)

    def test_generates_spf_and_dmarc_findings(self) -> None:
        records = {
            "example.invalid": ["v=spf1 +all"],
            "_dmarc.example.invalid": ["v=DMARC1; p=none"],
        }

        findings = audit_dns_mail_domain("example.invalid", lambda name: records.get(name, []))
        titles = {finding.title for finding in findings}

        self.assertIn("SPF record permits all senders", titles)
        self.assertIn("DMARC policy is monitoring only", titles)
        self.assertTrue(any(finding.severity == Severity.HIGH for finding in findings))

    def test_generates_missing_records_findings(self) -> None:
        findings = audit_dns_mail_domain("example.invalid", lambda _name: [])
        titles = {finding.title for finding in findings}

        self.assertIn("SPF record is missing", titles)
        self.assertIn("DMARC record is missing", titles)

    def test_checks_dkim_selectors_when_provided(self) -> None:
        records = {
            "example.invalid": ["v=spf1 include:_spf.example.invalid -all"],
            "_dmarc.example.invalid": ["v=DMARC1; p=reject"],
            "default._domainkey.example.invalid": ["v=DKIM1; k=rsa; p=;"],
        }

        findings = audit_dns_mail_domain(
            "example.invalid",
            lambda name: records.get(name, []),
            dkim_selectors=["default", "selector1"],
        )
        titles = {finding.title for finding in findings}

        self.assertIn("DKIM selector has no usable public key", titles)
        self.assertIn("DKIM selector TXT record is missing", titles)


if __name__ == "__main__":
    unittest.main()

