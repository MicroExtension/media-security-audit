# Sprint 182 - Pilot Handoff Summary

## Goal

Add a compact Markdown handoff summary for the pilot evidence package.

## Scope

- Add a standalone `/pilot/handoff-summary.md` export.
- Include `pilot-handoff-summary.md` in the pilot evidence bundle.
- Summarize readiness status, attention count, acceptance count, and handoff files.
- Keep existing Pilot exports unchanged.

## Out of Scope

- No live scanner execution.
- No network activity.
- No customer file collection.
- No disk writes for summary or bundle generation.

## Acceptance Criteria

- The Pilot page links to the handoff summary.
- The pilot ZIP contains `pilot-handoff-summary.md`.
- The manifest and verification outputs include the summary file.
- Existing Pilot bundle, manifest, verification, attention, readiness, runbook, and acceptance exports continue to work.
- Unit tests cover route wiring, summary content, bundle content, and manifest parity.
