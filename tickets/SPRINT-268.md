# Sprint 268 - Controlled Test Pilot Pack

## Goal

Make the session dashboard easier to use during a first controlled field test by
showing a compact pilot pack with the exact operational checks to review.

## Scope

- Add pilot pack data to the session dashboard.
- Show the VM update command, approved scope status, launchable controls,
  evidence status, and delivery readiness.
- Link each pack item to the matching mission or readiness section.
- Keep the pack short, status-driven, and readable on small screens.
- Update tests and documentation.

## Safety

- No scanner execution changes.
- No brute force, exploitation, payload, or credential attack flow.
- No external network dependency.
- The pack only summarizes safe operational steps and stored mission state.

## Acceptance Criteria

- Session dashboards expose a controlled test pilot pack.
- The pack includes VM command, scope, controls, evidence, and deliverables.
- Pack items show ready, warning, missing, or blocked status using existing
  mission state.
- Existing controlled test gate, runbook, and execution queue behavior remains
  unchanged.
- Unit tests pass.
