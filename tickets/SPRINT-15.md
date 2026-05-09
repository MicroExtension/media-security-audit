# Sprint 15 - Web Counter-test Plan

## Goal

Show technicians which findings are ready for counter-test from the mission
page, without launching scanner execution from the browser.

## Scope

1. Add counter-test view models for actionable findings.
2. Include findings with confirmed, remediated, or counter-test failed status.
3. Exclude false positives, accepted risks, new findings, and passed
   counter-tests.
4. Show remediation and counter-test instructions on the mission page.
5. Add unit tests for counter-test plan filtering.

## Safety Constraints

- No scan execution route in the web application.
- No live network requests.
- Counter-test plan is a checklist view only.
- Finding status changes continue through the existing review form.

## Acceptance Criteria

- Mission pages show a counter-test plan for actionable findings.
- Findings with passed counter-tests do not appear in the plan.
- Empty plans show a clear empty state.
- Unit tests cover counter-test plan selection.
