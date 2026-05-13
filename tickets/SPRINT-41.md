# Sprint 41 - Client Activity Summary

## Goal

Make each client detail page more useful for multi-client follow-up by showing
recent activity from that client's missions.

## Scope

- Add a client-level recent activity view model.
- Show recent client activity on the client detail page.
- Link from the client detail page to the workspace Activity page filtered by
  client.
- Keep all scan execution CLI-only.

## Acceptance Criteria

- Client detail pages include recent activity events from that client's
  missions only.
- Activity events include the source mission and a timestamp.
- The client page links to `/activity` with the matching client filter.
- Tests cover the client activity filtering behavior.
- No scanner execution path is added to the web UI.

## Safety Notes

- This sprint is read-only from a scanner perspective.
- It only reuses stored mission activity events.
- It does not add network activity, exploitation, brute force, payloads, or
  exfiltration.
