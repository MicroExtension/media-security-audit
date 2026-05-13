# Sprint 43 - Dashboard Preparation Summary

## Goal

Make the workspace dashboard show mission preparation blockers across all
clients before a technician opens individual client pages.

## Scope

- Add dashboard-level preparation rows with client and mission context.
- Summarize blocked, warning, and ready mission preparation counts.
- Show missing authorization, approved scope, and check selection status.
- Reuse the existing preparation logic from client detail pages.
- Keep all scan execution CLI-only.

## Acceptance Criteria

- The dashboard shows preparation status for every mission in the workspace.
- Blocked missions appear before warning and ready missions.
- Dashboard preparation rows include client links and mission links.
- Tests cover blocked, warning, and ready dashboard states.
- No scanner execution path is added to the web UI.

## Safety Notes

- This sprint only reads stored mission metadata and findings.
- It does not run scanner commands or perform network activity.
- It does not add brute force, exploitation, payloads, or exfiltration.
