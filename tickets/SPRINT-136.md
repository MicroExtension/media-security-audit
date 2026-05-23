# Sprint 136 - Maintenance Preview Status

## Goal

Include offline update preview verification status in maintenance reports without
applying any offline update package.

## Scope

- Extend `scripts/debian-vm-maintenance-report.sh`.
- Support optional `MEDIA_AUDIT_OFFLINE_UPDATE_PACKAGE`.
- Support optional `MEDIA_AUDIT_OFFLINE_UPDATE_PREVIEW`.
- Verify the preview manifest when a preview folder is provided.
- Run the offline update plan with package and preview context when available.
- Update README, deployment notes, next steps, and roadmap.
- Extend deployment file tests.

## Acceptance Criteria

- Maintenance reports can record offline preview verification status.
- Missing preview input is recorded as not provided, not treated as a destructive
  action.
- Failed preview verification marks the maintenance report as failed.
- The helper does not extract packages, apply updates, start services, collect
  logs, or run scanners.

## Safety

- No live scanner execution.
- No package application.
- No package extraction by the maintenance report.
- No customer data collection.
- No application logs collected.
- No destructive filesystem operations.
