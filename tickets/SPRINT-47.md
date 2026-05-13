# Sprint 47 - Mission Preparation Columns

## Goal

Make mission tables show preparation status directly so technicians do not need
to cross-reference the separate preparation table.

## Scope

- Add reusable mission preparation summary data.
- Add preparation status and next action to mission rows.
- Show preparation columns in dashboard mission tables.
- Show preparation columns in client mission tables.
- Keep all scan execution CLI-only.

## Acceptance Criteria

- Mission rows include preparation status.
- Mission rows include the next preparation action.
- Dashboard mission table displays the new preparation information.
- Client mission table displays the new preparation information.
- Tests cover mission row preparation fields.
- No scanner execution path is added to the web UI.

## Safety Notes

- This sprint only reads stored mission metadata and findings.
- It does not run scanner commands or perform network activity.
- It does not add brute force, exploitation, payloads, or exfiltration.
