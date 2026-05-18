# Sprint 87 - Accessible Form Labels

## Goal

Improve form accessibility across the web UI by giving each operational form an
explicit accessible name.

## Scope

- Add `aria-label` attributes to filter, creation, update, export, and review
  forms.
- Keep visible form labels and layout unchanged.
- Add a template test that requires named forms.
- Update product notes.

## Acceptance Criteria

- Every form in the web templates has an accessible name.
- The accessible name describes the workflow action.
- Existing form actions, field names, CSRF handling, and routes remain
  unchanged.
- Tests cover the named-form convention.

## Safety

- This sprint only changes web accessibility markup.
- No scanner execution is added.
- No network activity is added.
