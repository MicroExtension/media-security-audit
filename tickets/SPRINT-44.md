# Sprint 44 - Client Preparation Counts

## Goal

Make the dashboard client list show which customer accounts need preparation
attention without opening each client detail page.

## Scope

- Add per-client blocked, warning, and ready preparation counts to dashboard
  client rows.
- Reuse the existing mission preparation classification.
- Show those counts in the dashboard Clients table.
- Keep all scan execution CLI-only.

## Acceptance Criteria

- Dashboard client rows include blocked, warning, and ready preparation counts.
- Counts are derived only from missions belonging to each client.
- Existing workspace preparation totals remain unchanged.
- Tests cover per-client preparation counts.
- No scanner execution path is added to the web UI.

## Safety Notes

- This sprint only reads stored mission metadata and findings.
- It does not run scanner commands or perform network activity.
- It does not add brute force, exploitation, payloads, or exfiltration.
