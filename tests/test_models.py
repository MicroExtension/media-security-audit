from __future__ import annotations

import sys
import unittest
from pathlib import Path

from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.models import ScopeItem, ScopeType  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()

