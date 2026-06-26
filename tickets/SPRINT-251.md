# Sprint 251 - Service Readiness UX

## Goal

Make the mission page easier to use before a real-condition test by giving the
technician a clear service readiness center.

## Scope

- Add a service readiness center on mission detail pages.
- Show selected, ready, blocked, and recorded run counts.
- Add browser-side service search and filters.
- Keep service cards tied to their readiness and last run state.
- Repeat execution guardrails before scan launch.
- Update documentation and static UI tests.

## Acceptance Criteria

- The mission page exposes a `service-readiness` shortcut.
- Technicians can filter visible service cards by all, selected, ready, and blocked.
- Search filtering never launches a scan and only changes the current page view.
- Service execution guardrails remain visible before launch.
- Tests verify template hooks and CSS classes.

## Safety

- No scanner execution logic is changed.
- No network target is contacted.
- No brute force, exploitation, payload, or destructive action is added.
