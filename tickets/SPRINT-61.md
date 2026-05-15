# Sprint 61 - Dashboard Review Backlog Clients

## Goal

Show a dashboard watchlist of clients with new findings still waiting for
review, so technicians can move directly to qualification work.

## Scope

- Add review-backlog client rows to the dashboard view model.
- Include clients with one or more new findings.
- Sort by new finding count, risk score, high/critical count, active finding
  count, and client name.
- Display client links, review counts, risk score, and next action.
- Update tests and documentation.

## Acceptance Criteria

- Dashboard exposes review-backlog clients.
- Clients with only reviewed or false-positive findings are not shown.
- Review-backlog clients are sorted deterministically.
- Scan execution remains CLI-only.

## Safety

- No live scanner execution is added.
- No network activity is added.
- The sprint only adds read-only dashboard summary data.
