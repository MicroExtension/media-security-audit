# Sprint 194 - Pilot Workflow Inventory JSON

## Goal

Group the remaining Pilot workflow automation exports by adding structured JSON
for the technician runbook and bundle inventory, then including both files in
the evidence bundle.

## Scope

- Add `/pilot/runbook.json` for the technician workflow.
- Add `/pilot/bundle-inventory.json` for the expected bundle file inventory.
- Link both JSON exports from the Pilot page.
- Include both JSON files in the Pilot evidence ZIP.
- Update manifest, inventory CSV, verification Markdown, and verification JSON
  output for the expanded bundle.
- Update README, roadmap, and next-step notes.

## Out of scope

- No live scan execution.
- No network activity.
- No customer data collection.
- No destructive validation.
- No self-referential bundle checksum inventory.
- No disk writes for JSON or bundle generation.

## Acceptance Criteria

- The Pilot page links to runbook and bundle inventory JSON downloads.
- The two JSON exports are deterministic and machine-readable.
- The Pilot ZIP includes both workflow and inventory JSON files.
- The manifest hashes and file count account for both JSON files.
- Existing Pilot Markdown, readiness, review, sign-off, manifest, verification,
  inventory CSV, and bundle exports continue to work.
- Unit tests cover routes, template links, JSON payloads, and archived files.
