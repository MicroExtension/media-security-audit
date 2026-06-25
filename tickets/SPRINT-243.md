# Sprint 243 - Operator Start Workflow

## Goal

Make the web application easier to enter for a MEDIA technician before adding
more scan modules.

## Scope

1. Add a dedicated `/operator` start page.
2. Link client creation, guided audit creation, target setup, service selection,
   audit console, session dashboard, reports, CVE catalog, and VM readiness.
3. Show current workspace counters and recent audit sessions without crowding
   the page.
4. Keep explicit safety guardrails: no exploitation, payloads, post-exploitation,
   or brute-force workflow in the V1 operator path.
5. Add tests and documentation for the new entry point.

## Acceptance Criteria

- The main navigation exposes a Start link.
- The Overview dashboard links to the operator page.
- The operator page gives technicians a six-step audit path.
- Active audits link directly to mission detail, audit console, session
  dashboard, and the current next action.
- The page links to VM test readiness, system status, CVE catalog,
  remediations, exports, and pilot checklist.
- Unit tests cover route registration, template content, CSS, and navigation.
