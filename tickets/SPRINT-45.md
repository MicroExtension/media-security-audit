# Sprint 45 - Client Priority Actions

## Goal

Make the dashboard client list tell technicians which client needs attention
first and what action should happen next.

## Scope

- Add a preparation priority to dashboard client rows.
- Add the highest priority next action for each client.
- Link the action to the relevant mission when available.
- Keep existing per-client preparation counts.
- Keep all scan execution CLI-only.

## Acceptance Criteria

- Clients with blocked missions show blocked priority.
- Clients with warnings and no blockers show warning priority.
- Clients with ready missions and no warnings show ready priority.
- Clients without missions show a clear first-mission action.
- Tests cover client priorities and next actions.
- No scanner execution path is added to the web UI.

## Safety Notes

- This sprint only reads stored mission metadata and findings.
- It does not run scanner commands or perform network activity.
- It does not add brute force, exploitation, payloads, or exfiltration.
