# Sprint 185 - Pilot Readiness JSON Export

## Goal

Add a machine-readable Pilot readiness export so handoff automation can consume
the current pilot state without parsing Markdown.

## Scope

- Add a standalone `/pilot/readiness.json` export.
- Include `pilot-readiness.json` in the pilot evidence bundle.
- Add readiness JSON to handoff summary and bundle index references.
- Link the JSON export from the Pilot page readiness and attention areas.

## Out of Scope

- No live scanner execution.
- No network activity.
- No customer file collection.
- No disk writes for readiness JSON or bundle generation.

## Acceptance Criteria

- The Pilot page links to the readiness JSON export.
- The readiness JSON export includes schema version, rollup, and item details.
- The pilot ZIP contains `pilot-readiness.json`.
- The manifest and verification outputs account for the added file.
- Existing Pilot Markdown exports and manifest readiness metadata continue to work.
- Unit tests cover route wiring, JSON payload content, bundle content, and manifest
  parity.
