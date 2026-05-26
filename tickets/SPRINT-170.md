# Sprint 170 - Pilot Runbook Markdown Export

## Goal

Make the first-client pilot checklist portable by adding a deterministic
Markdown export that technicians can keep with the client handoff evidence.

## Scope

- Add a shared pilot runbook content module.
- Render the Pilot page from the shared runbook content.
- Add a protected Markdown download route.
- Add a Markdown action to the Pilot page.
- Update documentation and regression tests.

## Out Of Scope

- No scanner execution changes.
- No live network activity.
- No data mutation workflow.
- No customer data export changes.

## Acceptance Criteria

- `/pilot` renders the same runbook content from a shared view model.
- `/pilot/runbook.md` downloads a deterministic Markdown checklist.
- The Pilot page links to the Markdown export.
- Tests cover the view model, route wiring, template wiring, and Markdown
  output.
