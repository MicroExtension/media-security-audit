# Sprint 139 - Offline Apply Checklist

## Goal

Prepare the future offline update application workflow with a final read-only
checklist, without applying any package.

## Scope

- Add `scripts/debian-vm-offline-update-apply-checklist.sh`.
- Require an offline update package and preview folder.
- Verify package and preview metadata.
- Run the read-only offline update plan.
- Record explicit non-application status.
- Update README, deployment notes, next steps, and roadmap.
- Extend deployment file tests.

## Acceptance Criteria

- Checklist fails if package verification fails.
- Checklist fails if preview verification fails.
- Checklist records `application=not_implemented`.
- The helper does not extract packages, apply updates, replace files, build
  images, restart services, collect logs, or run scanners.

## Safety

- No live scanner execution.
- No package application.
- No package extraction.
- No file replacement.
- No customer data collection.
- No application logs collected.
- No destructive filesystem operations.
