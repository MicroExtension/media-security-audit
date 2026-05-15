# Sprint 64 - Dashboard Ready Missions

## Goal

Show a dashboard watchlist of missions that are ready for authorized work, so
technicians can identify what can proceed without opening every client.

## Scope

- Add ready mission rows to the dashboard view model.
- Reuse the existing mission preparation status.
- Display mission, client, authorization, scope, and check readiness.
- Update tests and documentation.

## Acceptance Criteria

- Dashboard exposes ready missions.
- Only missions with ready preparation status are shown.
- The watchlist links to mission and client pages.
- Scan execution remains CLI-only.

## Safety

- No live scanner execution is added.
- No network activity is added.
- The sprint only adds read-only dashboard summary data.
