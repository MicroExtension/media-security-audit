# Sprint 204 - Pilot Index Review Table

## Goal

Align the Pilot bundle index Markdown with the handoff and delivery exports by showing review order directly in the file table.

## Scope

- reuse the shared Pilot bundle file table in `pilot-bundle-index.md`
- show file kind, review order, and purpose in the bundle index table
- cover direct and archived bundle index Markdown outputs
- keep JSON payloads and ZIP contents unchanged

## Safety

- no live scanner changes
- no network activity
- no bundle extraction, restore, or checksum changes
- no customer data collection

## Acceptance Criteria

- bundle index Markdown includes `File`, `Kind`, `Review`, and `Purpose`
- manifest row shows review order `16`
- archived bundle index Markdown includes the same table
- tests cover direct and archived Markdown outputs
