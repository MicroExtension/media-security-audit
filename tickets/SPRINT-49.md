# Sprint 49 - Finding Review Note Guardrails

## Goal

Improve report defensibility by requiring a technician review note before a
finding can be marked as a false positive or an accepted risk.

## Scope

- Enforce the rule in the shared JSON store/domain workflow.
- Surface the expectation in the mission finding review form.
- Add unit tests for storage and form behavior.
- Update project documentation.

## Acceptance Criteria

- `false_positive` cannot be saved without a review note.
- `accepted_risk` cannot be saved without a review note.
- Other finding statuses can still clear the review note.
- Existing activity and reporting behavior remains unchanged.

## Safety

- No live scanner execution is added.
- No network activity is added.
- The change only affects finding review metadata validation.
