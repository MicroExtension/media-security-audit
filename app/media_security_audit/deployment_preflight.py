"""Deployment preflight checks for local appliance operations."""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from media_security_audit.web_auth import WebAuthSettings, web_auth_settings_from_env
from media_security_audit.web_system import PathStatus, ToolStatus, build_system_status


PREFLIGHT_SCHEMA_VERSION = 1
NO_ACTION_REQUIRED = "No action required."


@dataclass(frozen=True)
class PreflightItem:
    category: str
    label: str
    status: str
    detail: str
    action: str


@dataclass(frozen=True)
class DeploymentPreflight:
    status: str
    items: list[PreflightItem]


def build_deployment_preflight(
    data_dir: Path,
    reports_dir: Path,
    auth_settings: WebAuthSettings | None = None,
    tool_resolver: Callable[[str], str | None] = shutil.which,
) -> DeploymentPreflight:
    auth_error = ""
    if auth_settings is None:
        try:
            auth_settings = web_auth_settings_from_env()
        except RuntimeError as error:
            auth_settings = WebAuthSettings(enabled=True)
            auth_error = str(error)

    system_status = build_system_status(
        data_dir=data_dir,
        reports_dir=reports_dir,
        auth_settings=auth_settings,
        tool_resolver=tool_resolver,
    )

    items = [
        PreflightItem(
            category="auth",
            label="Web authentication",
            status="blocked" if auth_error else system_status.auth.status,
            detail=auth_error or system_status.auth.detail,
            action=auth_action("blocked" if auth_error else system_status.auth.status, auth_error),
        )
    ]
    items.extend(
        PreflightItem(
            category="storage",
            label=path.label,
            status=path.status,
            detail=path.detail,
            action=storage_action(path),
        )
        for path in system_status.paths
    )
    items.append(
        PreflightItem(
            category="inventory",
            label="Workspace inventory",
            status=system_status.inventory.status,
            detail=inventory_detail(system_status.inventory),
            action=inventory_action(system_status.inventory.status),
        )
    )
    items.extend(
        PreflightItem(
            category="tool",
            label=tool.label,
            status=tool.status,
            detail=tool.detail if tool.status == "ready" else tool.path,
            action=tool_action(tool),
        )
        for tool in system_status.tools
    )

    return DeploymentPreflight(status=overall_status(items), items=items)


def inventory_detail(inventory: object) -> str:
    issues = getattr(inventory, "issues", [])
    if issues:
        return issues[0].detail
    metric_count = len(getattr(inventory, "metrics", []))
    return f"{metric_count} workspace metric(s) checked."


def auth_action(status: str, auth_error: str) -> str:
    if status == "ready":
        return NO_ACTION_REQUIRED
    if auth_error:
        return "Set valid web authentication environment variables before startup."
    return "Enable MEDIA_AUDIT_REQUIRE_AUTH=true and set a strong web password before LAN use."


def storage_action(path: PathStatus) -> str:
    if path.status == "ready":
        return NO_ACTION_REQUIRED
    if "not a directory" in path.detail:
        return "Replace this path with a directory or configure a different location."
    if "not writable" in path.detail:
        return "Fix ownership or write permissions for the application user."
    if path.status == "warning":
        return "Create this directory during install for a deterministic deployment."
    return "Create the parent directory and grant write permission to the application user."


def inventory_action(status: str) -> str:
    if status == "ready":
        return NO_ACTION_REQUIRED
    return "Review workspace inventory issues before customer handoff."


def tool_action(tool: ToolStatus) -> str:
    if tool.status == "ready":
        return NO_ACTION_REQUIRED
    return f"Install {tool.command} on the VM or document why it is intentionally unavailable."


def overall_status(items: list[PreflightItem]) -> str:
    statuses = {item.status for item in items}
    if "blocked" in statuses:
        return "blocked"
    if statuses & {"warning", "missing"}:
        return "warning"
    return "ready"


def preflight_exit_code(preflight: DeploymentPreflight, strict: bool = False) -> int:
    if preflight.status == "blocked":
        return 1
    if strict and preflight.status == "warning":
        return 1
    return 0


def preflight_summary(preflight: DeploymentPreflight) -> dict[str, int]:
    statuses = ("ready", "warning", "missing", "blocked")
    return {
        status: sum(1 for item in preflight.items if item.status == status)
        for status in statuses
    }


def deployment_preflight_payload(preflight: DeploymentPreflight) -> dict[str, object]:
    return {
        "schema_version": PREFLIGHT_SCHEMA_VERSION,
        "status": preflight.status,
        "summary": preflight_summary(preflight),
        "items": [
            {
                "category": item.category,
                "label": item.label,
                "status": item.status,
                "detail": item.detail,
                "action": item.action,
            }
            for item in preflight.items
        ],
    }


def format_deployment_preflight(preflight: DeploymentPreflight) -> str:
    lines = [f"Deployment preflight: {preflight.status}"]
    for item in preflight.items:
        lines.append(f"[{item.status}] {item.category}: {item.label} - {item.detail}")
        if item.action != NO_ACTION_REQUIRED:
            lines.append(f"  Action: {item.action}")
    return "\n".join(lines)


def format_deployment_preflight_json(preflight: DeploymentPreflight) -> str:
    return json.dumps(deployment_preflight_payload(preflight), indent=2, sort_keys=True)
