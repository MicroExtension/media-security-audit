# Sprint 173 - Pilot Readiness Markdown Export

## Goal

Make the Pilot readiness summary portable so technicians can keep it with beta
evidence and client handoff files.

## Scope

- Add deterministic Markdown formatting for Pilot readiness items.
- Add a protected `/pilot/readiness.md` download route.
- Add Readiness Markdown actions to the Pilot page.
- Update documentation and regression tests.

## Out Of Scope

- No scanner execution changes.
- No live network activity.
- No data mutation workflow.
- No customer data export changes.

## Acceptance Criteria

- `/pilot/readiness.md` downloads a deterministic Markdown summary.
- The Markdown output includes ready, warning, and blocked counts.
- The Pilot page links to the readiness Markdown export.
- Tests cover route wiring, template wiring, normal output, and empty output.
