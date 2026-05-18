# Sprint 88 - Accessible Form Field Groups

## Goal

Improve the mission workflow forms by grouping related checkbox controls with
explicit `fieldset` and `legend` markup.

## Scope

- Group mission audit-check selection controls.
- Group scope status checkboxes for new and existing scope items.
- Add minimal shared styling for field groups.
- Add a template regression test for grouped controls.
- Update product notes.

## Acceptance Criteria

- Checkbox groups have explicit legends.
- Existing field names, form actions, and CSRF handling remain unchanged.
- The visual layout remains compact and consistent with the existing UI.
- Tests cover the field-group convention.

## Safety

- This sprint only changes mission form markup and CSS.
- No scanner execution is added.
- No network activity is added.
