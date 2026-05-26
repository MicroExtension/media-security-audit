# Sprint 169 - Pilot Runbook Page

## Goal

Prepare the product for a first client pilot by adding a local runbook page that
keeps the technician workflow visible inside the web interface.

## Scope

- Add a protected `/pilot` route.
- Add a `pilot.html` page with setup, mission, review, handoff, and closeout
  sections.
- Add top navigation to the pilot runbook.
- Link the runbook to existing operational pages.
- Update documentation and regression tests.

## Out Of Scope

- No scanner execution changes.
- No live network activity.
- No new data mutation workflow.
- No customer data export changes.

## Acceptance Criteria

- The web UI exposes a Pilot navigation item.
- `/pilot` renders a local checklist page.
- The page links to Dashboard, System, Templates, Activity, Remediations, and
  Exports.
- Tests cover the route, template, and navigation wiring.
