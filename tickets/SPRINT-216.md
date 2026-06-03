# Sprint 216 - Pilot Inventory JSON Summary Metrics

## Goal

Expose Pilot archive summary metrics in `pilot-bundle-inventory.json` for automation handoff.

## Scope

- add evidence, manifest, and archive file counts to the inventory JSON payload
- add evidence and archive byte totals to the inventory JSON payload
- bump the inventory JSON schema version to 3
- keep CSV output, bundle contents, manifests, and scanner behavior unchanged
- cover the new JSON fields with tests

## Safety

- no live scanner changes
- no network activity
- no bundle extraction or restore behavior
- no customer data collection

## Acceptance Criteria

- inventory JSON reports 15 evidence files, 1 manifest file, and 16 archive files
- inventory JSON reports evidence and archive byte totals from the Pilot view
- archived bundle inventory JSON uses schema version 3
- existing bundle exports remain covered by tests
