# Sprint 201 - Pilot Handoff File Details

## Goal

Make Pilot handoff and delivery JSON exports easier for automation to consume
without losing the existing simple file lists.

## Scope

- keep existing `handoff_files` and `delivered_files` string lists
- add detailed handoff file metadata with path, kind, purpose, and review order
- add detailed delivered file metadata with path, kind, purpose, and review order
- version handoff and delivery receipt JSON schemas for the new detail fields

## Safety

- no live scanner changes
- no network activity
- no bundle extraction, restore, or checksum changes
- no customer data collection

## Acceptance Criteria

- handoff JSON includes file count and file details
- delivery receipt JSON includes file count and file details
- archived bundle JSON files contain the same detail fields
- tests cover direct exports and archived bundle outputs
