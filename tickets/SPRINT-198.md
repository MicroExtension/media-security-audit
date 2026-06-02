# Sprint 198 - Pilot Bundle Index Categories

## Goal

Make the first Pilot evidence file a technician opens reflect the same file
categories used by the Pilot page and inventory exports.

## Scope

- add human-readable, automation, and manifest category counts to the bundle
  index Markdown
- add `kind` values to each bundle index JSON review step
- version the bundle index JSON schema for the new fields
- keep ZIP contents and checksums unchanged

## Safety

- no live scanner changes
- no network activity
- no bundle extraction or restore logic
- no customer data collection

## Acceptance Criteria

- Markdown index includes category counts and a `Kind` table column
- JSON index includes category counts and per-file `kind` values
- manifest review step is labelled separately from automation JSON files
- tests cover direct and archived bundle index outputs
