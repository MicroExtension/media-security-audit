# Sprint 129 - Offline Package Inventory

## Goal

Give technicians a read-only way to list local offline update packages and see
whether their sidecar manifests are present or verified.

## Scope

- Add `scripts/debian-vm-offline-update-inventory.sh`.
- List packages from `MEDIA_AUDIT_OFFLINE_UPDATE_DIR` or `dist/offline-updates`.
- Support optional `--verify-manifests`.
- Update README, deployment notes, next steps, and roadmap.
- Extend deployment file tests.

## Acceptance Criteria

- Inventory lists `media-audit-offline-update-*.tgz` packages.
- Manifest status is `missing`, `present`, `verified`, or `failed`.
- Verification uses `scripts/debian-vm-verify-offline-update-package.sh`.
- The helper does not delete packages, extract archives, apply updates, pull
  code, build images, restart services, collect logs, or run scanners.

## Safety

- No live scanner execution.
- No Git pull.
- No Docker build, run, or service startup.
- No archive extraction.
- No customer data collection.
- No destructive filesystem operations.
