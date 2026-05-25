from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.models import ScopeItem, ScopeType, Severity  # noqa: E402
from media_security_audit.scanners.smb import (  # noqa: E402
    SmbCommandBuilder,
    SmbExecutor,
    approved_smb_targets,
    findings_from_smb_shares,
    parse_smbclient_listing,
    smb_target_from_command,
    validate_smb_command,
    validate_smb_target,
)


class SmbScannerTests(unittest.TestCase):
    def test_filters_approved_smb_targets_only(self) -> None:
        scope = [
            ScopeItem(type=ScopeType.IP, value="192.0.2.10", approved=True),
            ScopeItem(type=ScopeType.HOST, value="FS01.CLIENT.LOCAL", approved=True),
            ScopeItem(type=ScopeType.DOMAIN, value="client.example", approved=True),
            ScopeItem(type=ScopeType.URL, value="https://client.example", approved=True),
            ScopeItem(type=ScopeType.CIDR, value="192.0.2.0/24", approved=True),
            ScopeItem(type=ScopeType.HOST, value="draft.client.local"),
            ScopeItem(type=ScopeType.IP, value="192.0.2.11", excluded=True),
        ]

        self.assertEqual(
            approved_smb_targets(scope),
            ["192.0.2.10", "fs01.client.local", "client.example"],
        )

    def test_rejects_invalid_smb_targets(self) -> None:
        invalid_targets = [
            "",
            "-host",
            "file server",
            "https://client.example",
            "//client.example/share",
            "DOMAIN\\user",
            "user@host",
        ]
        for target in invalid_targets:
            with self.subTest(target=target):
                with self.assertRaises(ValueError):
                    validate_smb_target(target)

    def test_builds_guarded_smbclient_command(self) -> None:
        command = SmbCommandBuilder().build("FS01.CLIENT.LOCAL")

        self.assertEqual(command[0], "smbclient")
        self.assertEqual(command[1:5], ["-L", "//fs01.client.local", "-N", "-g"])
        self.assertIn("--option=client min protocol=SMB2", command)
        self.assertIn("--option=client max protocol=SMB3", command)
        self.assertEqual(smb_target_from_command(command), "fs01.client.local")

    def test_rejects_unsafe_smbclient_commands(self) -> None:
        for command in [
            ["smbclient", "-L", "//client.example", "-U", "user"],
            ["smbclient", "-L", "//client.example", "-c", "dir"],
            ["smbclient", "-L", "//client.example", "-m", "NT1"],
            ["smbclient", "-L", "//client.example", "--option=client min protocol=NT1"],
        ]:
            with self.subTest(command=command):
                with self.assertRaises(ValueError):
                    validate_smb_command(command)

    def test_parses_smbclient_listing_and_generates_findings(self) -> None:
        fixture = Path(__file__).parent / "fixtures" / "smbclient_list_sample.txt"

        shares = parse_smbclient_listing(fixture.read_text(encoding="utf-8"), "client-fs")
        findings = findings_from_smb_shares(shares)

        self.assertEqual([share.name for share in shares[:3]], ["Public", "Finance", "ADMIN$"])
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].title, "Anonymous SMB listing exposes disk shares")
        self.assertEqual(findings[0].severity, Severity.MEDIUM)
        self.assertIn("Public", findings[0].proof)
        self.assertNotIn("ADMIN$", findings[0].proof)

    def test_generates_low_finding_for_ipc_only_listing(self) -> None:
        shares = parse_smbclient_listing("IPC|IPC$|IPC Service\n", "client-fs")
        findings = findings_from_smb_shares(shares)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].severity, Severity.LOW)
        self.assertEqual(findings[0].title, "Anonymous SMB listing is available")

    def test_executor_uses_prebuilt_command_without_shell(self) -> None:
        fixture = Path(__file__).parent / "fixtures" / "smbclient_list_sample.txt"
        command = SmbCommandBuilder().build("client-fs")

        def runner(
            command_args: list[str],
            timeout_seconds: int,
        ) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(
                command_args,
                0,
                fixture.read_text(encoding="utf-8"),
                "",
            )

        result = SmbExecutor(
            runner=runner,
            executable_lookup=lambda executable: f"/usr/bin/{executable}",
        ).run(command)

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.target, "client-fs")
        self.assertIn("Disk|Public", result.stdout)


if __name__ == "__main__":
    unittest.main()
