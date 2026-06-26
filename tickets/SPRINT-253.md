# Sprint 253 - Session Command Center UX

## Goal

Make the session dashboard the technician's primary real-condition audit
workspace.

## Scope

- Add a priority command center to the session dashboard.
- Summarize go/no-go, execution follow-up, CVE/KEV review, and delivery.
- Link each command card back to the detailed mission section.
- Keep the session page responsive for smaller operator screens.
- Update documentation and static UI tests.

## Acceptance Criteria

- The session dashboard exposes a command center immediately after the progress hero.
- The command center shows four priority cards with status, detail, count, and action.
- Cards link to existing detailed mission sections instead of duplicating workflows.
- The command center is responsive on narrow screens.
- Tests verify template hooks and CSS classes.

## Safety

- No scanner execution logic is changed.
- No network target is contacted.
- No brute force, exploitation, payload, or destructive action is added.
