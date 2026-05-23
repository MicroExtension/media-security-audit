# Sprint 132 - Offline Package Preview

## Goal

Give technicians a safe way to inspect a verified offline update package without
applying it to the live repository or customer data folders.

## Scope

- Add `scripts/debian-vm-offline-update-preview.sh`.
- Verify the package manifest before extraction.
- Extract packages only into `reports/offline-update-previews` or an explicit
  preview folder.
- Refuse extraction over `.git`, `data`, `runs`, `reports`, or `evidence`.
- Update README, deployment notes, next steps, and roadmap.
- Extend deployment file tests.

## Acceptance Criteria

- Preview extraction requires a verified offline update package.
- Preview extraction never targets the live repository or persistent data
  folders.
- The helper does not apply packages, pull code, build images, restart services,
  collect logs, or run scanners.
- Offline package application remains unimplemented.

## Safety

- No live scanner execution.
- No Git pull.
- No Docker build, run, or service startup.
- No package application.
- No customer data collection.
- No destructive filesystem operations.
