"""Healthcheck payload for local appliance deployments."""

from __future__ import annotations

from pathlib import Path

from media_security_audit.web_system import path_status


def build_health_status(data_dir: Path, reports_dir: Path) -> dict[str, object]:
    checks = {
        "data_directory": path_status("Data directory", data_dir).status,
        "reports_directory": path_status("Reports directory", reports_dir).status,
    }
    blocked = any(status == "blocked" for status in checks.values())
    warning = any(status == "warning" for status in checks.values())

    return {
        "status": "blocked" if blocked else "degraded" if warning else "ok",
        "checks": checks,
    }


def health_status_code(payload: dict[str, object]) -> int:
    return 503 if payload.get("status") == "blocked" else 200
