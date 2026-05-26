# Sprint 164 - Export Inventory Filters

## Goal

Let technicians filter the web mission export inventory before handoff review
and keep the same filtered state in exported JSON and Markdown files.

## Scope

- Add search and status filtering for mission export inventory items.
- Add filter controls to `/exports`.
- Preserve the missing-package toggle with current filters.
- Preserve current filters in JSON and Markdown downloads.
- Include filter metadata in downloaded inventory files.
- Update tests and documentation.

## Out Of Scope

- No scanner execution.
- No report regeneration.
- No package mutation.
- No archive extraction workflow.
- No customer network activity.

## Acceptance Criteria

- `/exports` can filter by search text and status.
- Export downloads use the same search, status, and missing-package filters.
- JSON downloads include filter metadata.
- Markdown downloads include filter metadata and filtered rows.
