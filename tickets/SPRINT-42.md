# Sprint 42 - Client Preparation Summary

## Goal

Help technicians understand which missions still need preparation directly
from the client detail page.

## Scope

- Add client-level mission preparation rows.
- Summarize blocked, warning, and ready mission counts.
- Show missing authorization, approved scope, and check selection status.
- Flag missions with new findings awaiting review.
- Keep all scan execution CLI-only.

## Acceptance Criteria

- Client detail pages show preparation status for each mission.
- Blocked missions appear before warning and ready missions.
- Preparation rows only include missions for the selected client.
- Tests cover blocked, warning, and ready preparation states.
- No scanner execution path is added to the web UI.

## Safety Notes

- This sprint only reads stored mission metadata and findings.
- It does not run scanner commands or perform network activity.
- It does not add brute force, exploitation, payloads, or exfiltration.
