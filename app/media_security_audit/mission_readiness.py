"""Mission readiness exports for guarded audit operations."""

from __future__ import annotations

import json
from pathlib import Path

from media_security_audit.scan_plan_exports import scan_plan_payload
from media_security_audit.storage import JsonStore
from media_security_audit.web_readiness import ReadinessItem, build_readiness_items
from media_security_audit.web_reports import list_generated_reports


MISSION_READINESS_SCHEMA_VERSION = 1


def readiness_status(items: list[ReadinessItem]) -> str:
    statuses = {item.status for item in items}
    if "blocked" in statuses:
        return "blocked"
    if "warning" in statuses:
        return "warning"
    return "ready"


def readiness_summary(items: list[ReadinessItem]) -> dict[str, int]:
    return {
        status: sum(1 for item in items if item.status == status)
        for status in ("ready", "warning", "blocked")
    }


def build_mission_readiness_payload(
    store: JsonStore,
    mission_id: str,
    reports_dir: Path,
) -> dict[str, object]:
    mission = store.get_mission(mission_id)
    findings = store.list_findings(mission_id)
    report_count = len(list_generated_reports(mission_id, reports_dir))
    items = build_readiness_items(mission, findings, report_count)
    summary = readiness_summary(items)
    return {
        "schema_version": MISSION_READINESS_SCHEMA_VERSION,
        "mission": {
            "id": mission.id,
            "name": mission.name,
            "status": mission.status.value,
        },
        "status": readiness_status(items),
        "summary": {
            **summary,
            "items": len(items),
            "findings": len(findings),
            "generated_reports": report_count,
            "execution": "not_executed",
        },
        "items": [
            {
                "label": item.label,
                "status": item.status,
                "detail": item.detail,
                "action_label": item.action_label,
                "action_href": item.action_href,
            }
            for item in items
        ],
        "scan_plan": scan_plan_payload(mission)["summary"],
    }


def format_mission_readiness_json(
    store: JsonStore,
    mission_id: str,
    reports_dir: Path,
) -> str:
    return json.dumps(
        build_mission_readiness_payload(store, mission_id, reports_dir),
        indent=2,
        sort_keys=True,
    )


def format_mission_readiness_text(
    store: JsonStore,
    mission_id: str,
    reports_dir: Path,
) -> str:
    payload = build_mission_readiness_payload(store, mission_id, reports_dir)
    mission = payload["mission"]
    summary = payload["summary"]
    lines = [
        f"Mission readiness: {payload['status']}",
        f"Mission: {mission['name']}",
        f"Mission ID: {mission['id']}",
        f"Mission status: {mission['status']}",
        f"Ready items: {summary['ready']}",
        f"Warning items: {summary['warning']}",
        f"Blocked items: {summary['blocked']}",
        f"Findings: {summary['findings']}",
        f"Generated reports: {summary['generated_reports']}",
        "Execution: not executed by this command",
        "",
    ]
    for item in payload["items"]:
        action = f" | action: {item['action_label']} {item['action_href']}".rstrip()
        action_suffix = action if item["action_label"] else ""
        lines.append(
            f"[{item['status']}] {item['label']}: {item['detail']}{action_suffix}"
        )

    scan_plan = payload["scan_plan"]
    lines.extend(
        [
            "",
            "Scan plan summary:",
            f"- ready checks: {scan_plan['ready']}",
            f"- blocked checks: {scan_plan['blocked']}",
            f"- planned commands: {scan_plan['planned_commands']}",
            f"- execution: {scan_plan['execution']}",
        ]
    )
    return "\n".join(lines)


def mission_readiness_exit_code(payload: dict[str, object], strict: bool = False) -> int:
    status = payload["status"]
    if status == "blocked":
        return 1
    if strict and status == "warning":
        return 1
    return 0
