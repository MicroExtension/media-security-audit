# Sprint 171 - Pilot Acceptance Checklist

## Goal

Make beta sign-off easier by adding a deterministic acceptance checklist for
the first client pilot workflow.

## Scope

- Add pilot acceptance items to the shared runbook model.
- Show acceptance items on the Pilot page.
- Add a protected Markdown acceptance checklist download.
- Update documentation and regression tests.

## Out Of Scope

- No scanner execution changes.
- No live network activity.
- No data mutation workflow.
- No customer data export changes.

## Acceptance Criteria

- `/pilot` shows an Acceptance section.
- `/pilot/acceptance.md` downloads a deterministic Markdown checklist.
- The checklist covers setup, mission, review, handoff, and closeout evidence.
- Tests cover the model, route wiring, template wiring, and Markdown output.
