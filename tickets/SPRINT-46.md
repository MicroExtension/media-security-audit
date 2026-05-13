# Sprint 46 - Client Priority Ordering

## Goal

Make the dashboard client list naturally surface the client accounts that need
technician attention first.

## Scope

- Sort dashboard client rows by preparation priority.
- Keep blocked clients before warning, ready, and no-mission clients.
- Use preparation counts as secondary ordering signals.
- Keep existing client priority and next-action display.
- Keep all scan execution CLI-only.

## Acceptance Criteria

- Blocked clients appear before warning clients.
- Warning clients appear before ready clients.
- Clients without missions appear last.
- Tests cover the dashboard client ordering.
- No scanner execution path is added to the web UI.

## Safety Notes

- This sprint only changes dashboard ordering.
- It does not run scanner commands or perform network activity.
- It does not add brute force, exploitation, payloads, or exfiltration.
