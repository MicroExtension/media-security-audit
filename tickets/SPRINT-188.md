# Sprint 188 - Pilot Bundle Inventory CSV

## Goal

Add a local CSV export for the Pilot evidence bundle inventory so technicians can
review file hashes and sizes in a spreadsheet before handoff.

## Scope

- Add a standalone `/pilot/bundle-inventory.csv` export.
- Include review order, path, size, SHA-256, and short SHA-256 fields.
- Link the CSV from the Pilot page actions and bundle section.
- Keep the pilot ZIP contents unchanged.

## Out of Scope

- No live scanner execution.
- No network activity.
- No customer file collection.
- No disk writes for CSV generation.

## Acceptance Criteria

- The Pilot page links to the bundle inventory CSV.
- The CSV export is deterministic and machine-readable.
- Existing Pilot Markdown, JSON, manifest, verification, and bundle exports continue to work.
- Unit tests cover route wiring, CSV headers, review order values, and hash fields.
