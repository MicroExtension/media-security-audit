# Sprint 214 - Pilot Archive Byte Summary

## Goal

Distinguish visible evidence bytes from archive bytes on the Pilot page before download.

## Scope

- add archive byte metadata to the Pilot runbook view
- show `Evidence Bytes` and `Archive Bytes` in Pilot evidence metrics
- estimate archive bytes from visible evidence metadata plus the manifest JSON
- keep bundle contents, manifests, CSV, and JSON export behavior unchanged
- cover the archive byte value with tests

## Safety

- no live scanner changes
- no network activity
- no bundle extraction or restore behavior
- no customer data collection

## Acceptance Criteria

- Pilot evidence metrics render evidence and archive byte labels
- archive bytes are greater than visible evidence bytes
- visible evidence byte total remains the sum of visible evidence files
- existing bundle exports remain covered by tests
