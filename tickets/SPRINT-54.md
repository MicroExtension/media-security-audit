# Sprint 54 - Mission Row Review Counts

## Goal

Show compact finding review counts in dashboard and client mission tables so
technicians can spot review backlog without opening each mission.

## Scope

- Add new, accepted risk, and false positive counts to mission row view models.
- Display the counts in dashboard mission tables.
- Display the counts in client mission tables.
- Update tests and documentation.

## Acceptance Criteria

- Mission rows expose new finding counts.
- Mission rows expose accepted risk counts.
- Mission rows expose false positive counts.
- Dashboard and client mission tables show the counts next to the total findings.
- Scan execution remains CLI-only.

## Safety

- No live scanner execution is added.
- No network activity is added.
- The sprint only adds read-only table summary data.
