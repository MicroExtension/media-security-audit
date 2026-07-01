# Sprint 267 - Controlled Test Operator Runbook

## Goal

Make the session dashboard usable during a first controlled real-world pilot by
showing a short operator runbook directly next to the test decision gate.

## Scope

- Add controlled test runbook step data to the session dashboard.
- Cover before, during, and after the pilot test.
- Remind technicians to update the VM and verify readiness.
- Link each step to the matching safe review section.
- Keep the runbook short and status-driven.
- Update tests and documentation.

## Safety

- No scanner execution changes.
- No brute force, exploitation, payload, or credential attack flow.
- No external network dependency.
- The runbook only summarizes safe operational steps and stored mission state.

## Acceptance Criteria

- Session dashboards expose a controlled test runbook.
- The runbook includes VM readiness, authorization/scope, ready checks,
  monitoring, and delivery steps.
- Steps show ready, warning, missing, or blocked status using existing mission
  state.
- Existing controlled test gate and execution queue behavior remains unchanged.
- Unit tests pass.
