from pathlib import Path
import shutil
import unittest

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.deployment_preflight import (  # noqa: E402
    build_deployment_preflight,
    format_deployment_preflight,
    preflight_exit_code,
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
        self.assertTrue(any(item.category == "auth" for item in preflight.items))
        self.assertTrue(any(item.status == "missing" for item in preflight.items))


if __name__ == "__main__":
    unittest.main()
