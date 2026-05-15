# Sprint 58 - Dashboard Client Priority Summary

## Goal

Show client-level priority counts on the dashboard so MSP technicians can see
how many customers are blocked, ready, awaiting review, or still without a
mission.

## Scope

- Add client priority summary rows to the dashboard view model.
- Count priority once per client, not once per mission.
- Display the summary above the detailed dashboard tables.
- Update tests and documentation.

## Acceptance Criteria

- Dashboard exposes blocked, review, ready, and no-mission client counts.
- A client with multiple missions is counted once using its highest priority.
- Summary display reuses existing non-interactive dashboard components.
- Scan execution remains CLI-only.

## Safety

- No live scanner execution is added.
- No network activity is added.
- The sprint only adds read-only dashboard summary data.
