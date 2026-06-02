# Sprint 196 - Pilot Evidence File Categories

## Goal

Make the Pilot bundle inventory easier to inspect before a technician downloads
the evidence ZIP.

## Scope

- classify visible Pilot evidence files as automation JSON or human-readable
  Markdown
- show category counts on the Pilot page
- add a file category column to the Pilot bundle table
- keep existing Pilot exports unchanged

## Safety

- no live scanner changes
- no network activity
- no changes to bundle generation or checksums
- no customer data collection

## Acceptance Criteria

- Pilot page exposes evidence category counts
- Pilot bundle table includes a category column
- view tests cover the new category data
- template tests cover the new visible fields
