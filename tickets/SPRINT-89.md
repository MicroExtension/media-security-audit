# Sprint 89 - Required Field Indicators

## Goal

Make required fields visible in the web UI so technicians can understand which
inputs must be completed before submitting operational forms.

## Scope

- Add shared CSS for required field indicators.
- Cover text inputs, selects, and textareas in field grids and finding review
  forms.
- Keep native `required` validation unchanged.
- Add a regression test for the required-field styling convention.
- Update product notes.

## Acceptance Criteria

- Required fields display a consistent visual marker.
- Existing form field names, actions, and validation remain unchanged.
- The marker uses the existing UI color system.
- Tests cover the shared required-field styling.

## Safety

- This sprint only changes CSS and documentation/tests.
- No scanner execution is added.
- No network activity is added.
