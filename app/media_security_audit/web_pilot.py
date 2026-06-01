"""Pilot runbook content for first client deployments."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
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
class PilotReadinessRollup:
    status: str
    ready: int
    warning: int
    blocked: int
    total: int
    detail: str


@dataclass(frozen=True)
class PilotRunbookSection:
    anchor: str
    title: str
    links: list[PilotRunbookLink]
    steps: list[PilotRunbookStep]


@dataclass(frozen=True)
class PilotEvidenceFileView:
    path: str
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
    evidence_files: list[PilotEvidenceFileView]


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
class PilotAttentionExport:
    filename: str
    media_type: str
    content: str


@dataclass(frozen=True)
class PilotHandoffSummaryExport:
    filename: str
    media_type: str
    content: str


@dataclass(frozen=True)
class PilotBundleIndexExport:
    filename: str
    media_type: str
    content: str


@dataclass(frozen=True)
class PilotReadinessJsonExport:
    filename: str
    media_type: str
    content: str
    payload: dict[str, object]


def build_pilot_runbook_view(
    readiness_items: list[PilotReadinessItem] | None = None,
) -> PilotRunbookView:
    readiness_items = readiness_items or []
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
        attention_items=build_pilot_attention_items(readiness_items),
        readiness_rollup=build_pilot_readiness_rollup(readiness_items),
        evidence_files=[],
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
    return replace(
        view,
        evidence_files=build_pilot_evidence_file_views(readiness_items, view),
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
        f"- Attention items: `{len(view.attention_items)}`",
        f"- Acceptance items: `{len(view.acceptance_items)}`",
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
            "- `pilot-runbook.md`: technician workflow.",
            "- `pilot-acceptance-checklist.md`: beta sign-off checklist.",
            "- `pilot-bundle-index.md`: bundle review order.",
            "- `pilot-readiness.md`: workspace readiness details.",
            "- `pilot-readiness.json`: machine-readable readiness evidence.",
            "- `pilot-attention.md`: remaining warnings and blockers.",
            "- `manifest.json`: bundle file checksums.",
        ]
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
        "",
        "## Recommended Review Order",
        "",
        "1. Open `pilot-handoff-summary.md` first for the current handoff state.",
        "2. Review `pilot-attention.md` for warnings or blockers.",
        "3. Review `pilot-readiness.md` for detailed workspace readiness.",
        "4. Complete `pilot-acceptance-checklist.md` for beta sign-off.",
        "5. Keep `pilot-runbook.md` with the technician delivery notes.",
        "6. Use `pilot-readiness.json` only when automation needs structured state.",
        "7. Compare extracted files with `manifest.json` before archiving.",
        "",
        "## Bundle Files",
        "",
        "| File | Purpose |",
        "| --- | --- |",
        "| pilot-bundle-index.md | Review order for extracted evidence. |",
        "| pilot-handoff-summary.md | Compact handoff state and next actions. |",
        "| pilot-attention.md | Remaining warnings and blockers. |",
        "| pilot-readiness.md | Detailed local readiness checks. |",
        "| pilot-readiness.json | Machine-readable readiness state. |",
        "| pilot-acceptance-checklist.md | Beta acceptance checklist. |",
        "| pilot-runbook.md | Technician workflow. |",
        "| manifest.json | File checksums for integrity review. |",
    ]
    return "\n".join(lines).rstrip() + "\n"


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
        "schema_version": 1,
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


def format_pilot_evidence_verification_markdown(payload: dict[str, object]) -> str:
    files = payload.get("files")
    file_entries = files if isinstance(files, list) else []
    readiness = payload.get("readiness")
    readiness_payload = readiness if isinstance(readiness, dict) else {}
    lines = [
        "# Pilot Evidence Bundle Verification",
        "",
        f"- Context: `{payload.get('context', '')}`",
        f"- Source: `{payload.get('source', '')}`",
        f"- Bundle type: `{payload.get('bundle_type', '')}`",
        f"- Schema version: `{payload.get('schema_version', '')}`",
        f"- File count: `{payload.get('file_count', len(file_entries))}`",
        f"- Readiness status: `{readiness_payload.get('status', '')}`",
        f"- Readiness detail: `{readiness_payload.get('detail', '')}`",
        "",
        "## Files",
        "",
        "| File | Bytes | SHA-256 |",
        "| --- | ---: | --- |",
    ]
    if not file_entries:
        lines.append("| None | 0 | - |")
    for item in file_entries:
        if not isinstance(item, dict):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(item.get("path", "")),
                    markdown_cell(item.get("size_bytes", "")),
                    markdown_cell(item.get("sha256", "")),
                ]
            )
            + " |"
        )
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


def build_pilot_evidence_files(
    readiness_items: list[PilotReadinessItem],
    view: PilotRunbookView,
) -> dict[str, str]:
    return {
        "pilot-acceptance-checklist.md": format_pilot_acceptance_markdown(view),
        "pilot-attention.md": format_pilot_attention_markdown(view.attention_items, view),
        "pilot-bundle-index.md": format_pilot_bundle_index_markdown(view),
        "pilot-handoff-summary.md": format_pilot_handoff_summary_markdown(view),
        "pilot-readiness.json": format_pilot_readiness_json(readiness_items, view),
        "pilot-readiness.md": format_pilot_readiness_markdown(readiness_items, view),
        "pilot-runbook.md": format_pilot_runbook_markdown(view),
    }


def build_pilot_evidence_manifest_payload(
    evidence_files: dict[str, str],
    view: PilotRunbookView,
) -> dict[str, object]:
    return {
        "bundle_type": "pilot_evidence",
        "context": view.subtitle,
        "file_count": len(evidence_files),
        "files": [
            manifest_file_entry(path, content)
            for path, content in sorted(evidence_files.items())
        ],
        "readiness": {
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


def build_pilot_evidence_file_views(
    readiness_items: list[PilotReadinessItem],
    view: PilotRunbookView,
) -> list[PilotEvidenceFileView]:
    evidence_files = build_pilot_evidence_files(readiness_items, view)
    file_views: list[PilotEvidenceFileView] = []
    for path, content in sorted(evidence_files.items()):
        entry = manifest_file_entry(path, content)
        sha256_value = str(entry["sha256"])
        file_views.append(
            PilotEvidenceFileView(
                path=str(entry["path"]),
                size_bytes=int(entry["size_bytes"]),
                sha256=sha256_value,
                sha256_short=sha256_value[:12],
            )
        )
    return file_views


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
