# Sprint 137 - Offline Preview Inventory

## Goal

Give technicians a read-only inventory of offline update preview folders and
their preview manifest status.

## Scope

- Add `scripts/debian-vm-offline-update-preview-inventory.sh`.
- List preview folders under `reports/offline-update-previews` by default.
- Support `MEDIA_AUDIT_OFFLINE_UPDATE_PREVIEW_DIR`.
- Support `--verify-manifests`.
- Report preview folder, manifest status, source package, and top-level source
  folder.
- Update README, deployment notes, next steps, and roadmap.
- Extend deployment file tests.

## Acceptance Criteria

- Preview inventory is read-only.
- Preview inventory can verify preview manifests when requested.
- Preview inventory reports missing and failed manifests.
- The helper does not delete previews, extract packages, apply updates, build
  images, restart services, collect logs, or run scanners.

## Safety

- No live scanner execution.
- No package application.
- No package extraction.
- No customer data collection.
- No application logs collected.
- No destructive filesystem operations.
