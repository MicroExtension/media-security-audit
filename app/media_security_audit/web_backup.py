"""Workspace backup exports for local appliance operations."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from media_security_audit.models import utc_now
from media_security_audit.storage import JsonStore


@dataclass(frozen=True)
class WorkspaceBackupLink:
    filename: str
    size_bytes: int


def workspace_backup_dir(reports_dir: Path) -> Path:
    return reports_dir / "_workspace-backups"


def workspace_backup_path(reports_dir: Path) -> Path:
    return workspace_backup_dir(reports_dir) / "workspace-backup.zip"


def generate_workspace_backup(data_dir: Path, reports_dir: Path) -> Path:
    store = JsonStore(data_dir)
    clients = store.list_clients()
    missions = store.list_missions()
    output_path = workspace_backup_path(reports_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data_files = list_files(data_dir)
    report_files = [
        path
        for path in list_files(reports_dir)
        if not is_within(path, workspace_backup_dir(reports_dir))
        and path.resolve() != output_path.resolve()
    ]
    manifest = {
        "generated_at": utc_now().isoformat(),
        "client_count": len(clients),
        "mission_count": len(missions),
        "data_file_count": len(data_files),
        "report_file_count": len(report_files),
        "data_root": str(data_dir),
        "reports_root": str(reports_dir),
    }

    with ZipFile(output_path, mode="w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
        for path in data_files:
            archive.write(path, prefixed_relative_path("data", data_dir, path))
        for path in report_files:
            archive.write(path, prefixed_relative_path("reports", reports_dir, path))

    return output_path


def list_workspace_backup(reports_dir: Path) -> WorkspaceBackupLink | None:
    path = workspace_backup_path(reports_dir)
    if not path.exists() or not path.is_file():
        return None
    return WorkspaceBackupLink(filename=path.name, size_bytes=path.stat().st_size)


def workspace_backup_file(reports_dir: Path) -> Path:
    path = workspace_backup_path(reports_dir)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError("workspace backup not found")
    return path


def list_files(root: Path) -> list[Path]:
    if not root.exists() or not root.is_dir():
        return []
    return sorted(path for path in root.rglob("*") if path.is_file())


def prefixed_relative_path(prefix: str, root: Path, path: Path) -> str:
    relative = path.relative_to(root)
    return str(Path(prefix) / relative).replace("\\", "/")


def is_within(path: Path, directory: Path) -> bool:
    try:
        path.resolve().relative_to(directory.resolve())
    except ValueError:
        return False
    return True
