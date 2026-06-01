# Sprint 184 - Pilot Manifest Readiness Summary

## Goal

Enrich the pilot evidence manifest with readiness metadata so the ZIP can be
reviewed after handoff without opening the web interface.

## Scope

- Add file count metadata to the pilot evidence manifest.
- Add readiness status, counts, detail, and attention count to the manifest.
- Surface readiness metadata in the Markdown verification sheet.
- Keep existing pilot evidence files and routes unchanged.

## Out of Scope

- No live scanner execution.
- No network activity.
- No customer file collection.
- No disk writes for manifest or verification generation.

## Acceptance Criteria

- The pilot manifest exposes readiness summary counters.
- The pilot manifest exposes the evidence file count.
- The pilot verification Markdown shows readiness status and file count.
- Existing Pilot bundle, index, handoff, attention, readiness, runbook, and
  acceptance exports continue to work.
- Unit tests cover manifest schema, readiness metadata, and verification output.
