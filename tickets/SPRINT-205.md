# Sprint 205 - Pilot Verification Purpose Table

## Goal

Make the Pilot evidence verification Markdown easier to use during handoff by showing each file purpose next to its checksum.

## Scope

- add a `Purpose` column to the verification Markdown file table
- keep checksum, kind, review order, and file size columns intact
- cover the rendered verification Markdown with tests
- keep JSON payloads and bundle contents unchanged

## Safety

- no live scanner changes
- no network activity
- no bundle extraction, restore, or checksum recalculation changes
- no customer data collection

## Acceptance Criteria

- verification Markdown includes `File`, `Kind`, `Review`, `Purpose`, `Bytes`, and `SHA-256`
- rendered rows include the purpose already present in manifest metadata
- tests cover the new verification table output
