# Sprint 222 - Scan Launch Confirmation

Status: implemented.

## Goal

Make guarded web scan execution easier to understand before a technician clicks a
live run button.

## Scope

- Add a pre-launch decision box to every ready scan plan.
- Remind the technician that written authorization is recorded.
- Remind the technician that matching approved scope exists.
- Show that the listed command count is what will execute.
- Remind the technician that live execution may contact target systems.
- Replace the short confirmation label with an explicit authorization, scope,
  service, and command confirmation.
- Show a clearer blocked-launch message for blocked plans.

## Out of Scope

- Do not add new scanners.
- Do not change execution guards.
- Do not bypass authorization, scope, or explicit confirmation requirements.
- Do not add brute force, exploitation, payload, or exfiltration features.

## Acceptance Criteria

- Ready plans show a pre-launch decision box before the run form.
- Blocked plans show a blocked launch decision and readiness action.
- The run confirmation text is explicit enough for technician use.
- Existing tests continue to pass.
