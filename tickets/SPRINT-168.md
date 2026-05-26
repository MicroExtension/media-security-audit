# Sprint 168 - Client Export Inventory Links

## Goal

Make client-specific handoff review easier by linking directly from client
workflows to the filtered mission export inventory.

## Scope

- Add a stable client export inventory URL helper.
- Expose filtered export inventory links on client detail pages.
- Expose filtered export inventory links in dashboard client rows.
- Update documentation and regression tests.

## Out Of Scope

- No scanner execution changes.
- No live network activity.
- No mission package generation changes.
- No export package extraction or restore workflow.

## Acceptance Criteria

- Client detail pages link to `/exports?client_id=<client_id>`.
- Dashboard client rows link to the same filtered export inventory.
- Existing activity and preparation links remain available.
- Tests cover the new view model URL and template wiring.
