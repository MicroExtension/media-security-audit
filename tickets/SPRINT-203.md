# Sprint 203 - Pilot Handoff File Tables

## Goal

Make Pilot handoff and delivery Markdown exports as clear as the JSON exports by showing file kind, review order, and purpose.

## Scope

- replace handoff Markdown file bullets with a metadata table
- replace delivery receipt Markdown file bullets with a metadata table
- reuse Pilot bundle metadata helpers
- keep JSON payloads and ZIP contents unchanged

## Safety

- no live scanner changes
- no network activity
- no bundle extraction, restore, or checksum changes
- no customer data collection

## Acceptance Criteria

- handoff Markdown includes file kind, review order, and purpose
- delivery receipt Markdown includes file kind, review order, and purpose
- archived bundle Markdown files include the same tables
- tests cover direct and archived Markdown outputs
