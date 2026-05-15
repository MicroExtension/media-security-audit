# Sprint 60 - Dashboard Top Risk Clients

## Goal

Show a short dashboard watchlist of the highest-risk clients so technicians can
move directly to the customers that need attention.

## Scope

- Add top-risk client rows to the dashboard view model.
- Exclude clients with no active risk score.
- Sort by risk score, high/critical count, active finding count, and client name.
- Display client links, risk score, active finding count, high/critical count,
  and next action.
- Update tests and documentation.

## Acceptance Criteria

- Dashboard exposes top-risk clients.
- Clients with no active risk are not shown in the watchlist.
- Top-risk clients are sorted deterministically by highest risk first.
- Scan execution remains CLI-only.

## Safety

- No live scanner execution is added.
- No network activity is added.
- The sprint only adds read-only dashboard summary data.
