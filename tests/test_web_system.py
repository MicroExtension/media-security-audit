from pathlib import Path
import shutil
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.web_auth import WebAuthSettings  # noqa: E402
from media_security_audit.web_system import build_system_status  # noqa: E402


def clean_data_dir(name: str) -> Path:
    data_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / name
    if data_dir.exists():
        shutil.rmtree(data_dir)
    return data_dir


class WebSystemTests(unittest.TestCase):
    def test_system_template_exposes_shortcut_anchors(self) -> None:
        template_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "media_security_audit"
            / "web_templates"
            / "system.html"
        )
        template = template_path.read_text(encoding="utf-8")

        for anchor in [
            "system-auth",
            "system-storage",
            "system-inventory",
            "system-backup",
            "system-tooling-plan",
            "system-tools",
        ]:
            self.assertIn(f'href="#{anchor}"', template)
            self.assertIn(f'id="{anchor}"', template)

        for counter in [
            "view.auth.status",
            "view.paths | length",
            "view.inventory.status",
            '"ready" if view.workspace_backup else "none"',
            "view.tools | length",
        ]:
            self.assertIn(f"{{{{ {counter} }}}}", template)
        for tool_field in [
            "tool.phase",
            "tool.requirement",
            "tool.pilot_blocking",
            "tool.action",
        ]:
            self.assertIn(tool_field, template)

    def test_builds_local_system_status_without_running_tools(self) -> None:
        data_dir = clean_data_dir("web-system-status")
        reports_dir = data_dir / "reports"
        data_dir.mkdir(parents=True)
        reports_dir.mkdir()

        calls: list[str] = []

        def resolver(command: str) -> str | None:
            calls.append(command)
            if command == "nmap":
                return "/usr/bin/nmap"
            return None

        status = build_system_status(
            data_dir=data_dir,
            reports_dir=reports_dir,
            auth_settings=WebAuthSettings(enabled=True, username="operator", password="secret"),
            tool_resolver=resolver,
        )

        self.assertEqual(status.auth.status, "ready")
        self.assertEqual(status.auth.username, "operator")
        self.assertTrue(all(item.status == "ready" for item in status.paths))
        self.assertIn("nmap", calls)
        self.assertEqual(status.tools[0].label, "Nmap")
        self.assertEqual(status.tools[0].status, "ready")
        self.assertEqual(status.tools[0].requirement, "pilot required")
        self.assertTrue(status.tools[0].pilot_blocking)
        self.assertEqual(status.tools[1].status, "missing")
        self.assertEqual(status.tools[1].requirement, "module required")
        self.assertFalse(status.tools[1].pilot_blocking)
        self.assertIn("V1 pilot UI", status.tools[1].action)
        self.assertIsNone(status.workspace_backup)
        self.assertEqual(status.inventory.status, "ready")
        self.assertEqual(status.inventory.metrics[0].label, "Clients")

    def test_missing_path_and_disabled_auth_are_reported_safely(self) -> None:
        root = clean_data_dir("web-system-missing")

        status = build_system_status(
            data_dir=root / "data",
            reports_dir=root / "reports",
            auth_settings=WebAuthSettings(enabled=False),
            tool_resolver=lambda command: None,
        )

        self.assertEqual(status.auth.status, "warning")
        self.assertTrue(all(item.status == "blocked" for item in status.paths))
        self.assertTrue(all(tool.status == "missing" for tool in status.tools))
        self.assertFalse(status.tools[2].pilot_blocking)
        self.assertEqual(status.tools[2].requirement, "future optional")
        self.assertIsNone(status.workspace_backup)
        self.assertEqual(status.inventory.status, "ready")


if __name__ == "__main__":
    unittest.main()
