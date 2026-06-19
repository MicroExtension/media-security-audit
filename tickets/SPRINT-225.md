# Sprint 225 - Client Action Report Plan

Status: implemented.

## Goal

Make generated reports easier for a client or MEDIA technician to use for
remediation planning.

## Scope

- Add a structured client action plan to the report summary.
- Include timing, severity, asset, status, risk explanation, recommended action,
  and validation counter-test for each prioritized action.
- Render the client action plan in JSON, Markdown, HTML, and PDF reports.
- Keep the existing technical remediation plan and finding details intact.

## Out of Scope

- Do not add new scanners.
- Do not add live vulnerability lookups.
- Do not change finding severity or scoring logic.
- Do not hide technical evidence from the report.

## Acceptance Criteria

- JSON reports expose `summary.remediation_guidance`.
- Markdown reports include a `Plan d’action client` section.
- HTML reports include action plan cards.
- PDF reports include a `Plan d'action client` section.
- Existing tests continue to pass.
