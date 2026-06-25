# Sprint 248 - Client And Audit List UX Polish

## Goal

Make the Clients and Audits pages feel like operator workspaces instead of dense
administrative tables.

## Scope

- Add operator-style hero sections to the Clients and Audits pages.
- Add local search bars for clients and audits.
- Add quick navigation shortcuts for common technician actions.
- Improve visible French labels for client creation, audit creation, audit status,
  preparation, scope, and next actions.
- Preserve existing routes, forms, and non-destructive workflow behavior.

## Safety

- No scanner behavior changes.
- No new live network activity.
- No brute force, exploitation, payload, or destructive automation.
- UI filtering runs locally in the browser against already-rendered rows.

## Acceptance Criteria

- Clients page exposes a clearer customer directory workflow.
- Audits page exposes a clearer task-list workflow.
- Existing client and mission forms still post to their current endpoints.
- Unit tests cover the new templates and CSS hooks.
