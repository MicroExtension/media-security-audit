from pathlib import Path
import shutil
import unittest

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.web_health import (  # noqa: E402
    build_health_status,
    health_status_code,
)


def clean_data_dir(name: str) -> Path:
    data_dir = Path(__file__).resolve().parents[1] / ".tmp-tests" / name
    if data_dir.exists():
        if data_dir.is_dir():
            shutil.rmtree(data_dir)
        else:
            data_dir.unlink()
    return data_dir


class WebHealthTests(unittest.TestCase):
    def test_health_status_reports_ready_storage_without_paths(self) -> None:
        root = clean_data_dir("web-health-ready")
        data_dir = root / "data"
        reports_dir = root / "reports"
        data_dir.mkdir(parents=True)
        reports_dir.mkdir(parents=True)

        payload = build_health_status(data_dir, reports_dir)

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(
            payload["checks"],
            {
                "data_directory": "ready",
                "reports_directory": "ready",
            },
        )
        self.assertNotIn(str(data_dir), str(payload))
        self.assertEqual(health_status_code(payload), 200)

    def test_health_status_blocks_when_storage_path_is_not_directory(self) -> None:
        root = clean_data_dir("web-health-blocked")
        data_dir = root / "data"
        reports_dir = root / "reports"
        data_dir.parent.mkdir(parents=True)
        data_dir.write_text("not a directory", encoding="utf-8")
        reports_dir.mkdir()

        payload = build_health_status(data_dir, reports_dir)

        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["checks"]["data_directory"], "blocked")
        self.assertEqual(payload["checks"]["reports_directory"], "ready")
        self.assertEqual(health_status_code(payload), 503)


if __name__ == "__main__":
    unittest.main()
