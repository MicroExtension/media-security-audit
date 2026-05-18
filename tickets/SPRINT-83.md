# Sprint 83 - Visible Keyboard Focus

## Goal

Improve keyboard accessibility across the local web interface by adding a clear
focus indicator for interactive controls.

## Scope

- Add shared `:focus-visible` styling for links, buttons, inputs, selects, and
  textareas.
- Keep the style restrained and consistent with the existing UI palette.
- Update tests and product notes.

## Acceptance Criteria

- Keyboard focus is visibly highlighted on shared interactive elements.
- Focus styling does not change pointer hover behavior.
- The shared CSS includes focus coverage for forms and buttons.
- Existing page behavior remains unchanged.

## Safety

- This sprint only changes shared web styling.
- No scanner execution is added.
- No network activity is added.
