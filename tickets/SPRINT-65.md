# Sprint 65 - Dashboard Review Missions

## Goal

Show a dashboard watchlist of missions that are close to ready but still need a
review action before execution.

## Scope

- Add review mission rows to the dashboard view model.
- Reuse the existing mission preparation `warning` status.
- Display mission, client, next action, authorization, scope, and check status.
- Update tests and documentation.

## Acceptance Criteria

- Dashboard exposes missions with warning preparation status.
- Ready and blocked missions are not shown in the review watchlist.
- The watchlist links to mission and client pages.
- Scan execution remains CLI-only.

## Safety

- No live scanner execution is added.
- No network activity is added.
- The sprint only adds read-only dashboard summary data.
