# Sprint 213 - Pilot Archive File Count Metric

## Goal

Show the total Pilot evidence archive file count, including the manifest.

## Scope

- add archive file count metadata to the Pilot runbook view
- show the archive file count in the Pilot evidence metrics
- keep visible evidence rows unchanged
- keep bundle contents, manifests, CSV, and JSON export behavior unchanged
- cover the archive count with tests

## Safety

- no live scanner changes
- no network activity
- no bundle extraction or restore behavior
- no customer data collection

## Acceptance Criteria

- Pilot evidence metrics render an archive file count
- archive file count equals visible evidence files plus manifest files
- default Pilot view reports sixteen archive files
- existing bundle exports remain covered by tests
