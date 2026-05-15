# Sprint 63 - Dashboard No-Mission Clients

## Goal

Show a dashboard watchlist of clients that do not have any mission yet, so MSP
technicians can onboard them into the audit workflow.

## Scope

- Add no-mission client rows to the dashboard view model.
- Include clients whose preparation priority is `none`.
- Sort clients alphabetically for deterministic display.
- Display client links, reference, and next action.
- Update tests and documentation.

## Acceptance Criteria

- Dashboard exposes clients without missions.
- Clients with existing missions are not shown in the no-mission watchlist.
- The watchlist displays the onboarding next action.
- Scan execution remains CLI-only.

## Safety

- No live scanner execution is added.
- No network activity is added.
- The sprint only adds read-only dashboard summary data.
