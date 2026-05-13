# Sprint 52 - Dashboard Finding Disposition Summary

## Goal

Show workspace-wide finding disposition counts on the dashboard so technicians
can spot review backlog without opening every mission.

## Scope

- Aggregate finding status counts across all missions.
- Display the counts on the dashboard using the existing disposition styling.
- Reuse the same counting logic used by mission pages and reports.
- Update tests and documentation.

## Acceptance Criteria

- Dashboard view exposes counts for every finding status.
- Dashboard page displays the workspace disposition counters.
- Mission disposition counters and report disposition counts remain unchanged.
- Scan execution remains CLI-only.

## Safety

- No live scanner execution is added.
- No network activity is added.
- The sprint only adds read-only dashboard summary data.
