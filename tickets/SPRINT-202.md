# Sprint 202 - Pilot Manifest File Metadata

## Goal

Make the Pilot evidence manifest the single authoritative file for both
checksum verification and evidence review metadata.

## Scope

- add per-file kind, purpose, and review order metadata to manifest entries
- surface file kind and review order in the verification Markdown table
- keep existing checksum fields and review order arrays intact
- version the manifest schema for the new metadata

## Safety

- no live scanner changes
- no network activity
- no bundle extraction, restore, or checksum changes
- no customer data collection

## Acceptance Criteria

- manifest entries include kind, purpose, and review order
- verification JSON exposes the enriched manifest entries
- verification Markdown shows kind and review order in the file table
- tests cover direct and archived manifest output
