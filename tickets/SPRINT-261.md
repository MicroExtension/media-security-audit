# Sprint 261 - Session Activity Timeline

## Goal

Make the session dashboard easier to read during and after a controlled pilot
audit.

## Scope

- Add a compact activity timeline to the session dashboard.
- Show mission preparation, latest scan runs, finding review, CVE/KEV review,
  generated reports, and handoff package state when available.
- Link each timeline item to the matching review section.
- Keep the existing command center, workflow lanes, result explorer, and
  detailed tables unchanged.

## Safety

- No scanner execution behavior is changed.
- No authorization, scope, or explicit launch guardrail is changed.
- The timeline is read-only and uses existing mission/session data.

## Acceptance

- The session dashboard exposes a timeline section.
- Timeline items show status, timestamp, short detail, and action link.
- Latest scan runs appear before detailed run tables.
- Tests cover the template, CSS, and computed timeline data.
