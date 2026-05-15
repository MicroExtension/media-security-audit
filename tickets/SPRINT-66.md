# Sprint 66 - Dashboard Blocked Missions

## Goal

Show a dashboard watchlist of missions blocked before execution, so technicians
can fix authorization, scope, or check selection gaps quickly.

## Scope

- Add blocked mission rows to the dashboard view model.
- Reuse the existing mission preparation `blocked` status.
- Display mission, client, next action, authorization, scope, and check status.
- Update tests and documentation.

## Acceptance Criteria

- Dashboard exposes missions with blocked preparation status.
- Ready and review missions are not shown in the blocked watchlist.
- The watchlist links to mission and client pages.
- Scan execution remains CLI-only.

## Safety

- No live scanner execution is added.
- No network activity is added.
- The sprint only adds read-only dashboard summary data.
