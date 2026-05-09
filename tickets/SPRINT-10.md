# Sprint 10 - Web Mission Readiness

## Goal

Help technicians understand whether a mission is ready for scan execution and
reporting from the local web UI, without launching network activity from the
browser.

## Scope

1. Add mission readiness view models for authorization, approved scope, finding
   review, and generated reports.
2. Add safe scan plan previews for Nmap, HTTP headers, and DNS/Mail using
   approved scope only.
3. Show readiness and plan previews on the mission page.
4. Keep scan execution CLI-only.
5. Add unit tests for readiness states and plan previews.

## Safety Constraints

- No scan execution route in the web application.
- No live network requests.
- No shell command execution.
- Plans must be derived from the same approved scope rules as the CLI.

## Acceptance Criteria

- Mission pages show ready, warning, or blocked readiness states.
- Mission pages show safe planned commands or checks when applicable.
- Unavailable scan plans are shown as blocked with a clear reason.
- Unit tests cover both ready and blocked readiness paths.
