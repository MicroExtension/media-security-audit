# Sprint 200 - Pilot Manifest Review Counts

## Goal

Align the Pilot evidence manifest and verification exports with the evidence
category counters already visible in the Pilot index, inventory, handoff, and
delivery receipt.

## Scope

- add manifest file count to the Pilot evidence manifest
- add review file count to the Pilot evidence manifest
- expose both counts in verification Markdown and JSON exports
- version the manifest and verification JSON schemas for the new fields

## Safety

- no live scanner changes
- no network activity
- no bundle extraction, restore, or checksum changes
- no customer data collection

## Acceptance Criteria

- manifest JSON includes manifest and review file counters
- verification Markdown includes manifest and review file counters
- verification JSON includes manifest and review file counters
- tests cover direct and archived manifest output
