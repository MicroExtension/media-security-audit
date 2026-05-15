# Sprint 62 - Dashboard Blocked Clients

## Goal

Show a dashboard watchlist of clients blocked before scan execution so
technicians can fix authorization, scope, or check selection gaps first.

## Scope

- Add blocked client rows to the dashboard view model.
- Include clients whose highest preparation priority is blocked.
- Sort by blocked mission count, risk score, new finding count, and client name.
- Display client links, preparation counts, and next action.
- Update tests and documentation.

## Acceptance Criteria

- Dashboard exposes blocked clients.
- Clients are counted once even when they have multiple missions.
- The watchlist links to the blocking mission when available.
- Scan execution remains CLI-only.

## Safety

- No live scanner execution is added.
- No network activity is added.
- The sprint only adds read-only dashboard summary data.
