"""Pilot runbook content for first client deployments."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, replace
from hashlib import sha256
from io import BytesIO, StringIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from media_security_audit.storage import JsonStore
from media_security_audit.web_exports import build_mission_export_inventory
from media_security_audit.web_system import SystemStatus

PILOT_BUNDLE_TIMESTAMP = (2026, 1, 1, 0, 0, 0)
PILOT_BUNDLE_REVIEW_ORDER = [
    "pilot-handoff-summary.md",
    "pilot-handoff-summary.json",
    "pilot-bundle-index.md",
    "pilot-bundle-index.json",
    "pilot-bundle-inventory.json",
    "pilot-attention.md",
    "pilot-attention.json",
    "pilot-readiness.md",
    "pilot-readiness.json",
    "pilot-acceptance-checklist.md",
    "pilot-acceptance-checklist.json",
    "pilot-runbook.md",
    "pilot-runbook.json",
    "pilot-delivery-receipt.md",
    "pilot-delivery-receipt.json",
    "pilot-final-handoff-checklist.md",
    "pilot-final-handoff-checklist.json",
    "manifest.json",
]

PILOT_BUNDLE_FILE_PURPOSES = {
    "manifest.json": "File checksums for integrity review.",
    "pilot-acceptance-checklist.md": "Beta acceptance checklist.",
    "pilot-acceptance-checklist.json": "Machine-readable beta acceptance checklist.",
    "pilot-attention.md": "Remaining warnings and blockers.",
    "pilot-attention.json": "Machine-readable attention items.",
    "pilot-bundle-index.md": "Review order for extracted evidence.",
    "pilot-bundle-index.json": "Machine-readable review order.",
    "pilot-bundle-inventory.json": "Machine-readable bundle inventory.",
    "pilot-delivery-receipt.md": "Delivery sign-off receipt.",
    "pilot-delivery-receipt.json": "Machine-readable delivery receipt.",
    "pilot-final-handoff-checklist.md": "Final handoff checklist for delivery review.",
    "pilot-final-handoff-checklist.json": "Machine-readable final handoff checklist.",
    "pilot-handoff-summary.md": "Compact handoff state and next actions.",
    "pilot-handoff-summary.json": "Machine-readable handoff state.",
    "pilot-readiness.md": "Detailed local readiness checks.",
    "pilot-readiness.json": "Machine-readable readiness state.",
    "pilot-runbook.md": "Technician workflow.",
    "pilot-runbook.json": "Machine-readable technician workflow.",
}


@dataclass(frozen=True)
class PilotRunbookMetric:
    label: str
    value: str


@dataclass(frozen=True)
class PilotRunbookLink:
    label: str
    href: str


@dataclass(frozen=True)
class PilotRunbookStep:
    title: str
    detail: str


@dataclass(frozen=True)
class PilotAcceptanceItem:
    phase: str
    title: str
    evidence: str


@dataclass(frozen=True)
class PilotReadinessItem:
    label: str
    status: str
    detail: str
    href: str


@dataclass(frozen=True)
class PilotReadinessRollup:
    status: str
    ready: int
    warning: int
    blocked: int
    total: int
    detail: str


@dataclass(frozen=True)
class PilotHandoffDecision:
    status: str
    title: str
    detail: str
    action_label: str
    action_href: str


@dataclass(frozen=True)
class PilotRunbookSection:
    anchor: str
    title: str
    links: list[PilotRunbookLink]
    steps: list[PilotRunbookStep]


@dataclass(frozen=True)
class PilotEvidenceFileView:
    path: str
    category: str
    kind: str
    review_order: int
    purpose: str
    size_bytes: int
    sha256: str
    sha256_short: str


@dataclass(frozen=True)
class PilotRunbookView:
    title: str
    subtitle: str
    metrics: list[PilotRunbookMetric]
    sections: list[PilotRunbookSection]
    acceptance_items: list[PilotAcceptanceItem]
    readiness_items: list[PilotReadinessItem]
    attention_items: list[PilotReadinessItem]
    readiness_rollup: PilotReadinessRollup
    handoff_decision: PilotHandoffDecision
    evidence_files: list[PilotEvidenceFileView]
    evidence_automation_file_count: int
    evidence_human_file_count: int
    evidence_manifest_file_count: int
    evidence_archive_file_count: int
    evidence_total_size_bytes: int
    evidence_archive_total_size_bytes: int


@dataclass(frozen=True)
class PilotEvidenceBundle:
    filename: str
    media_type: str
    content: bytes


@dataclass(frozen=True)
class PilotEvidenceManifest:
    filename: str
    media_type: str
    content: str
    payload: dict[str, object]


@dataclass(frozen=True)
class PilotEvidenceVerification:
    filename: str
    media_type: str
    content: str


@dataclass(frozen=True)
class PilotEvidenceVerificationJson:
    filename: str
    media_type: str
    content: str
    payload: dict[str, object]


@dataclass(frozen=True)
class PilotRunbookJsonExport:
    filename: str
    media_type: str
    content: str
    payload: dict[str, object]


@dataclass(frozen=True)
class PilotAttentionExport:
    filename: str
    media_type: str
    content: str


@dataclass(frozen=True)
class PilotAttentionJsonExport:
    filename: str
    media_type: str
    content: str
    payload: dict[str, object]


@dataclass(frozen=True)
class PilotHandoffSummaryExport:
    filename: str
    media_type: str
    content: str


@dataclass(frozen=True)
class PilotHandoffSummaryJsonExport:
    filename: str
    media_type: str
    content: str
    payload: dict[str, object]


@dataclass(frozen=True)
class PilotBundleIndexExport:
    filename: str
    media_type: str
    content: str


@dataclass(frozen=True)
class PilotBundleIndexJsonExport:
    filename: str
    media_type: str
    content: str
    payload: dict[str, object]


@dataclass(frozen=True)
class PilotBundleInventoryJsonExport:
    filename: str
    media_type: str
    content: str
    payload: dict[str, object]


@dataclass(frozen=True)
class PilotReadinessJsonExport:
    filename: str
    media_type: str
    content: str
    payload: dict[str, object]


@dataclass(frozen=True)
class PilotAcceptanceJsonExport:
    filename: str
    media_type: str
    content: str
    payload: dict[str, object]


@dataclass(frozen=True)
class PilotDeliveryReceiptExport:
    filename: str
    media_type: str
    content: str


@dataclass(frozen=True)
class PilotDeliveryReceiptJsonExport:
    filename: str
    media_type: str
    content: str
    payload: dict[str, object]


@dataclass(frozen=True)
class PilotFinalHandoffChecklistExport:
    filename: str
    media_type: str
    content: str


@dataclass(frozen=True)
class PilotFinalHandoffChecklistJsonExport:
    filename: str
    media_type: str
    content: str
    payload: dict[str, object]


@dataclass(frozen=True)
class PilotBundleInventoryCsvExport:
    filename: str
    media_type: str
    content: str


def build_pilot_runbook_view(
    readiness_items: list[PilotReadinessItem] | None = None,
) -> PilotRunbookView:
    readiness_items = readiness_items or []
    attention_items = build_pilot_attention_items(readiness_items)
    readiness_rollup = build_pilot_readiness_rollup(readiness_items)
    view = PilotRunbookView(
        title="Pilot Runbook",
        subtitle="Client Pilot",
        metrics=[
            PilotRunbookMetric(label="Phase", value="5"),
            PilotRunbookMetric(label="Mode", value="Local"),
            PilotRunbookMetric(label="Scans", value="Guarded"),
            PilotRunbookMetric(label="Output", value="Reports"),
        ],
        acceptance_items=[
            PilotAcceptanceItem(
                phase="Setup",
                title="Appliance status reviewed",
                evidence="System status page checked before client use.",
            ),
            PilotAcceptanceItem(
                phase="Mission",
                title="Client and mission created",
                evidence="Client detail and mission page exist in the dashboard.",
            ),
            PilotAcceptanceItem(
                phase="Mission",
                title="Authorization details completed",
                evidence="Authorization reference, contact, dates, and recipients are recorded.",
            ),
            PilotAcceptanceItem(
                phase="Mission",
                title="Approved scope recorded",
                evidence="Only validated scope items are approved for the mission.",
            ),
            PilotAcceptanceItem(
                phase="Mission",
                title="Checks selected from approved scope",
                evidence="Selected checks match authorization and visible scan plan previews.",
            ),
            PilotAcceptanceItem(
                phase="Review",
                title="Findings reviewed",
                evidence="False positives, accepted risks, and counter-test results have notes.",
            ),
            PilotAcceptanceItem(
                phase="Handoff",
                title="Reports generated",
                evidence="JSON, Markdown, and HTML reports are available from the mission.",
            ),
            PilotAcceptanceItem(
                phase="Handoff",
                title="Mission package generated",
                evidence="Mission ZIP package is available with manifest and verification links.",
            ),
            PilotAcceptanceItem(
                phase="Handoff",
                title="Export inventory verified",
                evidence="Mission export inventory shows the package as ready or reviewed.",
            ),
            PilotAcceptanceItem(
                phase="Closeout",
                title="Workspace backup created",
                evidence="System backup package exists before closing the pilot session.",
            ),
            PilotAcceptanceItem(
                phase="Closeout",
                title="Residual risks recorded",
                evidence="Accepted risks and pending counter-tests are visible for follow-up.",
            ),
        ],
        readiness_items=readiness_items,
        attention_items=attention_items,
        readiness_rollup=readiness_rollup,
        handoff_decision=build_pilot_handoff_decision(
            readiness_rollup,
            attention_items,
        ),
        evidence_files=[],
        evidence_automation_file_count=0,
        evidence_human_file_count=0,
        evidence_manifest_file_count=0,
        evidence_archive_file_count=0,
        evidence_total_size_bytes=0,
        evidence_archive_total_size_bytes=0,
        sections=[
            PilotRunbookSection(
                anchor="pilot-setup",
                title="Setup",
                links=[
                    PilotRunbookLink(label="System", href="/system"),
                    PilotRunbookLink(label="Templates", href="/templates"),
                ],
                steps=[
                    PilotRunbookStep(
                        title="Check appliance status",
                        detail=(
                            "Confirm authentication, storage, tool visibility, "
                            "and backup readiness."
                        ),
                    ),
                    PilotRunbookStep(
                        title="Select pilot template",
                        detail=(
                            "Use a restrained audit profile aligned with the "
                            "approved maintenance scope."
                        ),
                    ),
                    PilotRunbookStep(
                        title="Record client context",
                        detail=(
                            "Keep notes, reference, contacts, and retention "
                            "details ready before mission setup."
                        ),
                    ),
                ],
            ),
            PilotRunbookSection(
                anchor="pilot-mission",
                title="Mission",
                links=[
                    PilotRunbookLink(label="Dashboard", href="/"),
                    PilotRunbookLink(label="Templates", href="/templates"),
                ],
                steps=[
                    PilotRunbookStep(
                        title="Create client and mission",
                        detail=(
                            "Use the dashboard form and attach the selected "
                            "audit template when relevant."
                        ),
                    ),
                    PilotRunbookStep(
                        title="Complete authorization",
                        detail=(
                            "Add authorization reference, contact, dates, "
                            "emergency contact, and recipients."
                        ),
                    ),
                    PilotRunbookStep(
                        title="Approve scope",
                        detail=(
                            "Mark only validated IP, CIDR, domain, URL, and "
                            "host entries as approved."
                        ),
                    ),
                    PilotRunbookStep(
                        title="Select checks",
                        detail=(
                            "Keep selected checks aligned with authorization "
                            "and visible scan plan previews."
                        ),
                    ),
                ],
            ),
            PilotRunbookSection(
                anchor="pilot-review",
                title="Review",
                links=[
                    PilotRunbookLink(label="Activity", href="/activity"),
                    PilotRunbookLink(label="Remediations", href="/remediations"),
                ],
                steps=[
                    PilotRunbookStep(
                        title="Import or record findings",
                        detail=(
                            "Use manual findings or guarded CLI outputs that "
                            "stay inside approved scope."
                        ),
                    ),
                    PilotRunbookStep(
                        title="Review dispositions",
                        detail=(
                            "Add notes for false positives, accepted risks, "
                            "and counter-test decisions."
                        ),
                    ),
                    PilotRunbookStep(
                        title="Validate remediation wording",
                        detail=(
                            "Use remediation suggestions as a baseline, then "
                            "adapt to client context."
                        ),
                    ),
                    PilotRunbookStep(
                        title="Check activity trace",
                        detail=(
                            "Confirm mission events show the preparation and "
                            "review path."
                        ),
                    ),
                ],
            ),
            PilotRunbookSection(
                anchor="pilot-handoff",
                title="Handoff",
                links=[
                    PilotRunbookLink(label="Exports", href="/exports"),
                    PilotRunbookLink(label="Backup", href="/system#system-backup"),
                ],
                steps=[
                    PilotRunbookStep(
                        title="Generate reports",
                        detail=(
                            "Create JSON, Markdown, and HTML reports from the "
                            "reviewed mission page."
                        ),
                    ),
                    PilotRunbookStep(
                        title="Generate mission package",
                        detail=(
                            "Package reports, readiness, scan plan, manifest, "
                            "and evidence references."
                        ),
                    ),
                    PilotRunbookStep(
                        title="Verify export inventory",
                        detail=(
                            "Use the export inventory to confirm package "
                            "integrity before delivery."
                        ),
                    ),
                    PilotRunbookStep(
                        title="Create workspace backup",
                        detail="Generate a local backup before closing the pilot session.",
                    ),
                ],
            ),
            PilotRunbookSection(
                anchor="pilot-closeout",
                title="Closeout",
                links=[],
                steps=[
                    PilotRunbookStep(
                        title="Record residual risks",
                        detail=(
                            "Keep accepted risks and pending counter-tests "
                            "visible for the next visit."
                        ),
                    ),
                    PilotRunbookStep(
                        title="Save delivery evidence",
                        detail=(
                            "Keep package manifests, verification files, and "
                            "export inventory with the mission."
                        ),
                    ),
                    PilotRunbookStep(
                        title="Plan next iteration",
                        detail=(
                            "Use client feedback to tune templates, wording, "
                            "and remediation priorities."
                        ),
                    ),
                ],
            ),
        ],
    )
    evidence_files = build_pilot_evidence_file_views(readiness_items, view)
    manifest_file_count = len(
        [path for path in PILOT_BUNDLE_REVIEW_ORDER if path == "manifest.json"]
    )
    automation_file_count = len(
        [item for item in evidence_files if item.category == "automation"]
    )
    human_file_count = len(
        [item for item in evidence_files if item.category == "human"]
    )
    evidence_total_size_bytes = sum(item.size_bytes for item in evidence_files)
    view = replace(
        view,
        evidence_files=evidence_files,
        evidence_automation_file_count=automation_file_count,
        evidence_human_file_count=human_file_count,
        evidence_manifest_file_count=manifest_file_count,
        evidence_archive_file_count=len(evidence_files) + manifest_file_count,
        evidence_total_size_bytes=evidence_total_size_bytes,
    )
    return replace(
        view,
        evidence_archive_total_size_bytes=(
            evidence_total_size_bytes
            + pilot_visible_manifest_size_bytes(evidence_files, view)
        ),
    )


def build_pilot_attention_items(
    readiness_items: list[PilotReadinessItem],
) -> list[PilotReadinessItem]:
    return [item for item in readiness_items if item.status != "ready"]


def build_pilot_readiness_rollup(
    readiness_items: list[PilotReadinessItem],
) -> PilotReadinessRollup:
    ready = len([item for item in readiness_items if item.status == "ready"])
    warning = len([item for item in readiness_items if item.status == "warning"])
    blocked = len([item for item in readiness_items if item.status == "blocked"])
    total = len(readiness_items)
    if blocked:
        status = "blocked"
    elif warning or not total:
        status = "warning"
    else:
        status = "ready"
    detail = (
        "No readiness item was generated."
        if not total
        else f"{ready} ready, {warning} warning, {blocked} blocked."
    )
    return PilotReadinessRollup(
        status=status,
        ready=ready,
        warning=warning,
        blocked=blocked,
        total=total,
        detail=detail,
    )


def build_pilot_handoff_decision(
    readiness_rollup: PilotReadinessRollup,
    attention_items: list[PilotReadinessItem],
) -> PilotHandoffDecision:
    if readiness_rollup.status == "ready":
        return PilotHandoffDecision(
            status="ready",
            title="Ready for pilot handoff",
            detail=(
                "All Pilot readiness checks are ready. Download the evidence "
                "bundle, verify checksums, and complete the delivery receipt."
            ),
            action_label="Download Bundle",
            action_href="/pilot/bundle.zip",
        )
    if readiness_rollup.status == "blocked":
        return PilotHandoffDecision(
            status="blocked",
            title="Blocked before pilot handoff",
            detail=(
                f"{readiness_rollup.blocked} blocked readiness check(s) must "
                "be resolved before the Pilot bundle is delivered."
            ),
            action_label="Resolve Blockers",
            action_href="#pilot-attention" if attention_items else "/system",
        )
    if attention_items:
        return PilotHandoffDecision(
            status="warning",
            title="Review before pilot handoff",
            detail=(
                f"{len(attention_items)} attention item(s) should be reviewed "
                "before the Pilot bundle is delivered."
            ),
            action_label="Review Attention",
            action_href="#pilot-attention",
        )
    return PilotHandoffDecision(
        status="warning",
        title="Readiness review required",
        detail=(
            "No Pilot readiness item was generated yet. Review system status "
            "and workspace exports before delivering the Pilot bundle."
        ),
        action_label="Review System",
        action_href="/system",
    )


def build_pilot_readiness_items(
    store: JsonStore,
    reports_dir: Path,
    system_status: SystemStatus,
) -> list[PilotReadinessItem]:
    clients = store.list_clients()
    missions = store.list_missions()
    export_items = build_mission_export_inventory(store, reports_dir, include_missing=True)
    package_items = [item for item in export_items if item.status != "missing"]
    ready_packages = [item for item in package_items if item.status == "ready"]
    ready_paths = [item for item in system_status.paths if item.status == "ready"]
    ready_tools = [item for item in system_status.tools if item.status == "ready"]

    return [
        PilotReadinessItem(
            label="Web authentication",
            status=system_status.auth.status,
            detail=system_status.auth.detail,
            href="/system#system-auth",
        ),
        PilotReadinessItem(
            label="Storage readiness",
            status=readiness_rollup_status([item.status for item in system_status.paths]),
            detail=f"{len(ready_paths)}/{len(system_status.paths)} storage path(s) ready.",
            href="/system#system-storage",
        ),
        PilotReadinessItem(
            label="Client records",
            status="ready" if clients else "warning",
            detail=f"{len(clients)} client record(s) available.",
            href="/",
        ),
        PilotReadinessItem(
            label="Mission records",
            status="ready" if missions else "warning",
            detail=f"{len(missions)} mission record(s) available.",
            href="/",
        ),
        PilotReadinessItem(
            label="Mission exports",
            status="ready" if ready_packages else "warning",
            detail=(
                f"{len(ready_packages)} ready package(s), "
                f"{len(package_items)} package(s) total."
            ),
            href="/exports",
        ),
        PilotReadinessItem(
            label="Workspace backup",
            status="ready" if system_status.workspace_backup else "warning",
            detail=(
                system_status.workspace_backup.filename
                if system_status.workspace_backup
                else "No workspace backup package found."
            ),
            href="/system#system-backup",
        ),
        PilotReadinessItem(
            label="External tools",
            status="ready" if len(ready_tools) == len(system_status.tools) else "warning",
            detail=f"{len(ready_tools)}/{len(system_status.tools)} tool(s) available.",
            href="/system#system-tools",
        ),
    ]


def readiness_rollup_status(statuses: list[str]) -> str:
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if any(status != "ready" for status in statuses):
        return "warning"
    return "ready"


def format_pilot_runbook_markdown(view: PilotRunbookView | None = None) -> str:
    view = view or build_pilot_runbook_view()
    lines = [
        f"# {view.title}",
        "",
        f"- Context: `{view.subtitle}`",
    ]
    for metric in view.metrics:
        lines.append(f"- {metric.label}: `{metric.value}`")
    lines.extend(["", "## Workflow", ""])
    for section in view.sections:
        lines.extend([f"### {section.title}", ""])
        if section.links:
            links = ", ".join(f"[{link.label}]({link.href})" for link in section.links)
            lines.extend([f"Links: {links}", ""])
        for index, step in enumerate(section.steps, start=1):
            lines.append(f"{index}. **{step.title}**")
            lines.append(f"   {step.detail}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_pilot_runbook_json_export(
    view: PilotRunbookView | None = None,
) -> PilotRunbookJsonExport:
    view = view or build_pilot_runbook_view()
    payload = pilot_runbook_payload(view)
    return PilotRunbookJsonExport(
        filename="pilot-runbook.json",
        media_type="application/json",
        content=json.dumps(payload, indent=2, sort_keys=True) + "\n",
        payload=payload,
    )


def pilot_runbook_payload(view: PilotRunbookView) -> dict[str, object]:
    return {
        "acceptance_item_count": len(view.acceptance_items),
        "context": view.subtitle,
        "handoff_decision": pilot_handoff_decision_payload(view.handoff_decision),
        "metrics": [
            {"label": metric.label, "value": metric.value}
            for metric in view.metrics
        ],
        "readiness": {
            "blocked": view.readiness_rollup.blocked,
            "detail": view.readiness_rollup.detail,
            "ready": view.readiness_rollup.ready,
            "status": view.readiness_rollup.status,
            "total": view.readiness_rollup.total,
            "warning": view.readiness_rollup.warning,
        },
        "runbook_type": "pilot",
        "schema_version": 2,
        "sections": [
            {
                "anchor": section.anchor,
                "links": [
                    {"href": link.href, "label": link.label}
                    for link in section.links
                ],
                "steps": [
                    {"detail": step.detail, "title": step.title}
                    for step in section.steps
                ],
                "title": section.title,
            }
            for section in view.sections
        ],
        "source": view.title,
    }


def pilot_handoff_decision_payload(
    decision: PilotHandoffDecision,
) -> dict[str, object]:
    return {
        "action_href": decision.action_href,
        "action_label": decision.action_label,
        "detail": decision.detail,
        "status": decision.status,
        "title": decision.title,
    }


def format_pilot_acceptance_markdown(view: PilotRunbookView | None = None) -> str:
    view = view or build_pilot_runbook_view()
    lines = [
        "# Pilot Acceptance Checklist",
        "",
        f"- Context: `{view.subtitle}`",
        f"- Source: `{view.title}`",
        "",
        "## Checklist",
        "",
    ]
    for item in view.acceptance_items:
        lines.append(f"- [ ] **{item.phase}: {item.title}**")
        lines.append(f"  Evidence: {item.evidence}")
    return "\n".join(lines).rstrip() + "\n"


def build_pilot_acceptance_json_export(
    view: PilotRunbookView | None = None,
) -> PilotAcceptanceJsonExport:
    view = view or build_pilot_runbook_view()
    payload = pilot_acceptance_payload(view)
    return PilotAcceptanceJsonExport(
        filename="pilot-acceptance-checklist.json",
        media_type="application/json",
        content=json.dumps(payload, indent=2, sort_keys=True) + "\n",
        payload=payload,
    )


def pilot_acceptance_payload(view: PilotRunbookView) -> dict[str, object]:
    return {
        "acceptance_type": "pilot",
        "context": view.subtitle,
        "item_count": len(view.acceptance_items),
        "items": [
            {
                "evidence": item.evidence,
                "phase": item.phase,
                "status": "pending",
                "title": item.title,
            }
            for item in view.acceptance_items
        ],
        "schema_version": 1,
        "source": view.title,
    }


def format_pilot_readiness_markdown(
    readiness_items: list[PilotReadinessItem],
    view: PilotRunbookView | None = None,
) -> str:
    view = view or build_pilot_runbook_view(readiness_items=readiness_items)
    counts = {
        "ready": len([item for item in readiness_items if item.status == "ready"]),
        "warning": len([item for item in readiness_items if item.status == "warning"]),
        "blocked": len([item for item in readiness_items if item.status == "blocked"]),
    }
    lines = [
        "# Pilot Readiness Summary",
        "",
        f"- Context: `{view.subtitle}`",
        f"- Source: `{view.title}`",
        f"- Handoff decision: `{view.handoff_decision.status}`",
        f"- Handoff action: `{view.handoff_decision.action_label}`",
        f"- Ready: `{counts['ready']}`",
        f"- Warning: `{counts['warning']}`",
        f"- Blocked: `{counts['blocked']}`",
        "",
        "## Readiness",
        "",
        "| Check | Status | Detail | Review |",
        "| --- | --- | --- | --- |",
    ]
    if not readiness_items:
        lines.append("| None | warning | No readiness item was generated. | - |")
    for item in readiness_items:
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(item.label),
                    markdown_cell(item.status),
                    markdown_cell(item.detail),
                    markdown_cell(item.href),
                ]
            )
            + " |"
        )
    return "\n".join(lines).rstrip() + "\n"


def build_pilot_handoff_summary_export(
    readiness_items: list[PilotReadinessItem],
    view: PilotRunbookView | None = None,
) -> PilotHandoffSummaryExport:
    view = view or build_pilot_runbook_view(readiness_items=readiness_items)
    return PilotHandoffSummaryExport(
        filename="pilot-handoff-summary.md",
        media_type="text/markdown; charset=utf-8",
        content=format_pilot_handoff_summary_markdown(view),
    )


def build_pilot_handoff_summary_json_export(
    readiness_items: list[PilotReadinessItem],
    view: PilotRunbookView | None = None,
) -> PilotHandoffSummaryJsonExport:
    view = view or build_pilot_runbook_view(readiness_items=readiness_items)
    payload = pilot_handoff_summary_payload(view)
    return PilotHandoffSummaryJsonExport(
        filename="pilot-handoff-summary.json",
        media_type="application/json",
        content=json.dumps(payload, indent=2, sort_keys=True) + "\n",
        payload=payload,
    )


def pilot_handoff_summary_payload(view: PilotRunbookView) -> dict[str, object]:
    handoff_files = [
        "pilot-runbook.md",
        "pilot-acceptance-checklist.md",
        "pilot-acceptance-checklist.json",
        "pilot-handoff-summary.json",
        "pilot-bundle-index.md",
        "pilot-bundle-index.json",
        "pilot-bundle-inventory.json",
        "pilot-delivery-receipt.md",
        "pilot-delivery-receipt.json",
        "pilot-readiness.md",
        "pilot-readiness.json",
        "pilot-attention.md",
        "pilot-attention.json",
        "pilot-runbook.json",
        "pilot-final-handoff-checklist.md",
        "pilot-final-handoff-checklist.json",
        "manifest.json",
    ]
    return {
        "acceptance_items": len(view.acceptance_items),
        "automation_file_count": view.evidence_automation_file_count,
        "attention_items": [
            {
                "detail": item.detail,
                "href": item.href,
                "label": item.label,
                "status": item.status,
            }
            for item in view.attention_items
        ],
        "context": view.subtitle,
        "handoff_decision": pilot_handoff_decision_payload(view.handoff_decision),
        "handoff_file_count": len(handoff_files),
        "handoff_file_details": pilot_bundle_file_details(handoff_files),
        "handoff_files": handoff_files,
        "handoff_type": "pilot",
        "human_file_count": view.evidence_human_file_count,
        "manifest_file_count": 1,
        "next_action_count": len(view.attention_items),
        "readiness": {
            "blocked": view.readiness_rollup.blocked,
            "detail": view.readiness_rollup.detail,
            "ready": view.readiness_rollup.ready,
            "status": view.readiness_rollup.status,
            "total": view.readiness_rollup.total,
            "warning": view.readiness_rollup.warning,
        },
        "schema_version": 5,
        "source": view.title,
    }


def format_pilot_handoff_summary_markdown(
    view: PilotRunbookView | None = None,
) -> str:
    view = view or build_pilot_runbook_view()
    lines = [
        "# Pilot Handoff Summary",
        "",
        f"- Context: `{view.subtitle}`",
        f"- Source: `{view.title}`",
        f"- Readiness status: `{view.readiness_rollup.status}`",
        f"- Readiness detail: `{view.readiness_rollup.detail}`",
        f"- Handoff decision: `{view.handoff_decision.status}`",
        f"- Handoff action: `{view.handoff_decision.action_label}`",
        f"- Attention items: `{len(view.attention_items)}`",
        f"- Acceptance items: `{len(view.acceptance_items)}`",
        f"- Automation files: `{view.evidence_automation_file_count}`",
        f"- Human-readable files: `{view.evidence_human_file_count}`",
        "- Manifest files: `1`",
        "",
        "## Next Actions",
        "",
    ]
    if not view.attention_items:
        lines.append("- No attention item is currently open.")
    for item in view.attention_items:
        lines.append(
            f"- **{item.label}** (`{item.status}`): {item.detail} "
            f"[Review]({item.href})"
        )
    lines.extend(
        [
            "",
            "## Handoff Files",
            "",
        ]
    )
    handoff_files = pilot_handoff_summary_payload(view)["handoff_files"]
    if isinstance(handoff_files, list):
        lines.extend(
            format_pilot_bundle_file_table([str(path) for path in handoff_files])
        )
    return "\n".join(lines).rstrip() + "\n"


def build_pilot_bundle_index_export(
    readiness_items: list[PilotReadinessItem],
    view: PilotRunbookView | None = None,
) -> PilotBundleIndexExport:
    view = view or build_pilot_runbook_view(readiness_items=readiness_items)
    return PilotBundleIndexExport(
        filename="pilot-bundle-index.md",
        media_type="text/markdown; charset=utf-8",
        content=format_pilot_bundle_index_markdown(view),
    )


def build_pilot_bundle_index_json_export(
    readiness_items: list[PilotReadinessItem],
    view: PilotRunbookView | None = None,
) -> PilotBundleIndexJsonExport:
    view = view or build_pilot_runbook_view(readiness_items=readiness_items)
    payload = pilot_bundle_index_payload(view)
    return PilotBundleIndexJsonExport(
        filename="pilot-bundle-index.json",
        media_type="application/json",
        content=json.dumps(payload, indent=2, sort_keys=True) + "\n",
        payload=payload,
    )


def pilot_bundle_index_payload(view: PilotRunbookView) -> dict[str, object]:
    return {
        "automation_file_count": view.evidence_automation_file_count,
        "bundle_file_count": len(PILOT_BUNDLE_REVIEW_ORDER) - 1,
        "context": view.subtitle,
        "human_file_count": view.evidence_human_file_count,
        "index_type": "pilot_evidence",
        "manifest_file_count": 1,
        "readiness": {
            "attention_items": len(view.attention_items),
            "detail": view.readiness_rollup.detail,
            "status": view.readiness_rollup.status,
        },
        "review_order": [
            {
                "category": pilot_evidence_file_category(path),
                "kind": pilot_bundle_review_file_kind(path),
                "order": index,
                "path": path,
                "purpose": pilot_bundle_file_purpose(path),
            }
            for index, path in enumerate(PILOT_BUNDLE_REVIEW_ORDER, start=1)
        ],
        "review_step_count": len(PILOT_BUNDLE_REVIEW_ORDER),
        "schema_version": 3,
        "source": view.title,
    }


def format_pilot_bundle_index_markdown(
    view: PilotRunbookView | None = None,
) -> str:
    view = view or build_pilot_runbook_view()
    lines = [
        "# Pilot Evidence Bundle Index",
        "",
        f"- Context: `{view.subtitle}`",
        f"- Source: `{view.title}`",
        f"- Readiness status: `{view.readiness_rollup.status}`",
        f"- Attention items: `{len(view.attention_items)}`",
        f"- Automation files: `{view.evidence_automation_file_count}`",
        f"- Human-readable files: `{view.evidence_human_file_count}`",
        "- Manifest files: `1`",
        "",
        "## Recommended Review Order",
        "",
        "1. Open `pilot-handoff-summary.md` first for the current handoff state.",
        "2. Use `pilot-handoff-summary.json` when automation needs handoff state.",
        "3. Use `pilot-bundle-index.json` for structured review order.",
        "4. Review `pilot-bundle-inventory.json` for expected bundle files.",
        "5. Review `pilot-attention.md` for warnings or blockers.",
        "6. Use `pilot-attention.json` when automation needs attention items.",
        "7. Review `pilot-readiness.md` for detailed workspace readiness.",
        "8. Use `pilot-readiness.json` only when automation needs structured state.",
        "9. Complete `pilot-acceptance-checklist.md` for beta sign-off.",
        "10. Use `pilot-acceptance-checklist.json` for structured beta sign-off.",
        "11. Keep `pilot-runbook.md` with the technician delivery notes.",
        "12. Use `pilot-runbook.json` when automation needs workflow steps.",
        "13. Complete `pilot-delivery-receipt.md` after client handoff.",
        "14. Use `pilot-delivery-receipt.json` for structured delivery evidence.",
        "15. Complete `pilot-final-handoff-checklist.md` before archiving.",
        "16. Use `pilot-final-handoff-checklist.json` for structured closeout.",
        "17. Compare extracted files with `manifest.json` before archiving.",
        "",
        "## Bundle Files",
        "",
    ]
    lines.extend(format_pilot_bundle_file_table(PILOT_BUNDLE_REVIEW_ORDER))
    return "\n".join(lines).rstrip() + "\n"


def pilot_bundle_file_purpose(path: str) -> str:
    return PILOT_BUNDLE_FILE_PURPOSES.get(path, "Pilot evidence file.")


def pilot_bundle_review_file_kind(path: str) -> str:
    if path == "manifest.json":
        return "Manifest JSON"
    return pilot_evidence_file_kind(path)


def pilot_bundle_review_order(path: str) -> int:
    try:
        return PILOT_BUNDLE_REVIEW_ORDER.index(path) + 1
    except ValueError:
        return 0


def pilot_bundle_file_details(paths: list[str]) -> list[dict[str, object]]:
    return [
        {
            "category": pilot_evidence_file_category(path),
            "kind": pilot_bundle_review_file_kind(path),
            "path": path,
            "purpose": pilot_bundle_file_purpose(path),
            "review_order": pilot_bundle_review_order(path),
        }
        for path in paths
    ]


def format_pilot_bundle_file_table(paths: list[str]) -> list[str]:
    lines = [
        "| File | Category | Kind | Review | Purpose |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for item in pilot_bundle_file_details(paths):
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(item["path"]),
                    markdown_cell(item["category"]),
                    markdown_cell(item["kind"]),
                    markdown_cell(item["review_order"]),
                    markdown_cell(item["purpose"]),
                ]
            )
            + " |"
        )
    return lines


def build_pilot_attention_export(
    readiness_items: list[PilotReadinessItem],
    view: PilotRunbookView | None = None,
) -> PilotAttentionExport:
    view = view or build_pilot_runbook_view(readiness_items=readiness_items)
    return PilotAttentionExport(
        filename="pilot-attention.md",
        media_type="text/markdown; charset=utf-8",
        content=format_pilot_attention_markdown(view.attention_items, view),
    )


def build_pilot_attention_json_export(
    readiness_items: list[PilotReadinessItem],
    view: PilotRunbookView | None = None,
) -> PilotAttentionJsonExport:
    view = view or build_pilot_runbook_view(readiness_items=readiness_items)
    payload = pilot_attention_payload(view)
    return PilotAttentionJsonExport(
        filename="pilot-attention.json",
        media_type="application/json",
        content=json.dumps(payload, indent=2, sort_keys=True) + "\n",
        payload=payload,
    )


def pilot_attention_payload(view: PilotRunbookView) -> dict[str, object]:
    return {
        "attention_type": "pilot",
        "context": view.subtitle,
        "items": [
            {
                "detail": item.detail,
                "href": item.href,
                "label": item.label,
                "status": item.status,
            }
            for item in view.attention_items
        ],
        "open_item_count": len(view.attention_items),
        "readiness_status": view.readiness_rollup.status,
        "schema_version": 1,
        "source": view.title,
    }


def format_pilot_attention_markdown(
    attention_items: list[PilotReadinessItem],
    view: PilotRunbookView | None = None,
) -> str:
    view = view or build_pilot_runbook_view(readiness_items=attention_items)
    lines = [
        "# Pilot Attention Items",
        "",
        f"- Context: `{view.subtitle}`",
        f"- Source: `{view.title}`",
        f"- Open items: `{len(attention_items)}`",
        "",
        "## Attention",
        "",
        "| Check | Status | Detail | Review |",
        "| --- | --- | --- | --- |",
    ]
    if not attention_items:
        lines.append("| None | ready | No attention item is currently open. | - |")
    for item in attention_items:
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(item.label),
                    markdown_cell(item.status),
                    markdown_cell(item.detail),
                    markdown_cell(item.href),
                ]
            )
            + " |"
        )
    return "\n".join(lines).rstrip() + "\n"


def build_pilot_delivery_receipt_export(
    readiness_items: list[PilotReadinessItem],
    view: PilotRunbookView | None = None,
) -> PilotDeliveryReceiptExport:
    view = view or build_pilot_runbook_view(readiness_items=readiness_items)
    return PilotDeliveryReceiptExport(
        filename="pilot-delivery-receipt.md",
        media_type="text/markdown; charset=utf-8",
        content=format_pilot_delivery_receipt_markdown(view),
    )


def build_pilot_delivery_receipt_json_export(
    readiness_items: list[PilotReadinessItem],
    view: PilotRunbookView | None = None,
) -> PilotDeliveryReceiptJsonExport:
    view = view or build_pilot_runbook_view(readiness_items=readiness_items)
    payload = pilot_delivery_receipt_payload(view)
    return PilotDeliveryReceiptJsonExport(
        filename="pilot-delivery-receipt.json",
        media_type="application/json",
        content=json.dumps(payload, indent=2, sort_keys=True) + "\n",
        payload=payload,
    )


def pilot_delivery_receipt_payload(view: PilotRunbookView) -> dict[str, object]:
    delivered_files = [
        "pilot-handoff-summary.md",
        "pilot-handoff-summary.json",
        "pilot-bundle-index.md",
        "pilot-bundle-index.json",
        "pilot-bundle-inventory.json",
        "pilot-readiness.md",
        "pilot-readiness.json",
        "pilot-attention.md",
        "pilot-attention.json",
        "pilot-acceptance-checklist.md",
        "pilot-acceptance-checklist.json",
        "pilot-runbook.md",
        "pilot-runbook.json",
        "pilot-delivery-receipt.json",
        "pilot-final-handoff-checklist.md",
        "pilot-final-handoff-checklist.json",
        "manifest.json",
    ]
    return {
        "automation_file_count": view.evidence_automation_file_count,
        "attention_items": len(view.attention_items),
        "context": view.subtitle,
        "delivery_type": "pilot",
        "delivered_file_count": len(delivered_files),
        "delivered_file_details": pilot_bundle_file_details(delivered_files),
        "delivered_files": delivered_files,
        "human_file_count": view.evidence_human_file_count,
        "manifest_file_count": 1,
        "readiness": {
            "blocked": view.readiness_rollup.blocked,
            "detail": view.readiness_rollup.detail,
            "ready": view.readiness_rollup.ready,
            "status": view.readiness_rollup.status,
            "total": view.readiness_rollup.total,
            "warning": view.readiness_rollup.warning,
        },
        "schema_version": 4,
        "sign_off_fields": [
            "client_representative",
            "technician",
            "delivery_date",
            "delivery_channel",
            "remaining_attention_items_reviewed",
            "evidence_bundle_retained_by_msp",
        ],
        "source": view.title,
    }


def format_pilot_delivery_receipt_markdown(
    view: PilotRunbookView | None = None,
) -> str:
    view = view or build_pilot_runbook_view()
    lines = [
        "# Pilot Delivery Receipt",
        "",
        f"- Context: `{view.subtitle}`",
        f"- Source: `{view.title}`",
        f"- Readiness status: `{view.readiness_rollup.status}`",
        f"- Readiness detail: `{view.readiness_rollup.detail}`",
        f"- Attention items: `{len(view.attention_items)}`",
        f"- Automation files: `{view.evidence_automation_file_count}`",
        f"- Human-readable files: `{view.evidence_human_file_count}`",
        "- Manifest files: `1`",
        "",
        "## Delivered Files",
        "",
    ]
    delivered_files = pilot_delivery_receipt_payload(view)["delivered_files"]
    if isinstance(delivered_files, list):
        lines.extend(
            format_pilot_bundle_file_table([str(path) for path in delivered_files])
        )
    lines.extend(
        [
            "",
            "## Sign-off",
            "",
            "- Client representative: ______________________________",
            "- Technician: ______________________________",
            "- Delivery date: ______________________________",
            "- Delivery channel: ______________________________",
            "- Remaining attention items reviewed: [ ] yes  [ ] no",
            "- Evidence bundle retained by MSP: [ ] yes  [ ] no",
            "",
            "## Notes",
            "",
            "- ______________________________",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def build_pilot_final_handoff_checklist_export(
    readiness_items: list[PilotReadinessItem],
    view: PilotRunbookView | None = None,
) -> PilotFinalHandoffChecklistExport:
    view = view or build_pilot_runbook_view(readiness_items=readiness_items)
    return PilotFinalHandoffChecklistExport(
        filename="pilot-final-handoff-checklist.md",
        media_type="text/markdown; charset=utf-8",
        content=format_pilot_final_handoff_checklist_markdown(view),
    )


def build_pilot_final_handoff_checklist_json_export(
    readiness_items: list[PilotReadinessItem],
    view: PilotRunbookView | None = None,
) -> PilotFinalHandoffChecklistJsonExport:
    view = view or build_pilot_runbook_view(readiness_items=readiness_items)
    payload = pilot_final_handoff_checklist_payload(view)
    return PilotFinalHandoffChecklistJsonExport(
        filename="pilot-final-handoff-checklist.json",
        media_type="application/json",
        content=json.dumps(payload, indent=2, sort_keys=True) + "\n",
        payload=payload,
    )


def pilot_final_handoff_checklist_payload(
    view: PilotRunbookView,
) -> dict[str, object]:
    items = pilot_final_handoff_checklist_items(view)
    return {
        "attention_item_count": len(
            [item for item in items if item["status"] == "attention"]
        ),
        "checklist_type": "pilot_final_handoff",
        "context": view.subtitle,
        "handoff_decision": pilot_handoff_decision_payload(view.handoff_decision),
        "item_count": len(items),
        "items": items,
        "manual_item_count": len([item for item in items if item["status"] == "manual"]),
        "readiness": {
            "attention_items": len(view.attention_items),
            "blocked": view.readiness_rollup.blocked,
            "detail": view.readiness_rollup.detail,
            "ready": view.readiness_rollup.ready,
            "status": view.readiness_rollup.status,
            "total": view.readiness_rollup.total,
            "warning": view.readiness_rollup.warning,
        },
        "ready_item_count": len([item for item in items if item["status"] == "ready"]),
        "schema_version": 1,
        "source": view.title,
    }


def pilot_final_handoff_checklist_items(
    view: PilotRunbookView,
) -> list[dict[str, str]]:
    return [
        {
            "action_href": view.handoff_decision.action_href,
            "action_label": view.handoff_decision.action_label,
            "detail": view.handoff_decision.detail,
            "id": "review_handoff_decision",
            "label": "Review handoff decision",
            "status": "ready"
            if view.handoff_decision.status == "ready"
            else "attention",
        },
        {
            "action_href": "/pilot/readiness.md",
            "action_label": "Readiness",
            "detail": view.readiness_rollup.detail,
            "id": "verify_readiness",
            "label": "Verify readiness",
            "status": "ready"
            if view.readiness_rollup.status == "ready"
            else "attention",
        },
        {
            "action_href": "/pilot/attention.md",
            "action_label": "Attention",
            "detail": "No attention item is open."
            if not view.attention_items
            else f"{len(view.attention_items)} attention item(s) require review.",
            "id": "review_attention_items",
            "label": "Review attention items",
            "status": "ready" if not view.attention_items else "attention",
        },
        {
            "action_href": "/pilot/bundle.zip",
            "action_label": "Bundle",
            "detail": "Download the pilot evidence bundle from the local Pilot page.",
            "id": "download_evidence_bundle",
            "label": "Download evidence bundle",
            "status": "manual",
        },
        {
            "action_href": "/pilot/bundle-verification.md",
            "action_label": "Verify",
            "detail": "Compare extracted files with manifest hashes before archiving.",
            "id": "verify_bundle_manifest",
            "label": "Verify bundle manifest",
            "status": "manual",
        },
        {
            "action_href": "/pilot/delivery-receipt.md",
            "action_label": "Receipt",
            "detail": "Complete the delivery receipt after client handoff.",
            "id": "complete_delivery_receipt",
            "label": "Complete delivery receipt",
            "status": "manual",
        },
        {
            "action_href": "/pilot/bundle-manifest.json",
            "action_label": "Manifest",
            "detail": "Archive the manifest, verification output, and signed receipt.",
            "id": "archive_evidence",
            "label": "Archive evidence",
            "status": "manual",
        },
    ]


def format_pilot_final_handoff_checklist_markdown(
    view: PilotRunbookView | None = None,
) -> str:
    view = view or build_pilot_runbook_view()
    payload = pilot_final_handoff_checklist_payload(view)
    items = payload["items"] if isinstance(payload["items"], list) else []
    lines = [
        "# Pilot Final Handoff Checklist",
        "",
        f"- Context: `{view.subtitle}`",
        f"- Source: `{view.title}`",
        f"- Handoff decision: `{view.handoff_decision.status}`",
        f"- Handoff action: `{view.handoff_decision.action_label}`",
        f"- Readiness status: `{view.readiness_rollup.status}`",
        f"- Readiness detail: `{view.readiness_rollup.detail}`",
        f"- Attention items: `{len(view.attention_items)}`",
        f"- Ready checklist items: `{payload['ready_item_count']}`",
        f"- Attention checklist items: `{payload['attention_item_count']}`",
        f"- Manual checklist items: `{payload['manual_item_count']}`",
        "",
        "## Checklist",
        "",
        "| Item | Status | Detail | Action |",
        "| --- | --- | --- | --- |",
    ]
    for item in items:
        if not isinstance(item, dict):
            continue
        action = f"[{item.get('action_label', '')}]({item.get('action_href', '')})"
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(item.get("label", "")),
                    markdown_cell(item.get("status", "")),
                    markdown_cell(item.get("detail", "")),
                    markdown_cell(action),
                ]
            )
            + " |"
        )
    return "\n".join(lines).rstrip() + "\n"


def build_pilot_bundle_inventory_csv_export(
    readiness_items: list[PilotReadinessItem],
    view: PilotRunbookView | None = None,
) -> PilotBundleInventoryCsvExport:
    view = view or build_pilot_runbook_view(readiness_items=readiness_items)
    return PilotBundleInventoryCsvExport(
        filename="pilot-bundle-inventory.csv",
        media_type="text/csv; charset=utf-8",
        content=format_pilot_bundle_inventory_csv(view.evidence_files),
    )


def build_pilot_bundle_inventory_json_export(
    readiness_items: list[PilotReadinessItem],
    view: PilotRunbookView | None = None,
) -> PilotBundleInventoryJsonExport:
    view = view or build_pilot_runbook_view(readiness_items=readiness_items)
    payload = pilot_bundle_inventory_payload(view)
    return PilotBundleInventoryJsonExport(
        filename="pilot-bundle-inventory.json",
        media_type="application/json",
        content=json.dumps(payload, indent=2, sort_keys=True) + "\n",
        payload=payload,
    )


def pilot_bundle_inventory_payload(view: PilotRunbookView) -> dict[str, object]:
    review_order = {
        path: index
        for index, path in enumerate(PILOT_BUNDLE_REVIEW_ORDER, start=1)
    }
    inventory_paths = sorted(
        (path for path in PILOT_BUNDLE_REVIEW_ORDER if path != "manifest.json"),
        key=pilot_bundle_path_sort_key,
    )
    return {
        "archive_file_count": view.evidence_archive_file_count,
        "archive_total_size_bytes": view.evidence_archive_total_size_bytes,
        "automation_file_count": view.evidence_automation_file_count,
        "bundle_type": "pilot_evidence",
        "context": view.subtitle,
        "evidence_file_count": len(view.evidence_files),
        "evidence_total_size_bytes": view.evidence_total_size_bytes,
        "expected_file_count": len(PILOT_BUNDLE_REVIEW_ORDER) - 1,
        "files": [
            {
                "category": pilot_evidence_file_category(path),
                "kind": pilot_evidence_file_kind(path),
                "path": path,
                "purpose": pilot_bundle_file_purpose(path),
                "review_order": review_order.get(path, 0),
            }
            for path in inventory_paths
        ],
        "human_file_count": view.evidence_human_file_count,
        "manifest_file_count": view.evidence_manifest_file_count,
        "manifest_path": "manifest.json",
        "schema_version": 4,
        "source": view.title,
    }


def format_pilot_bundle_inventory_csv(
    evidence_files: list[PilotEvidenceFileView],
) -> str:
    output = StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(
        [
            "review_order",
            "path",
            "category",
            "kind",
            "size_bytes",
            "sha256",
            "sha256_short",
        ]
    )
    review_order = {
        path: index
        for index, path in enumerate(PILOT_BUNDLE_REVIEW_ORDER, start=1)
    }
    for item in sorted(
        evidence_files,
        key=lambda item: pilot_bundle_path_sort_key(item.path),
    ):
        writer.writerow(
            [
                review_order.get(item.path, ""),
                item.path,
                item.category,
                item.kind,
                item.size_bytes,
                item.sha256,
                item.sha256_short,
            ]
        )
    return output.getvalue()


def pilot_bundle_path_sort_key(path: str) -> tuple[int, str]:
    review_order = pilot_bundle_review_order(path)
    if review_order <= 0:
        review_order = len(PILOT_BUNDLE_REVIEW_ORDER) + 1
    return (review_order, path)


def build_pilot_readiness_json_export(
    readiness_items: list[PilotReadinessItem],
    view: PilotRunbookView | None = None,
) -> PilotReadinessJsonExport:
    view = view or build_pilot_runbook_view(readiness_items=readiness_items)
    payload = pilot_readiness_payload(readiness_items, view)
    return PilotReadinessJsonExport(
        filename="pilot-readiness.json",
        media_type="application/json",
        content=json.dumps(payload, indent=2, sort_keys=True) + "\n",
        payload=payload,
    )


def pilot_readiness_payload(
    readiness_items: list[PilotReadinessItem],
    view: PilotRunbookView,
) -> dict[str, object]:
    return {
        "context": view.subtitle,
        "handoff_decision": pilot_handoff_decision_payload(view.handoff_decision),
        "items": [
            {
                "detail": item.detail,
                "href": item.href,
                "label": item.label,
                "status": item.status,
            }
            for item in readiness_items
        ],
        "rollup": {
            "attention_items": len(view.attention_items),
            "blocked": view.readiness_rollup.blocked,
            "detail": view.readiness_rollup.detail,
            "ready": view.readiness_rollup.ready,
            "status": view.readiness_rollup.status,
            "total": view.readiness_rollup.total,
            "warning": view.readiness_rollup.warning,
        },
        "schema_version": 2,
        "source": view.title,
    }


def format_pilot_readiness_json(
    readiness_items: list[PilotReadinessItem],
    view: PilotRunbookView,
) -> str:
    return json.dumps(
        pilot_readiness_payload(readiness_items, view),
        indent=2,
        sort_keys=True,
    ) + "\n"


def build_pilot_evidence_bundle(
    readiness_items: list[PilotReadinessItem],
    view: PilotRunbookView | None = None,
) -> PilotEvidenceBundle:
    view = view or build_pilot_runbook_view(readiness_items=readiness_items)
    evidence_files = build_pilot_evidence_files(readiness_items, view)
    manifest = build_pilot_evidence_manifest_payload(evidence_files, view)
    bundle_files = {
        **evidence_files,
        "manifest.json": json.dumps(manifest, indent=2, sort_keys=True) + "\n",
    }

    output = BytesIO()
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for path, content in sorted(bundle_files.items()):
            write_zip_text(archive, path, content)

    return PilotEvidenceBundle(
        filename="pilot-evidence-bundle.zip",
        media_type="application/zip",
        content=output.getvalue(),
    )


def build_pilot_evidence_manifest(
    readiness_items: list[PilotReadinessItem],
    view: PilotRunbookView | None = None,
) -> PilotEvidenceManifest:
    view = view or build_pilot_runbook_view(readiness_items=readiness_items)
    evidence_files = build_pilot_evidence_files(readiness_items, view)
    payload = build_pilot_evidence_manifest_payload(evidence_files, view)
    return PilotEvidenceManifest(
        filename="pilot-evidence-manifest.json",
        media_type="application/json",
        content=json.dumps(payload, indent=2, sort_keys=True) + "\n",
        payload=payload,
    )


def build_pilot_evidence_verification(
    readiness_items: list[PilotReadinessItem],
    view: PilotRunbookView | None = None,
) -> PilotEvidenceVerification:
    manifest = build_pilot_evidence_manifest(readiness_items, view)
    return PilotEvidenceVerification(
        filename="pilot-evidence-verification.md",
        media_type="text/markdown; charset=utf-8",
        content=format_pilot_evidence_verification_markdown(manifest.payload),
    )


def build_pilot_evidence_verification_json(
    readiness_items: list[PilotReadinessItem],
    view: PilotRunbookView | None = None,
) -> PilotEvidenceVerificationJson:
    manifest = build_pilot_evidence_manifest(readiness_items, view)
    payload = pilot_evidence_verification_payload(manifest.payload)
    return PilotEvidenceVerificationJson(
        filename="pilot-evidence-verification.json",
        media_type="application/json",
        content=json.dumps(payload, indent=2, sort_keys=True) + "\n",
        payload=payload,
    )


def pilot_evidence_verification_payload(
    manifest_payload: dict[str, object],
) -> dict[str, object]:
    files = manifest_payload.get("files")
    file_entries = files if isinstance(files, list) else []
    automation_files = manifest_payload.get("automation_files")
    human_files = manifest_payload.get("human_files")
    readiness = manifest_payload.get("readiness")
    review_order = manifest_payload.get("review_order")
    review_order_entries = review_order if isinstance(review_order, list) else []
    return {
        "automation_file_count": manifest_payload.get("automation_file_count", 0),
        "automation_files": automation_files if isinstance(automation_files, list) else [],
        "bundle_type": manifest_payload.get("bundle_type", ""),
        "checks": [
            {
                "id": "download_bundle",
                "status": "manual",
                "detail": "Download the pilot evidence bundle from the local Pilot page.",
            },
            {
                "id": "extract_bundle",
                "status": "manual",
                "detail": "Extract the ZIP on a trusted workstation.",
            },
            {
                "id": "compare_hashes",
                "status": "manual",
                "detail": "Compare each extracted file hash with the manifest SHA-256.",
            },
            {
                "id": "retain_evidence",
                "status": "manual",
                "detail": "Keep verification output with the pilot handoff evidence.",
            },
        ],
        "context": manifest_payload.get("context", ""),
        "file_count": manifest_payload.get("file_count", len(file_entries)),
        "files": file_entries,
        "human_file_count": manifest_payload.get("human_file_count", 0),
        "human_files": human_files if isinstance(human_files, list) else [],
        "manifest_file_count": manifest_payload.get("manifest_file_count", 0),
        "manifest_schema_version": manifest_payload.get("schema_version", ""),
        "readiness": readiness if isinstance(readiness, dict) else {},
        "review_file_count": manifest_payload.get(
            "review_file_count",
            len(review_order_entries),
        ),
        "review_order": review_order_entries,
        "schema_version": 3,
        "source": manifest_payload.get("source", ""),
        "verification_type": "pilot_evidence",
    }


def format_pilot_evidence_verification_markdown(payload: dict[str, object]) -> str:
    files = payload.get("files")
    file_entries = files if isinstance(files, list) else []
    readiness = payload.get("readiness")
    readiness_payload = readiness if isinstance(readiness, dict) else {}
    review_order = payload.get("review_order")
    review_order_entries = review_order if isinstance(review_order, list) else []
    lines = [
        "# Pilot Evidence Bundle Verification",
        "",
        f"- Context: `{payload.get('context', '')}`",
        f"- Source: `{payload.get('source', '')}`",
        f"- Bundle type: `{payload.get('bundle_type', '')}`",
        f"- Schema version: `{payload.get('schema_version', '')}`",
        f"- File count: `{payload.get('file_count', len(file_entries))}`",
        f"- Automation files: `{payload.get('automation_file_count', 0)}`",
        f"- Human-readable files: `{payload.get('human_file_count', 0)}`",
        f"- Manifest files: `{payload.get('manifest_file_count', 0)}`",
        f"- Review files: `{payload.get('review_file_count', len(review_order_entries))}`",
        f"- Readiness status: `{readiness_payload.get('status', '')}`",
        f"- Readiness detail: `{readiness_payload.get('detail', '')}`",
        "",
        "## Files",
        "",
        "| File | Category | Kind | Review | Purpose | Bytes | SHA-256 |",
        "| --- | --- | --- | ---: | --- | ---: | --- |",
    ]
    if not file_entries:
        lines.append("| None | - | - | 0 | - | 0 | - |")
    sorted_file_entries = sorted(
        [item for item in file_entries if isinstance(item, dict)],
        key=pilot_verification_file_sort_key,
    )
    for item in sorted_file_entries:
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(item.get("path", "")),
                    markdown_cell(item.get("category", "")),
                    markdown_cell(item.get("kind", "")),
                    markdown_cell(item.get("review_order", "")),
                    markdown_cell(item.get("purpose", "")),
                    markdown_cell(item.get("size_bytes", "")),
                    markdown_cell(item.get("sha256", "")),
                ]
            )
            + " |"
        )
    if review_order_entries:
        lines.extend(["", "## Review Order", ""])
        for index, path in enumerate(review_order_entries, start=1):
            lines.append(f"{index}. `{path}`")
    lines.extend(
        [
            "",
            "## Verification Steps",
            "",
            "1. Download the pilot evidence bundle.",
            "2. Extract the ZIP on a trusted workstation.",
            "3. Compare each extracted file hash with the SHA-256 value above.",
            "4. Keep this verification sheet with the pilot handoff evidence.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def pilot_verification_file_sort_key(item: dict[str, object]) -> tuple[int, str]:
    review_order = item.get("review_order")
    try:
        review_value = int(review_order)
    except (TypeError, ValueError):
        review_value = 0
    if review_value <= 0:
        review_value = len(PILOT_BUNDLE_REVIEW_ORDER) + 1
    return (review_value, str(item.get("path", "")))


def build_pilot_evidence_files(
    readiness_items: list[PilotReadinessItem],
    view: PilotRunbookView,
) -> dict[str, str]:
    return {
        "pilot-acceptance-checklist.md": format_pilot_acceptance_markdown(view),
        "pilot-acceptance-checklist.json": build_pilot_acceptance_json_export(
            view,
        ).content,
        "pilot-attention.json": build_pilot_attention_json_export(
            readiness_items,
            view,
        ).content,
        "pilot-attention.md": format_pilot_attention_markdown(view.attention_items, view),
        "pilot-bundle-index.json": build_pilot_bundle_index_json_export(
            readiness_items,
            view,
        ).content,
        "pilot-bundle-index.md": format_pilot_bundle_index_markdown(view),
        "pilot-bundle-inventory.json": build_pilot_bundle_inventory_json_export(
            readiness_items,
            view,
        ).content,
        "pilot-delivery-receipt.json": build_pilot_delivery_receipt_json_export(
            readiness_items,
            view,
        ).content,
        "pilot-delivery-receipt.md": format_pilot_delivery_receipt_markdown(view),
        "pilot-final-handoff-checklist.json": (
            build_pilot_final_handoff_checklist_json_export(
                readiness_items,
                view,
            ).content
        ),
        "pilot-final-handoff-checklist.md": (
            format_pilot_final_handoff_checklist_markdown(view)
        ),
        "pilot-handoff-summary.json": build_pilot_handoff_summary_json_export(
            readiness_items,
            view,
        ).content,
        "pilot-handoff-summary.md": format_pilot_handoff_summary_markdown(view),
        "pilot-readiness.json": format_pilot_readiness_json(readiness_items, view),
        "pilot-readiness.md": format_pilot_readiness_markdown(readiness_items, view),
        "pilot-runbook.json": build_pilot_runbook_json_export(view).content,
        "pilot-runbook.md": format_pilot_runbook_markdown(view),
    }


def build_pilot_evidence_manifest_payload(
    evidence_files: dict[str, str],
    view: PilotRunbookView,
) -> dict[str, object]:
    file_entries = [
        manifest_file_entry(path, content) for path, content in sorted(evidence_files.items())
    ]
    return build_pilot_evidence_manifest_payload_from_entries(file_entries, view)


def build_pilot_evidence_manifest_payload_from_entries(
    file_entries: list[dict[str, object]],
    view: PilotRunbookView,
) -> dict[str, object]:
    automation_files = [
        str(entry["path"])
        for entry in file_entries
        if str(entry["path"]).endswith(".json")
    ]
    human_files = [
        str(entry["path"]) for entry in file_entries if str(entry["path"]).endswith(".md")
    ]
    return {
        "automation_file_count": len(automation_files),
        "automation_files": automation_files,
        "bundle_type": "pilot_evidence",
        "context": view.subtitle,
        "file_count": len(file_entries),
        "files": file_entries,
        "human_file_count": len(human_files),
        "human_files": human_files,
        "manifest_file_count": 1,
        "readiness": {
            "attention_items": len(view.attention_items),
            "blocked": view.readiness_rollup.blocked,
            "detail": view.readiness_rollup.detail,
            "ready": view.readiness_rollup.ready,
            "status": view.readiness_rollup.status,
            "total": view.readiness_rollup.total,
            "warning": view.readiness_rollup.warning,
        },
        "review_file_count": len(PILOT_BUNDLE_REVIEW_ORDER),
        "review_order": PILOT_BUNDLE_REVIEW_ORDER,
        "schema_version": 7,
        "source": view.title,
    }


def pilot_visible_manifest_size_bytes(
    evidence_files: list[PilotEvidenceFileView],
    view: PilotRunbookView,
) -> int:
    file_entries = [
        {
            "category": item.category,
            "kind": pilot_bundle_review_file_kind(item.path),
            "path": item.path,
            "purpose": item.purpose,
            "review_order": item.review_order,
            "sha256": item.sha256,
            "size_bytes": item.size_bytes,
        }
        for item in sorted(evidence_files, key=lambda item: item.path)
    ]
    payload = build_pilot_evidence_manifest_payload_from_entries(file_entries, view)
    return len((json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def build_pilot_evidence_file_views(
    readiness_items: list[PilotReadinessItem],
    view: PilotRunbookView,
) -> list[PilotEvidenceFileView]:
    evidence_files = build_pilot_evidence_files(readiness_items, view)
    file_views: list[PilotEvidenceFileView] = []
    for path, content in sorted(
        evidence_files.items(),
        key=lambda item: pilot_bundle_path_sort_key(item[0]),
    ):
        entry = manifest_file_entry(path, content)
        sha256_value = str(entry["sha256"])
        file_views.append(
            PilotEvidenceFileView(
                path=str(entry["path"]),
                category=pilot_evidence_file_category(str(entry["path"])),
                kind=pilot_evidence_file_kind(str(entry["path"])),
                review_order=pilot_bundle_review_order(str(entry["path"])),
                purpose=pilot_bundle_file_purpose(str(entry["path"])),
                size_bytes=int(entry["size_bytes"]),
                sha256=sha256_value,
                sha256_short=sha256_value[:12],
            )
        )
    return file_views


def pilot_evidence_file_category(path: str) -> str:
    if path == "manifest.json":
        return "manifest"
    if path.endswith(".json"):
        return "automation"
    if path.endswith(".md"):
        return "human"
    return "other"


def pilot_evidence_file_kind(path: str) -> str:
    if path.endswith(".json"):
        return "Automation JSON"
    if path.endswith(".md"):
        return "Human-readable Markdown"
    return "Other"


def manifest_file_entry(path: str, content: str) -> dict[str, object]:
    content_bytes = content.encode("utf-8")
    return {
        "category": pilot_evidence_file_category(path),
        "kind": pilot_bundle_review_file_kind(path),
        "path": path,
        "purpose": pilot_bundle_file_purpose(path),
        "review_order": pilot_bundle_review_order(path),
        "sha256": sha256(content_bytes).hexdigest(),
        "size_bytes": len(content_bytes),
    }


def write_zip_text(archive: ZipFile, path: str, content: str) -> None:
    info = ZipInfo(path, date_time=PILOT_BUNDLE_TIMESTAMP)
    info.compress_type = ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o600 << 16
    archive.writestr(info, content.encode("utf-8"))


def markdown_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")
