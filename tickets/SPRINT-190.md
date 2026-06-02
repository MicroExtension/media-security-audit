# Sprint 190 - Pilot Handoff JSON

## Goal

Add a machine-readable Pilot handoff summary so technician or owner automation
can consume the same handoff state currently exposed as Markdown.

## Scope

- Add a standalone `/pilot/handoff-summary.json` export.
- Include readiness status, readiness counters, attention items, handoff files,
  and next-action count.
- Link the JSON summary from the Pilot page actions and bundle area.
- Keep the Pilot evidence ZIP contents unchanged.
- Update README, roadmap, and next-step notes.

## Out of scope

- No live scan execution.
- No network activity.
- No customer data collection.
- No evidence bundle file changes.
- No disk writes for JSON summary generation.

## Acceptance Criteria

- The Pilot page links to the handoff JSON export.
- The JSON export is deterministic and machine-readable.
- Existing Pilot Markdown, JSON, manifest, CSV, verification, and bundle exports
  continue to work.
- Unit tests cover route wiring, template links, and JSON summary content.
