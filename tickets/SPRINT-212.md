# Sprint 212 - Pilot Manifest Count Metric

## Goal

Show that the Pilot evidence bundle includes a manifest file before download.

## Scope

- add manifest file count metadata to the Pilot runbook view
- show the manifest count in the Pilot evidence metrics
- keep visible evidence file rows unchanged
- keep bundle contents, manifests, CSV, and JSON export behavior unchanged
- cover the manifest count with tests

## Safety

- no live scanner changes
- no network activity
- no bundle extraction or restore behavior
- no customer data collection

## Acceptance Criteria

- Pilot evidence metrics render a manifest count
- default Pilot view reports one manifest file
- evidence file counts remain 8 automation and 7 human-readable files
- existing bundle exports remain covered by tests
