from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.models import ScopeItem, ScopeType, Severity  # noqa: E402
from media_security_audit.scanners.nmap import (  # noqa: E402
    NmapCommandBuilder,
    approved_nmap_targets,
    findings_from_hosts,
    parse_nmap_xml_file,
    render_command,
    validate_nmap_target,
)


class NmapScannerTests(unittest.TestCase):
    def test_builds_safe_dry_run_command(self) -> None:
        command = NmapCommandBuilder().build("192.0.2.10")

        self.assertEqual(command[0], "nmap")
        self.assertIn("--version-light", command)
        self.assertIn("-T2", command)
        self.assertNotIn("-A", command)
        self.assertNotIn("-sU", command)
        self.assertNotIn("--script", command)

    def test_filters_approved_nmap_targets(self) -> None:
        scope = [
            ScopeItem(type=ScopeType.DOMAIN, value="example.invalid", approved=True),
            ScopeItem(type=ScopeType.IP, value="192.0.2.10", approved=False),
            ScopeItem(type=ScopeType.URL, value="https://example.invalid", approved=True),
            ScopeItem(type=ScopeType.CIDR, value="192.0.2.0/30", excluded=True),
        ]

        self.assertEqual(approved_nmap_targets(scope), ["example.invalid"])

    def test_parses_nmap_xml_fixture(self) -> None:
        fixture = Path(__file__).parent / "fixtures" / "nmap_sample.xml"
        hosts = parse_nmap_xml_file(fixture)

        self.assertEqual(len(hosts), 1)
        self.assertEqual(hosts[0].address, "192.0.2.10")
        self.assertEqual(hosts[0].hostnames, ("server.example.invalid",))
        self.assertEqual(len(hosts[0].services), 2)
        self.assertEqual(hosts[0].services[1].port, 3389)

    def test_generates_findings_from_open_services(self) -> None:
        fixture = Path(__file__).parent / "fixtures" / "nmap_sample.xml"
        findings = findings_from_hosts(parse_nmap_xml_file(fixture))

        self.assertEqual(len(findings), 2)
        self.assertEqual(findings[0].severity, Severity.INFO)
        self.assertEqual(findings[1].severity, Severity.HIGH)
        self.assertIn("RDP", findings[1].title)

    def test_render_command_quotes_display_only(self) -> None:
        command = ["nmap", "-oX", "path with spaces/out.xml", "example.invalid"]

        self.assertEqual(
            render_command(command),
            'nmap -oX "path with spaces/out.xml" example.invalid',
        )

    def test_rejects_option_like_or_whitespace_targets(self) -> None:
        with self.assertRaises(ValueError):
            validate_nmap_target("-oX")

        with self.assertRaises(ValueError):
            validate_nmap_target("example invalid")


if __name__ == "__main__":
    unittest.main()
