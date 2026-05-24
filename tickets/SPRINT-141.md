# Sprint 141 - Counter-Test Note Guardrails

## Goal

Require technician notes when a finding is marked as a counter-test result.

## Scope

- Extend finding review note guardrails to `counter_test_passed` and
  `counter_test_failed`.
- Update the mission finding review form guidance.
- Update README, roadmap, and product next steps.
- Add storage and web form regression tests.

## Acceptance Criteria

- `false_positive`, `accepted_risk`, `counter_test_passed`, and
  `counter_test_failed` cannot be saved without a review note.
- Counter-test pass/fail notes are stored as finding review notes.
- Non-exception statuses can still clear the review note.
- No scan execution, scanner defaults, deployment scripts, or report generation
  behavior is changed.

## Safety

- No live scanner execution.
- No network activity added.
- No destructive test added.
- No automatic exploitation or brute force.
- No deployment apply workflow added.
