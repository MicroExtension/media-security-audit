# Sprint 206 - Pilot Verification Review Order

## Goal

Make the Pilot evidence verification Markdown follow the same review order as the handoff workflow.

## Scope

- sort verification Markdown file rows by `review_order`
- keep file purpose, size, and SHA-256 columns intact
- keep JSON payloads and bundle contents unchanged
- cover the rendered row order with tests

## Safety

- no live scanner changes
- no network activity
- no bundle extraction, restore, or checksum recalculation changes
- no customer data collection

## Acceptance Criteria

- verification Markdown lists handoff files before later review files
- acceptance checklist rows appear after earlier handoff rows
- delivery receipt rows remain near the end of the verification table
- tests cover the rendered Markdown order
