# Sprint 252 - Run Monitor UX

## Goal

Make mission execution follow-up easier to use during a controlled real-condition
test.

## Scope

- Add a run monitor control center to mission pages.
- Show run, finding, evidence, and ready-service counts.
- Add browser-side run search and status filters.
- Keep run cards and table rows synchronized when filters change.
- Update documentation and static UI tests.

## Acceptance Criteria

- The mission page exposes run monitor metrics before the run cards.
- Technicians can filter runs by all, completed, failed, and runs with findings.
- Search filtering never launches a scan and only changes the current page view.
- Run cards and run table rows hide/show together for the same execution.
- Tests verify template hooks and CSS classes.

## Safety

- No scanner execution logic is changed.
- No network target is contacted.
- No brute force, exploitation, payload, or destructive action is added.
