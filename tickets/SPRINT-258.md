# Sprint 258 - Session Progress Readability

## Goal

Make the analysis session dashboard easier to understand during a pilot test.

## Scope

- Add a readable progress summary near the top of the session dashboard.
- Show the active phase, ready workflow steps, remaining attention items, and
  blockers.
- Show the next technician action with the same source of truth as the
  existing session workflow.
- Keep the detailed progress cards available below the summary.

## Safety

- No scan execution is changed.
- No authorization, scope, or launch guardrail is changed.
- The summary is read-only and uses existing mission/session data.

## Acceptance

- The session dashboard shows a progress summary before detailed steps.
- The summary includes the active phase, ready step count, blocker count, and
  next action detail.
- The layout remains responsive on small screens.
- Tests cover the template, CSS, and computed session counters.
