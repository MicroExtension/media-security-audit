# Sprint 197 - Pilot Inventory Category Exports

## Goal

Keep the Pilot bundle inventory exports aligned with the visible Pilot page file
categories.

## Scope

- add file category values to `pilot-bundle-inventory.csv`
- add file category values to `pilot-bundle-inventory.json`
- add automation and human-readable file counters to the JSON inventory
- version the inventory JSON schema for the new fields

## Safety

- no live scanner changes
- no network activity
- no changes to bundle checksums or extraction
- no customer data collection

## Acceptance Criteria

- CSV inventory includes a `kind` column
- JSON inventory includes per-file `kind` values
- JSON inventory includes category counters
- tests cover direct exports and archived bundle inventory content
