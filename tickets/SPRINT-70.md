# Sprint 70 - Mission Row Actions

## Goal

Show direct preparation action links in the dashboard mission table so
technicians can move from a mission row to the right workflow section.

## Scope

- Add preparation action labels and links to mission rows.
- Reuse the mission readiness anchor logic already used by dashboard watchlists.
- Display the action link in the mission table preparation column.
- Update tests and documentation.

## Acceptance Criteria

- Mission rows expose a preparation action label.
- Mission rows expose a preparation action href.
- Dashboard mission rows link to setup, scope, checks, findings, or reports.
- Tests cover mission row action labels and hrefs.
- Scan execution remains CLI-only.

## Safety

- No live scanner execution is added.
- No network activity is added.
- The sprint only adds read-only navigation links.
