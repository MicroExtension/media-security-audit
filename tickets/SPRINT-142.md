# Sprint 142 - Counter-Test Review Actions

## Goal

Let technicians record counter-test pass or fail decisions directly from the
mission counter-test plan.

## Scope

- Add pass/fail review actions to counter-test plan cards.
- Require a counter-test note before submitting either action.
- Preserve the existing finding status update endpoint and guardrails.
- Keep scan execution CLI-only.
- Update documentation and UI regression tests.

## Acceptance Criteria

- Counter-test plan cards expose a required note field.
- Counter-test plan cards can submit `counter_test_passed`.
- Counter-test plan cards can submit `counter_test_failed`.
- Existing review note guardrails still reject empty counter-test notes.
- No browser scan execution, new scanner default, deployment apply workflow, or
  network activity is added.

## Safety

- No live scanner execution.
- No network activity added.
- No brute force or exploitation.
- No destructive test.
- Counter-test actions are status review actions only.
