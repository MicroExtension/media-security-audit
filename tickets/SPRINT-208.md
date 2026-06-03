# Sprint 208 - Pilot Page Inventory Review Order

## Goal

Make the Pilot page evidence inventory follow the same review order as the Pilot handoff exports.

## Scope

- sort visible Pilot page evidence files by `review_order`
- keep file size, kind, and SHA-256 preview metadata unchanged
- keep ZIP contents, manifest payloads, and scanner behavior unchanged
- cover the visible inventory order with tests

## Safety

- no live scanner changes
- no network activity
- no bundle extraction, restore, or checksum recalculation changes
- no customer data collection

## Acceptance Criteria

- Pilot page evidence inventory starts with `pilot-handoff-summary.md`
- second visible file is `pilot-handoff-summary.json`
- delivery receipt JSON remains near the end of the visible inventory
- tests cover the visible inventory ordering
