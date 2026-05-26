# Sprint 165 - Export Inventory CSV Download

## Goal

Let technicians export the filtered mission export inventory as CSV for
spreadsheet review during handoff.

## Scope

- Add CSV as a mission export inventory web download format.
- Add a CSV action to the `/exports` page.
- Preserve existing search, status, and missing-package filters.
- Include stable package and integrity columns.
- Update tests and documentation.

## Out Of Scope

- No scanner execution.
- No report regeneration.
- No package mutation.
- No archive extraction workflow.
- No customer network activity.

## Acceptance Criteria

- `/exports` exposes a CSV download action.
- CSV output contains one row per filtered inventory item.
- CSV output includes mission, client, package, status, and integrity columns.
- Existing JSON and Markdown downloads remain unchanged.
