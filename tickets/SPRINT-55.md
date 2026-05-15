# Sprint 55 - Dashboard Client Review Counts

## Goal

Show compact finding review counts in the dashboard client table so technicians
can identify client-level review backlog before opening client or mission pages.

## Scope

- Add new, accepted risk, and false positive counts to client row view models.
- Aggregate those counts from each client's missions.
- Display the counts in the dashboard client table.
- Update tests and documentation.

## Acceptance Criteria

- Client rows expose new finding counts.
- Client rows expose accepted risk counts.
- Client rows expose false positive counts.
- Counts are scoped to each client and do not include other clients' missions.
- Scan execution remains CLI-only.

## Safety

- No live scanner execution is added.
- No network activity is added.
- The sprint only adds read-only dashboard summary data.
