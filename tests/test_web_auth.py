from pathlib import Path
import unittest

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.web_auth import (  # noqa: E402
    parse_bool,
    valid_credentials,
    web_auth_settings_from_env,
)


class WebAuthTests(unittest.TestCase):
    def test_auth_is_disabled_by_default_for_direct_local_runs(self) -> None:
        settings = web_auth_settings_from_env({})

        self.assertFalse(settings.enabled)
        self.assertTrue(valid_credentials(settings, None, None))

    def test_auth_requires_password_when_enabled(self) -> None:
        with self.assertRaises(RuntimeError) as error:
            web_auth_settings_from_env({"MEDIA_AUDIT_REQUIRE_AUTH": "true"})

        self.assertIn("MEDIA_AUDIT_WEB_PASSWORD is required", str(error.exception))

    def test_auth_rejects_placeholder_and_short_passwords(self) -> None:
        with self.assertRaises(RuntimeError):
            web_auth_settings_from_env(
                {
                    "MEDIA_AUDIT_REQUIRE_AUTH": "true",
                    "MEDIA_AUDIT_WEB_PASSWORD": "change-this-password",
                }
            )

        with self.assertRaises(RuntimeError):
            web_auth_settings_from_env(
                {
                    "MEDIA_AUDIT_REQUIRE_AUTH": "true",
                    "MEDIA_AUDIT_WEB_PASSWORD": "short",
                }
            )

    def test_auth_accepts_expected_credentials_only(self) -> None:
        settings = web_auth_settings_from_env(
            {
                "MEDIA_AUDIT_REQUIRE_AUTH": "true",
                "MEDIA_AUDIT_WEB_USERNAME": "operator",
                "MEDIA_AUDIT_WEB_PASSWORD": "very-long-password",
            }
        )

        self.assertTrue(settings.enabled)
        self.assertTrue(valid_credentials(settings, "operator", "very-long-password"))
        self.assertFalse(valid_credentials(settings, "operator", "wrong-password"))
        self.assertFalse(valid_credentials(settings, "admin", "very-long-password"))

    def test_parse_bool_accepts_common_values(self) -> None:
        self.assertTrue(parse_bool("yes"))
        self.assertTrue(parse_bool("1"))
        self.assertFalse(parse_bool("no"))
        self.assertFalse(parse_bool("0"))
        self.assertFalse(parse_bool(None, default=False))
        self.assertTrue(parse_bool(None, default=True))

        with self.assertRaises(RuntimeError):
            parse_bool("maybe")


if __name__ == "__main__":
    unittest.main()
