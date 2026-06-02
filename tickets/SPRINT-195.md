# Sprint 195 - Pilot Manifest File Classification

## Goal

Make the local Pilot evidence manifest easier to review manually and easier to
consume by future automation.

## Scope

- classify Pilot evidence bundle files by machine-readable JSON and
  human-readable Markdown
- expose classification counts in the manifest
- expose the same counts in the verification JSON and Markdown outputs
- keep bundle contents unchanged

## Safety

- no live scanner changes
- no network activity
- no customer data collection
- checksum-only verification remains unchanged

## Acceptance Criteria

- Pilot evidence manifest schema is updated for file classification
- verification exports show automation and human-readable file counts
- Pilot bundle ZIP still contains the same evidence files
- tests cover the new classification fields
