# Sprint 133 - Offline Preview Manifest

## Goal

Make offline update package previews auditable without applying any package to
the live repository or customer data folders.

## Scope

- Extend `scripts/debian-vm-offline-update-preview.sh`.
- Write `preview-manifest.txt` inside each preview folder.
- Record package name, package path, size, SHA-256, preview path, and top-level
  source folder.
- Record explicit non-application status.
- Update README, deployment notes, next steps, and roadmap.
- Extend deployment file tests.

## Acceptance Criteria

- Preview extraction still verifies the source package first.
- Preview extraction remains isolated from live folders.
- Each preview folder contains local metadata for technician review.
- The helper does not apply packages, pull code, build images, restart services,
  collect logs, or run scanners.

## Safety

- No live scanner execution.
- No Git pull.
- No Docker build, run, or service startup.
- No package application.
- No customer data collection.
- No destructive filesystem operations.
