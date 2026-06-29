# Sprint 259 - Session Workflow Lanes

## Goal

Make the session dashboard easier to scan after an audit has been prepared or
started.

## Scope

- Add guided workflow lanes for discovery, execution, analysis, and delivery.
- Show each lane status with two useful counters.
- Link each lane to the relevant section of the session dashboard.
- Keep the existing command center and detailed progress steps available.

## Safety

- No scanner execution behavior is changed.
- No authorization, scope, or explicit launch guardrail is changed.
- The workflow lanes are read-only and use existing mission data.

## Acceptance

- The session dashboard displays the four workflow lanes.
- Lanes reflect target, service, run, finding, CVE/KEV, report, and package
  state.
- Small screens collapse the workflow lanes into one column.
- Tests cover the template, CSS, and computed lane data.
