from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import unittest
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.models import Client, Finding, Mission, Severity  # noqa: E402
from media_security_audit.storage import JsonStore  # noqa: E402
from media_security_audit.web_backup import (  # noqa: E402
    generate_workspace_backup,
    list_workspace_backup,
    workspace_backup_file,
)
from media_security_audit.web_reports import generate_web_reports  # noqa: E402


def clean_dir(name: str) -> Path:
    path = Path(__file__).resolve().parents[1] / ".tmp-tests" / name
    if path.exists():
        shutil.rmtree(path)
    return path


class WebBackupTests(unittest.TestCase):
    def test_generates_workspace_backup_package(self) -> None:
        data_dir = clean_dir("web-backup-data")
        reports_dir = clean_dir("web-backup-reports")
        store = JsonStore(data_dir)
        client = store.create_client(Client(name="Client Backup"))
        mission = store.create_mission(Mission(client_id=client.id, name="Backup Audit"))
        store.add_finding(
            mission.id,
            Finding(
                title="Backup finding",
                severity=Severity.LOW,
                affected_asset="client.example",
                category="manual",
                source_module="manual",
                proof="Observed manually.",
                risk="Risk pending review.",
                remediation="Apply remediation.",
                counter_test="Repeat the check.",
                confidence=0.8,
            ),
        )
        generate_web_reports(store, mission.id, reports_dir)

        backup_path = generate_workspace_backup(data_dir, reports_dir)

        self.assertEqual(backup_path, workspace_backup_file(reports_dir))
        self.assertEqual(list_workspace_backup(reports_dir).filename, "workspace-backup.zip")
        with ZipFile(backup_path) as archive:
            names = set(archive.namelist())
            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))

        self.assertEqual(manifest["client_count"], 1)
        self.assertEqual(manifest["mission_count"], 1)
        self.assertGreaterEqual(manifest["data_file_count"], 3)
        self.assertGreaterEqual(manifest["report_file_count"], 3)
        self.assertIn(f"data/clients/{client.id}.json", names)
        self.assertIn(f"data/missions/{mission.id}.json", names)
        self.assertIn(f"reports/{mission.id}/{mission.id}.html", names)
        self.assertNotIn("reports/_workspace-backups/workspace-backup.zip", names)

    def test_backup_can_be_generated_when_directories_are_empty(self) -> None:
        data_dir = clean_dir("web-backup-empty-data")
        reports_dir = clean_dir("web-backup-empty-reports")

        backup_path = generate_workspace_backup(data_dir, reports_dir)

        with ZipFile(backup_path) as archive:
            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))

        self.assertEqual(manifest["client_count"], 0)
        self.assertEqual(manifest["mission_count"], 0)
        self.assertEqual(manifest["data_file_count"], 0)
        self.assertEqual(manifest["report_file_count"], 0)

    def test_missing_workspace_backup_has_named_error(self) -> None:
        reports_dir = clean_dir("web-backup-missing")

        with self.assertRaises(FileNotFoundError) as error:
            workspace_backup_file(reports_dir)

        self.assertIn("workspace backup not found", str(error.exception))


if __name__ == "__main__":
    unittest.main()
