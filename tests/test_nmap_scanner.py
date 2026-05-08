from __future__ import annotations

import sys
import subprocess
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.models import ScopeItem, ScopeType, Severity  # noqa: E402
from media_security_audit.scanners.nmap import (  # noqa: E402
    NmapCommandBuilder,
    NmapExecutor,
    approved_nmap_targets,
    findings_from_hosts,
    nmap_output_path,
    parse_nmap_xml_file,
    render_command,
    validate_nmap_command,
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

    def test_validates_safe_command_shape(self) -> None:
        with self.assertRaises(ValueError):
            validate_nmap_command(["nmap", "-A", "example.invalid"])

        with self.assertRaises(ValueError):
            validate_nmap_command(["nmap", "-sU", "example.invalid"])

        with self.assertRaises(ValueError):
            validate_nmap_command(["nmap", "--script", "default", "example.invalid"])

    def test_extracts_nmap_output_path(self) -> None:
        command = ["nmap", "-oX", "runs/mission/evidence/nmap-1.xml", "example.invalid"]

        self.assertEqual(
            nmap_output_path(command),
            Path("runs/mission/evidence/nmap-1.xml"),
        )

    def test_executor_runs_list_command_without_shell(self) -> None:
        received: dict[str, object] = {}

        def runner(command: list[str], timeout_seconds: int) -> subprocess.CompletedProcess[str]:
            received["command"] = command
            received["timeout"] = timeout_seconds
            output_path = nmap_output_path(command)
            assert output_path is not None
            output_path.write_text("<nmaprun />", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, "", "")

        command = NmapCommandBuilder(executable="nmap").build(
            "example.invalid",
            Path(".tmp-tests/nmap-executor/nmap.xml"),
        )
        executor = NmapExecutor(
            runner=runner,
            executable_lookup=lambda executable: f"/usr/bin/{executable}",
            timeout_seconds=123,
        )

        result = executor.run(command)

        self.assertEqual(received["command"], command)
        self.assertEqual(received["timeout"], 123)
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(result.output_path and result.output_path.exists())

    def test_executor_requires_nmap_executable(self) -> None:
        command = NmapCommandBuilder(executable="nmap").build("example.invalid")
        executor = NmapExecutor(executable_lookup=lambda _executable: None)

        with self.assertRaises(FileNotFoundError):
            executor.run(command)


if __name__ == "__main__":
    unittest.main()
