# Sprint 265 - Session Execution Queue

## Goal

Make the session dashboard easier to use during a controlled test by showing a
clear execution queue for selected checks.

## Scope

- Add a session execution queue model.
- Combine scan plan readiness with the latest stored run per selected check.
- Show planned command count, latest run status, finding count, evidence count,
  and next action.
- Add a dedicated execution queue section and shortcut on the session dashboard.
- Update tests and documentation.

## Safety

- No scanner execution changes.
- No brute force, exploitation, payload, or credential attack flow.
- No external network dependency.
- The queue only summarizes stored scan plans and stored run metadata.

## Acceptance Criteria

- Session dashboards expose an execution queue for selected checks.
- Completed checks show the latest stored run counters.
- Ready and blocked checks point to safe preparation or execution sections.
- Existing progress, client brief, result explorer, timeline, finding explainer,
  and remediation priority behavior remains unchanged.
- Unit tests pass.
