# Sprint 163 - Export Inventory Downloads

## Goal

Let technicians download the global mission export inventory from the web UI for
handoff review and local archival.

## Scope

- Add JSON and Markdown export formats for mission export inventory.
- Add `/exports/download/{format}` web downloads.
- Add download actions to the `/exports` page.
- Preserve the current missing-package toggle in downloads.
- Update tests and documentation.

## Out Of Scope

- No scanner execution.
- No report regeneration.
- No package mutation.
- No archive extraction workflow.
- No customer network activity.

## Acceptance Criteria

- `/exports` exposes JSON and Markdown download actions.
- JSON download contains summary and item details.
- Markdown download contains summary, execution marker, and package rows.
- Downloads reuse the inventory state and do not create scan run records.
