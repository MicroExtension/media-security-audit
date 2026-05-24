# Sprint 140 - Maintenance Apply Checklist

## Goal

Include the read-only offline apply checklist in maintenance reports when package
and preview context are provided.

## Scope

- Extend `scripts/debian-vm-maintenance-report.sh`.
- Run `scripts/debian-vm-offline-update-apply-checklist.sh` when
  `MEDIA_AUDIT_OFFLINE_UPDATE_PACKAGE` and `MEDIA_AUDIT_OFFLINE_UPDATE_PREVIEW`
  are set.
- Record `not_provided` when package or preview inputs are missing.
- Update documentation and deployment tests.

## Acceptance Criteria

- Maintenance reports record offline apply checklist readiness.
- Missing package or preview context is recorded without applying anything.
- A failed checklist marks the maintenance report as failed.
- No package extraction, package application, file replacement, service restart,
  Docker build/run, application log collection, or scanner execution is added.

## Safety

- No live scanner execution.
- No package application.
- No package extraction.
- No file replacement.
- No customer data collection.
- No application logs collected.
- No destructive filesystem operations.
