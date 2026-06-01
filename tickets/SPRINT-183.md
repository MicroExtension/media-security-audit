# Sprint 183 - Pilot Bundle Index

## Goal

Add a compact Markdown index for the pilot evidence bundle so a technician can
review extracted files in the intended order.

## Scope

- Add a standalone `/pilot/bundle-index.md` export.
- Include `pilot-bundle-index.md` in the pilot evidence bundle.
- Link the index from the Pilot page actions and bundle links.
- Add the index to manifest, verification, inventory, and handoff summary flow.

## Out of Scope

- No live scanner execution.
- No network activity.
- No customer file collection.
- No disk writes for index or bundle generation.

## Acceptance Criteria

- The Pilot page links to the bundle index.
- The pilot ZIP contains `pilot-bundle-index.md`.
- The manifest and verification outputs include the index file.
- The handoff summary references the index.
- Existing Pilot bundle, manifest, verification, attention, readiness, runbook,
  and acceptance exports continue to work.
- Unit tests cover route wiring, index content, bundle content, and manifest
  parity.
