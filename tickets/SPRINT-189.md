# Sprint 189 - Pilot Verification JSON

## Goal

Add a JSON verification export for the Pilot evidence bundle so automation can
consume the same verification plan currently provided as Markdown.

## Scope

- Add a standalone `/pilot/bundle-verification.json` export.
- Include manifest schema version, readiness, review order, files, and manual checks.
- Link the JSON verification export from the Pilot page actions and bundle areas.
- Keep the pilot ZIP contents unchanged.

## Out of Scope

- No live scanner execution.
- No network activity.
- No customer file collection.
- No disk writes for JSON verification generation.

## Acceptance Criteria

- The Pilot page links to the verification JSON export.
- The verification JSON export is deterministic and machine-readable.
- Existing Pilot Markdown, JSON, manifest, verification, CSV, and bundle exports continue to work.
- Unit tests cover route wiring, payload fields, review order, manual checks, and file entries.
