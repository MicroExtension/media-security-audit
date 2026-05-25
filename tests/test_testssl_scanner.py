from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.models import ScopeItem, ScopeType, Severity  # noqa: E402
from media_security_audit.scanners.testssl import (  # noqa: E402
    TestsslCommandBuilder,
    TestsslExecutor,
    approved_tls_targets,
    parse_testssl_json,
    testssl_output_path,
    tls_target_from_url,
    validate_testssl_command,
    validate_tls_target,
)


class TestsslScannerTests(unittest.TestCase):
    def test_filters_approved_tls_targets_only(self) -> None:
        scope = [
            ScopeItem(type=ScopeType.URL, value="https://client.example/login", approved=True),
            ScopeItem(type=ScopeType.DOMAIN, value="client.example", approved=True),
            ScopeItem(type=ScopeType.CIDR, value="192.0.2.0/24", approved=True),
            ScopeItem(type=ScopeType.HOST, value="draft.client.example"),
            ScopeItem(type=ScopeType.IP, value="192.0.2.10", excluded=True),
        ]

        self.assertEqual(approved_tls_targets(scope), ["client.example"])

    def test_rejects_invalid_tls_targets(self) -> None:
        invalid_targets = [
            "",
            "-client.example",
            "client example",
            "https://client.example",
            "user@host",
        ]
        for target in invalid_targets:
            with self.subTest(target=target):
                with self.assertRaises(ValueError):
                    validate_tls_target(target)

        for url in ["http://client.example", "https://user:pass@client.example", "https:///"]:
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    tls_target_from_url(url)

    def test_builds_conservative_testssl_command(self) -> None:
        output_path = Path("runs/mission_1/evidence/testssl-1.json")
        command = TestsslCommandBuilder().build("client.example", output_path=output_path)

        self.assertEqual(command[0], "testssl.sh")
        self.assertIn("--warnings", command)
        self.assertIn("batch", command)
        self.assertIn("--severity", command)
        self.assertIn("MEDIUM", command)
        self.assertEqual(testssl_output_path(command), output_path)
        self.assertEqual(command[-1], "client.example")

    def test_rejects_unsafe_testssl_commands(self) -> None:
        with self.assertRaises(ValueError):
            validate_testssl_command(["testssl.sh", "--parallel", "client.example"])
        with self.assertRaises(ValueError):
            validate_testssl_command(["testssl.sh", "--openssl", "/tmp/openssl", "client.example"])

    def test_parses_testssl_json_findings(self) -> None:
        fixture = Path(__file__).parent / "fixtures" / "testssl_sample.json"

        findings = parse_testssl_json(fixture.read_text(encoding="utf-8"), "client.example")
        titles = {finding.title for finding in findings}

        self.assertEqual(len(findings), 2)
        self.assertIn("TLS finding: TLS1", titles)
        self.assertIn("TLS finding: cipher-rc4", titles)
        self.assertTrue(any(finding.severity == Severity.HIGH for finding in findings))
        self.assertTrue(all(finding.category == "tls" for finding in findings))
        self.assertTrue(all(finding.source_module == "testssl" for finding in findings))

    def test_executor_uses_prebuilt_command_without_shell(self) -> None:
        fixture = Path(__file__).parent / "fixtures" / "testssl_sample.json"
        output_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / "testssl-executor"
        command = TestsslCommandBuilder().build(
            "client.example",
            output_path=output_dir / "testssl-1.json",
        )

        def runner(
            command_args: list[str],
            timeout_seconds: int,
        ) -> subprocess.CompletedProcess[str]:
            output_path = testssl_output_path(command_args)
            assert output_path is not None
            output_path.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")
            return subprocess.CompletedProcess(command_args, 0, "", "")

        result = TestsslExecutor(
            runner=runner,
            executable_lookup=lambda executable: f"/usr/bin/{executable}",
        ).run(command)

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.target, "client.example")
        self.assertTrue(result.output_path and result.output_path.exists())


if __name__ == "__main__":
    unittest.main()
