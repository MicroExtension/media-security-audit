"""Pilot runbook content for first client deployments."""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from media_security_audit.storage import JsonStore
from media_security_audit.web_exports import build_mission_export_inventory
from media_security_audit.web_system import SystemStatus

PILOT_BUNDLE_TIMESTAMP = (2026, 1, 1, 0, 0, 0)


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
class PilotRunbookSection:
    anchor: str
    title: str
    links: list[PilotRunbookLink]
    steps: list[PilotRunbookStep]


@dataclass(frozen=True)
class PilotRunbookView:
    title: str
    subtitle: str
    metrics: list[PilotRunbookMetric]
    sections: list[PilotRunbookSection]
    acceptance_items: list[PilotAcceptanceItem]
    readiness_items: list[PilotReadinessItem]


@dataclass(frozen=True)
class PilotEvidenceBundle:
    filename: str
    media_type: str
    content: bytes


def build_pilot_runbook_view(
    readiness_items: list[PilotReadinessItem] | None = None,
) -> PilotRunbookView:
    return PilotRunbookView(
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
        readiness_items=readiness_items or [],
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


def build_pilot_evidence_bundle(
    readiness_items: list[PilotReadinessItem],
    view: PilotRunbookView | None = None,
) -> PilotEvidenceBundle:
    view = view or build_pilot_runbook_view(readiness_items=readiness_items)
    evidence_files = {
        "pilot-acceptance-checklist.md": format_pilot_acceptance_markdown(view),
        "pilot-readiness.md": format_pilot_readiness_markdown(readiness_items, view),
        "pilot-runbook.md": format_pilot_runbook_markdown(view),
    }
    manifest = {
        "bundle_type": "pilot_evidence",
        "context": view.subtitle,
        "files": [
            manifest_file_entry(path, content)
            for path, content in sorted(evidence_files.items())
        ],
        "schema_version": 1,
        "source": view.title,
    }
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


def manifest_file_entry(path: str, content: str) -> dict[str, object]:
    content_bytes = content.encode("utf-8")
    return {
        "path": path,
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
