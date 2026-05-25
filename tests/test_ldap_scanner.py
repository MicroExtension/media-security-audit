from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.models import ScopeItem, ScopeType, Severity  # noqa: E402
from media_security_audit.scanners.ldap import (  # noqa: E402
    LdapCommandBuilder,
    LdapExecutor,
    approved_ldap_targets,
    findings_from_root_dse,
    ldap_target_from_command,
    parse_ldap_root_dse,
    validate_ldap_command,
    validate_ldap_target,
)


class LdapScannerTests(unittest.TestCase):
    def test_filters_approved_ldap_targets_only(self) -> None:
        scope = [
            ScopeItem(type=ScopeType.IP, value="192.0.2.10", approved=True),
            ScopeItem(type=ScopeType.HOST, value="DC01.CLIENT.LOCAL", approved=True),
            ScopeItem(type=ScopeType.DOMAIN, value="client.local", approved=True),
            ScopeItem(type=ScopeType.URL, value="https://client.example", approved=True),
            ScopeItem(type=ScopeType.CIDR, value="192.0.2.0/24", approved=True),
            ScopeItem(type=ScopeType.HOST, value="draft.client.local"),
        ]

        self.assertEqual(
            approved_ldap_targets(scope),
            ["192.0.2.10", "dc01.client.local", "client.local"],
        )

    def test_rejects_invalid_ldap_targets(self) -> None:
        invalid_targets = [
            "",
            "-host",
            "domain controller",
            "ldap://client.local",
            "client.local/base",
            "DOMAIN\\user",
            "user@host",
        ]
        for target in invalid_targets:
            with self.subTest(target=target):
                with self.assertRaises(ValueError):
                    validate_ldap_target(target)

    def test_builds_guarded_ldapsearch_command(self) -> None:
        command = LdapCommandBuilder().build("DC01.CLIENT.LOCAL")

        self.assertEqual(command[0], "ldapsearch")
        self.assertIn("-x", command)
        self.assertIn("-LLL", command)
        self.assertEqual(command[command.index("-H") + 1], "ldap://dc01.client.local")
        self.assertEqual(command[command.index("-s") + 1], "base")
        self.assertEqual(command[command.index("-b") + 1], "")
        self.assertEqual(ldap_target_from_command(command), "dc01.client.local")

    def test_rejects_unsafe_ldapsearch_commands(self) -> None:
        unsafe_commands = [
            ["ldapsearch", "-x", "-H", "ldap://dc01.client.local", "-D", "cn=admin"],
            ["ldapsearch", "-x", "-H", "ldap://dc01.client.local", "-w", "secret"],
            ["ldapsearch", "-x", "-H", "ldap://dc01.client.local", "-f", "targets.txt"],
            ["ldapsearch", "-x", "-H", "ldap://dc01.client.local", "-e", "pr=100"],
            ["ldapsearch", "-x", "-H", "ldap://dc01.client.local", "-s", "sub", "-b", ""],
            ["ldapsearch", "-x", "-H", "ldaps://dc01.client.local", "-s", "base", "-b", ""],
        ]
        for command in unsafe_commands:
            with self.subTest(command=command):
                with self.assertRaises(ValueError):
                    validate_ldap_command(command)

    def test_parses_root_dse_and_generates_findings(self) -> None:
        fixture = Path(__file__).parent / "fixtures" / "ldap_rootdse_sample.ldif"

        root_dse = parse_ldap_root_dse(fixture.read_text(encoding="utf-8"), "dc01.client.local")
        findings = findings_from_root_dse(root_dse)
        titles = {finding.title for finding in findings}

        self.assertEqual(root_dse.naming_contexts[0], "DC=client,DC=local")
        self.assertIn("LDAPv2 is advertised by directory service", titles)
        self.assertIn("LDAP advertises anonymous SASL mechanism", titles)
        self.assertIn("LDAP RootDSE exposes naming contexts", titles)
        self.assertTrue(any(finding.severity == Severity.MEDIUM for finding in findings))
        self.assertTrue(all(finding.category == "ldap" for finding in findings))

    def test_executor_uses_prebuilt_command_without_shell(self) -> None:
        fixture = Path(__file__).parent / "fixtures" / "ldap_rootdse_sample.ldif"
        command = LdapCommandBuilder().build("dc01.client.local")

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

        result = LdapExecutor(
            runner=runner,
            executable_lookup=lambda executable: f"/usr/bin/{executable}",
        ).run(command)

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.target, "dc01.client.local")
        self.assertIn("namingContexts", result.stdout)


if __name__ == "__main__":
    unittest.main()
