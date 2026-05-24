# Sprint 144 - Counter-Test Rollups

## Goal

Show counter-test status rollups on dashboard and client pages.

## Scope

- Reuse the mission counter-test summary model for workspace and client views.
- Add a dashboard counter-test summary section.
- Add a client counter-test summary section.
- Keep counter-test actions scoped to mission pages.
- Update documentation and UI tests.

## Acceptance Criteria

- Dashboard shows ready, passed, and failed counter-test counts for the workspace.
- Client pages show ready, passed, and failed counter-test counts scoped to the client.
- Dashboard and client shortcut links include the new counter-test sections.
- Mission counter-test behavior remains unchanged.
- No scanner execution, network activity, or deployment workflow is added.

## Safety

- No live scanner execution.
- No browser scan execution.
- No network activity added.
- No destructive test.
- This sprint only summarizes stored finding statuses.
