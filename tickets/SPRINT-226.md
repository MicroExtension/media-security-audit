# Sprint 226 - Pilot V1 Smoke Test Checklist

Status: implemented.

## Goal

Make VM pilot validation easier to run from the local Pilot page before a
customer handoff.

## Scope

- Add a V1 smoke test checklist to the Pilot page.
- Cover web access, mission creation, approved scope, safe finding review,
  report generation, package export, and backup evidence.
- Include expected result, evidence, and review link for each smoke test step.
- Include the smoke test checklist in Pilot runbook Markdown and JSON exports.

## Out of Scope

- Do not run scanners automatically.
- Do not add network activity.
- Do not change deployment scripts.
- Do not replace the full V1 readiness and pilot closeout reports.

## Acceptance Criteria

- `/pilot` shows the V1 smoke test checklist.
- `pilot-runbook.md` includes a V1 Smoke Test section.
- `pilot-runbook.json` includes machine-readable smoke test items.
- Existing Pilot evidence bundle exports remain deterministic.
- Existing tests continue to pass.
