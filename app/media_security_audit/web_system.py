"""Local appliance status helpers for the web UI."""

from __future__ import annotations

import os
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from media_security_audit.storage import JsonStore
from media_security_audit.web_auth import WebAuthSettings
from media_security_audit.web_backup import WorkspaceBackupLink, list_workspace_backup
from media_security_audit.web_inventory import WorkspaceInventory, build_workspace_inventory


@dataclass(frozen=True)
class PathStatus:
    label: str
    path: str
    status: str
    detail: str


@dataclass(frozen=True)
class ToolStatus:
    label: str
    command: str
    status: str
    detail: str
    path: str


@dataclass(frozen=True)
class AuthStatus:
    status: str
    detail: str
    username: str
    realm: str


@dataclass(frozen=True)
class SystemStatus:
    auth: AuthStatus
    paths: list[PathStatus]
    tools: list[ToolStatus]
    workspace_backup: WorkspaceBackupLink | None
    inventory: WorkspaceInventory


TOOL_CHECKS: tuple[tuple[str, str, str], ...] = (
    ("Nmap", "nmap", "Required for guarded Nmap execution."),
    ("testssl.sh", "testssl.sh", "Required for guarded TLS execution."),
    ("Nuclei", "nuclei", "Optional future template checks."),
    ("smbclient", "smbclient", "Planned for SMB checks."),
    ("ldapsearch", "ldapsearch", "Planned for LDAP checks."),
)


def build_system_status(
    data_dir: Path,
    reports_dir: Path,
    auth_settings: WebAuthSettings,
    tool_resolver: Callable[[str], str | None] = shutil.which,
) -> SystemStatus:
    store = JsonStore(data_dir)
    return SystemStatus(
        auth=auth_status(auth_settings),
        paths=[
            path_status("Data directory", data_dir),
            path_status("Reports directory", reports_dir),
        ],
        tools=[
            tool_status(label, command, purpose, tool_resolver)
            for label, command, purpose in TOOL_CHECKS
        ],
        workspace_backup=list_workspace_backup(reports_dir),
        inventory=build_workspace_inventory(store, reports_dir),
    )


def auth_status(settings: WebAuthSettings) -> AuthStatus:
    if settings.enabled:
        return AuthStatus(
            status="ready",
            detail="Authentication is required for protected web pages.",
            username=settings.username,
            realm=settings.realm,
        )
    return AuthStatus(
        status="warning",
        detail="Authentication is disabled for this local web session.",
        username=settings.username,
        realm=settings.realm,
    )


def path_status(label: str, path: Path) -> PathStatus:
    if path.exists() and path.is_dir():
        writable = os.access(path, os.W_OK)
        detail = (
            "Directory exists and is writable."
            if writable
            else "Directory exists but is not writable."
        )
        return PathStatus(
            label=label,
            path=str(path),
            status="ready" if writable else "blocked",
            detail=detail,
        )

    if path.exists():
        return PathStatus(
            label=label,
            path=str(path),
            status="blocked",
            detail="Path exists but is not a directory.",
        )

    parent = path.parent if path.parent != Path("") else Path(".")
    parent_writable = parent.exists() and os.access(parent, os.W_OK)
    return PathStatus(
        label=label,
        path=str(path),
        status="warning" if parent_writable else "blocked",
        detail=(
            "Directory will be created when data is written."
            if parent_writable
            else "Parent directory is missing or not writable."
        ),
    )


def tool_status(
    label: str,
    command: str,
    purpose: str,
    tool_resolver: Callable[[str], str | None],
) -> ToolStatus:
    resolved_path = tool_resolver(command)
    if resolved_path:
        return ToolStatus(
            label=label,
            command=command,
            status="ready",
            detail=purpose,
            path=resolved_path,
        )
    return ToolStatus(
        label=label,
        command=command,
        status="missing",
        detail=purpose,
        path="not found in PATH",
    )
