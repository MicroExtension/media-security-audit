from pathlib import Path
import json
import shutil
import unittest

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.deployment_preflight import (  # noqa: E402
    build_deployment_preflight,
    format_deployment_preflight,
    format_deployment_preflight_json,
    preflight_exit_code,
    preflight_summary,
)
from media_security_audit.web_auth import WebAuthSettings  # noqa: E402


def clean_dir(name: str) -> Path:
    path = Path(__file__).resolve().parents[1] / ".tmp-tests" / name
    if path.exists():
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    return path


class DeploymentPreflightTests(unittest.TestCase):
    def test_preflight_reports_ready_without_running_tools(self) -> None:
        root = clean_dir("deployment-preflight-ready")
        data_dir = root / "data"
        reports_dir = root / "reports"
        data_dir.mkdir(parents=True)
        reports_dir.mkdir()
        calls: list[str] = []

        def resolver(command: str) -> str:
            calls.append(command)
            return f"/usr/bin/{command}"

        preflight = build_deployment_preflight(
            data_dir=data_dir,
            reports_dir=reports_dir,
            auth_settings=WebAuthSettings(
                enabled=True,
                username="operator",
                password="long-secure-password",
            ),
            tool_resolver=resolver,
        )

        self.assertEqual(preflight.status, "ready")
        self.assertEqual(preflight_exit_code(preflight), 0)
        self.assertIn("nmap", calls)
        output = format_deployment_preflight(preflight)
        self.assertIn("Deployment preflight: ready", output)
        self.assertIn("[ready] auth: Web authentication", output)
        self.assertIn("[ready] storage: Data directory", output)
        self.assertNotIn("Action:", output)

    def test_preflight_blocks_when_storage_is_invalid(self) -> None:
        root = clean_dir("deployment-preflight-blocked")
        data_dir = root / "data"
        reports_dir = root / "reports"
        data_dir.parent.mkdir(parents=True)
        data_dir.write_text("not a directory", encoding="utf-8")
        reports_dir.mkdir()

        preflight = build_deployment_preflight(
            data_dir=data_dir,
            reports_dir=reports_dir,
            auth_settings=WebAuthSettings(
                enabled=True,
                username="operator",
                password="long-secure-password",
            ),
            tool_resolver=lambda command: None,
        )

        self.assertEqual(preflight.status, "blocked")
        self.assertEqual(preflight_exit_code(preflight), 1)
        self.assertTrue(
            any(
                item.category == "storage"
                and item.label == "Data directory"
                and item.status == "blocked"
                for item in preflight.items
            )
        )

    def test_preflight_warns_for_disabled_auth_and_missing_tools(self) -> None:
        root = clean_dir("deployment-preflight-warning")
        data_dir = root / "data"
        reports_dir = root / "reports"
        data_dir.mkdir(parents=True)
        reports_dir.mkdir()

        preflight = build_deployment_preflight(
            data_dir=data_dir,
            reports_dir=reports_dir,
            auth_settings=WebAuthSettings(enabled=False),
            tool_resolver=lambda command: None,
        )

        self.assertEqual(preflight.status, "warning")
        self.assertEqual(preflight_exit_code(preflight), 0)
        self.assertEqual(preflight_exit_code(preflight, strict=True), 1)
        self.assertGreaterEqual(preflight_summary(preflight)["missing"], 1)
        self.assertTrue(any(item.category == "auth" for item in preflight.items))
        self.assertTrue(any(item.status == "missing" for item in preflight.items))
        output = format_deployment_preflight(preflight)
        self.assertIn("Action: Enable MEDIA_AUDIT_REQUIRE_AUTH=true", output)
        self.assertIn("Action: Install nmap", output)
        self.assertIn("V1 pilot UI can continue without it", output)
        self.assertIn("Install nuclei only when the Nuclei module is enabled", output)

    def test_preflight_formats_json_for_automation(self) -> None:
        root = clean_dir("deployment-preflight-json")
        data_dir = root / "data"
        reports_dir = root / "reports"
        data_dir.mkdir(parents=True)
        reports_dir.mkdir()

        preflight = build_deployment_preflight(
            data_dir=data_dir,
            reports_dir=reports_dir,
            auth_settings=WebAuthSettings(
                enabled=True,
                username="operator",
                password="long-secure-password",
            ),
            tool_resolver=lambda command: f"/usr/bin/{command}",
        )

        payload = json.loads(format_deployment_preflight_json(preflight))

        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["summary"]["blocked"], 0)
        self.assertEqual(payload["summary"]["missing"], 0)
        self.assertGreaterEqual(payload["summary"]["ready"], 1)
        self.assertEqual(payload["items"][0]["category"], "auth")
        self.assertEqual(payload["items"][0]["status"], "ready")
        self.assertEqual(payload["items"][0]["action"], "No action required.")
        self.assertNotIn(str(data_dir), json.dumps(payload))


if __name__ == "__main__":
    unittest.main()
