# Sprint 145 - Mission Counter-Test Counts

## Goal

Show per-mission counter-test counts in dashboard and client mission tables.

## Scope

- Add counter-test ready, passed, and failed counts to mission rows.
- Display those counts in the workspace mission table.
- Display those counts in the client mission table.
- Update documentation and UI tests.

## Acceptance Criteria

- Mission rows expose ready counter-test counts.
- Mission rows expose passed counter-test counts.
- Mission rows expose failed counter-test counts.
- Dashboard and client mission tables render the compact counts.
- No scanner execution, network activity, or deployment workflow is added.

## Safety

- No live scanner execution.
- No browser scan execution.
- No network activity added.
- No destructive test.
- This sprint only summarizes stored finding statuses.
