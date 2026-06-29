# Sprint 260 - Session Result Explorer

## Goal

Make session results easier to navigate during a pilot audit.

## Scope

- Add a result explorer to the session dashboard.
- Provide quick cards for targets, services, executions, CVE/KEV candidates,
  findings, and deliverables.
- Show each card status, count, short meaning, and target section link.
- Keep existing detailed session sections unchanged.

## Safety

- No scanner execution behavior is changed.
- No authorization, scope, or explicit launch guardrail is changed.
- The result explorer is read-only and uses existing mission/session data.

## Acceptance

- The session dashboard exposes six result shortcut cards.
- Cards link to the relevant session sections.
- Result statuses are computed from existing target, service, run, finding,
  CVE/KEV, report, and export state.
- Tests cover the template, CSS, and computed shortcut data.
