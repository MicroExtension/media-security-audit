# Sprint 166 - Export Filter Context

## Goal

Make the mission export inventory easier to review by showing active filter
context and page shortcuts.

## Scope

- Add page shortcuts for filters, inventory, and downloads.
- Show active search, status, and missing-package filters.
- Show visible item count against the unfiltered inventory count.
- Add a clear filters action.
- Keep existing filtered CSV, JSON, and Markdown downloads unchanged.
- Update tests and documentation.

## Out Of Scope

- No scanner execution.
- No report regeneration.
- No package mutation.
- No archive extraction workflow.
- No customer network activity.

## Acceptance Criteria

- `/exports` exposes shortcuts to filters, inventory, and downloads.
- Active filters are summarized when filters are applied.
- Clearing filters returns to the unfiltered export inventory.
- Existing download links still preserve current filters.
