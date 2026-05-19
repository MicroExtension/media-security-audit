"""Deployment preflight checks for local appliance operations."""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from media_security_audit.web_auth import WebAuthSettings, web_auth_settings_from_env
from media_security_audit.web_system import build_system_status


PREFLIGHT_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class PreflightItem:
    category: str
    label: str
    status: str
    detail: str


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
        )
    ]
    items.extend(
        PreflightItem(
            category="storage",
            label=path.label,
            status=path.status,
            detail=path.detail,
        )
        for path in system_status.paths
    )
    items.append(
        PreflightItem(
            category="inventory",
            label="Workspace inventory",
            status=system_status.inventory.status,
            detail=inventory_detail(system_status.inventory),
        )
    )
    items.extend(
        PreflightItem(
            category="tool",
            label=tool.label,
            status=tool.status,
            detail=tool.detail if tool.status == "ready" else tool.path,
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
            }
            for item in preflight.items
        ],
    }


def format_deployment_preflight(preflight: DeploymentPreflight) -> str:
    lines = [f"Deployment preflight: {preflight.status}"]
    for item in preflight.items:
        lines.append(f"[{item.status}] {item.category}: {item.label} - {item.detail}")
    return "\n".join(lines)


def format_deployment_preflight_json(preflight: DeploymentPreflight) -> str:
    return json.dumps(deployment_preflight_payload(preflight), indent=2, sort_keys=True)
