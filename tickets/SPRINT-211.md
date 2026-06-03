# Sprint 211 - Pilot Evidence Bytes Summary

## Goal

Show the total Pilot evidence file size before bundle download.

## Scope

- add total evidence byte metadata to the Pilot runbook view
- show total evidence bytes in the Pilot evidence metrics
- keep individual file metadata unchanged
- keep bundle contents, manifests, CSV, and JSON export behavior unchanged
- cover the total byte value with tests

## Safety

- no live scanner changes
- no network activity
- no bundle extraction or restore behavior
- no customer data collection

## Acceptance Criteria

- Pilot evidence metrics render total evidence bytes
- total bytes equal the sum of visible evidence file sizes
- total bytes are greater than zero for the default Pilot view
- existing bundle exports remain covered by tests
