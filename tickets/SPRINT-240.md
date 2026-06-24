# Sprint 240 - Mission Operator Console

## Goal

Make a real audit easier to run by adding a focused mission console that guides a
technician through preparation, launch, analysis, and delivery without exposing
every detailed form on the first screen.

## Scope

1. Add `/missions/{mission_id}/console`.
2. Redirect guided audit creation to the mission console.
3. Add console entry points from mission detail and audit list pages.
4. Present four operational phases: Prepare, Launch, Analyze, Deliver.
5. Reuse existing mission readiness, launch, CVE/KEV, and delivery view models.
6. Keep detailed editing on the full mission page.

## Acceptance Criteria

- A guided audit lands on the mission console after creation.
- The mission page exposes an Open Console action.
- The Audits page exposes console links for mission cards and rows.
- The console shows go/no-go gates, selected service status, CVE/KEV candidates,
  and delivery checklist items.
- Tests cover the route, template markers, navigation links, and styles.

## Safety

- No scanner behavior is changed.
- No brute force or exploit automation is added.
- The console links to guarded launch forms instead of bypassing authorization checks.
