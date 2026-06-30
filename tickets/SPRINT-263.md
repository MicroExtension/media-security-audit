# Sprint 263 - Session Client Brief

## Goal

Make the session dashboard easier to use during customer restitution by adding a
short client briefing block above the operator command center.

## Scope

- Add a session client brief model.
- Surface the current decision, priority focus, immediate action, validation,
  and delivery status.
- Use the highest-priority active finding when one exists.
- Show a ready/missing fallback when the session has no active finding yet.
- Keep the section visually aligned with the dark operator dashboard.
- Update tests and documentation.

## Safety

- No scanner execution changes.
- No brute force, exploitation, payload, or credential attack flow.
- No external network dependency.
- The brief only summarizes stored mission data and existing report readiness.

## Acceptance Criteria

- The session dashboard template exposes a dedicated client brief section.
- The brief links to findings, reports, or service preparation depending on the
  current session state.
- A high or critical active finding produces a warning brief with remediation
  and counter-test guidance.
- Existing session progress, workflow, result explorer, timeline, and
  remediation priority behavior remains unchanged.
- Unit tests pass.
