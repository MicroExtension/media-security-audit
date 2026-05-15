# Sprint 53 - Client Finding Disposition Summary

## Goal

Show finding disposition counts on each client detail page so technicians can
review one customer's finding status coverage without opening each mission.

## Scope

- Aggregate finding status counts across missions for the selected client.
- Display the counts on the client detail page using existing disposition
  styling.
- Reuse the same counting helper used by dashboard, mission pages, and reports.
- Update tests and documentation.

## Acceptance Criteria

- Client detail view exposes counts for every finding status.
- Counts only include missions that belong to the selected client.
- Dashboard, mission, and report disposition summaries remain unchanged.
- Scan execution remains CLI-only.

## Safety

- No live scanner execution is added.
- No network activity is added.
- The sprint only adds read-only client summary data.
