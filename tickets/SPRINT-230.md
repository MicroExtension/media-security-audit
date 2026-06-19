# Sprint 230 - Wizard Target Coverage Guard

Status: implemented.

## Goal

Keep the guided audit wizard aligned with server-side target coverage
validation.

## Scope

- Treat selected services as ready only when matching target coverage exists.
- Block wizard progression and final creation when service coverage is missing.
- Update the final review checklist wording from selected checks to covered
  checks.
- Update tests and documentation.

## Out of Scope

- Do not run scans.
- Do not change server-side scan execution.
- Do not add external network activity.
- Do not change mission storage behavior.

## Acceptance Criteria

- The wizard checks step blocks progress when selected services lack matching
  target coverage.
- Final creation remains disabled until selected services are covered and scope
  is confirmed.
- The server-side guided target validation remains unchanged.
- Existing tests continue to pass.
