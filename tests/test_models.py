from __future__ import annotations

import sys
import unittest
from pathlib import Path

from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.models import AuditCheck, Mission, ScopeItem, ScopeType  # noqa: E402


class ScopeItemTests(unittest.TestCase):
    def test_accepts_valid_cidr(self) -> None:
        item = ScopeItem(type=ScopeType.CIDR, value="192.168.1.0/24", approved=True)

        self.assertEqual(item.value, "192.168.1.0/24")

    def test_rejects_invalid_ip(self) -> None:
        with self.assertRaises(ValidationError):
            ScopeItem(type=ScopeType.IP, value="999.999.999.999")

    def test_rejects_approved_and_excluded_scope(self) -> None:
        with self.assertRaises(ValidationError):
            ScopeItem(type=ScopeType.DOMAIN, value="example.invalid", approved=True, excluded=True)


class MissionTests(unittest.TestCase):
    def test_default_selected_checks_are_safe_foundation_modules(self) -> None:
        mission = Mission(client_id="client_1", name="Audit")

        self.assertEqual(
            mission.selected_checks,
            [AuditCheck.NMAP, AuditCheck.HTTP_HEADERS, AuditCheck.DNS_MAIL],
        )

    def test_selected_checks_are_deduplicated(self) -> None:
        mission = Mission(
            client_id="client_1",
            name="Audit",
            selected_checks=[AuditCheck.NMAP, AuditCheck.NMAP, AuditCheck.DNS_MAIL],
        )

        self.assertEqual(mission.selected_checks, [AuditCheck.NMAP, AuditCheck.DNS_MAIL])


if __name__ == "__main__":
    unittest.main()
