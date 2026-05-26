# Sprint 167 - Export Inventory Client Filter

## Goal

Make the mission export inventory easier to use for MSP handoff review by
letting technicians filter packages by client before downloading evidence
inventories.

## Scope

- Add a client filter to `/exports`.
- Preserve the selected client in CSV, JSON, and Markdown download links.
- Include `client_id` in export filter metadata.
- Show the selected client in the active filter summary.
- Update documentation and regression tests.

## Out Of Scope

- No scanner execution changes.
- No live network activity.
- No package extraction or restore workflow.
- No customer data upload.

## Acceptance Criteria

- `/exports` exposes a client selector.
- Filtered inventory rows only include the selected client's missions.
- JSON and Markdown downloads preserve the selected `client_id` filter.
- Existing search, status, and missing-package filters still work together.
- Tests cover the client filter and the web template wiring.
