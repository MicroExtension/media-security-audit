# Sprint 85 - Accessible Table Captions

## Goal

Improve table accessibility across operational web pages by adding screen-reader
captions that describe each table's purpose.

## Scope

- Add a shared `sr-only` CSS helper.
- Add hidden captions to dashboard, client, mission, activity, and system
  tables.
- Add tests ensuring table captions stay aligned with table usage.
- Update product notes.

## Acceptance Criteria

- Every operational table in the updated templates has a caption.
- Captions are available to assistive technology without adding visual clutter.
- Existing table layout, data, and actions remain unchanged.
- Tests cover the caption convention.

## Safety

- This sprint only changes web accessibility markup and CSS.
- No scanner execution is added.
- No network activity is added.
