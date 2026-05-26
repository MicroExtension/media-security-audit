"""Pilot runbook content for first client deployments."""

from __future__ import annotations

from dataclasses import dataclass


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


def build_pilot_runbook_view() -> PilotRunbookView:
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
