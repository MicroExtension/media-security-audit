# Sprint 24 - Workspace Inventory Diagnostics

## Goal

Expose read-only workspace inventory and integrity diagnostics on the System
page so appliance operators can quickly understand local data health.

## Scope

1. Add workspace inventory metrics for clients, missions, ready missions,
   findings, activity events, scan runs, reports, authorization briefs, and
   mission exports.
2. Detect missing client references from mission records.
3. Detect orphan mission folders under findings, activity, scan runs, and
   reports.
4. Render the inventory and integrity status on the System page.
5. Add unit tests for healthy and inconsistent workspaces.

## Safety Constraints

- Diagnostics are read-only.
- No scan execution is added.
- No automatic repair, deletion, or restore action is added.
- Existing backup and report directories are inspected only through known local
  paths.

## Acceptance Criteria

- System status includes inventory metrics.
- Healthy workspaces show a ready integrity status.
- Missing client references are reported as blocked.
- Orphan data/report folders are reported as warnings.
- Unit tests cover the workflow without network activity.
