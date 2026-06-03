# Sprint 207 - Pilot Inventory Review Order

## Goal

Make Pilot bundle inventory CSV and JSON exports follow the same review order as the handoff workflow.

## Scope

- sort bundle inventory CSV rows by `review_order`
- sort bundle inventory JSON file entries by `review_order`
- keep checksums and file metadata unchanged
- cover the exported order with tests

## Safety

- no live scanner changes
- no network activity
- no bundle extraction, restore, or checksum recalculation changes
- no customer data collection

## Acceptance Criteria

- CSV inventory starts with `pilot-handoff-summary.md`
- JSON inventory starts with `pilot-handoff-summary.md`
- delivery receipt JSON remains the last inventory file before the manifest
- tests cover CSV and JSON inventory ordering
