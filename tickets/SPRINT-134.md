# Sprint 134 - Verify Offline Preview

## Goal

Let technicians verify that an offline update preview still matches its source
package and extracted source folder without applying any update.

## Scope

- Add `scripts/debian-vm-verify-offline-update-preview.sh`.
- Verify `preview-manifest.txt` in a preview folder.
- Confirm package name, size, SHA-256, preview path, and top-level source
  folder.
- Confirm explicit non-application status values.
- Update README, deployment notes, next steps, and roadmap.
- Extend deployment file tests.

## Acceptance Criteria

- Preview verification is read-only.
- Preview verification fails when the source package metadata does not match.
- Preview verification fails when the top-level source folder is missing.
- The helper does not extract packages, apply updates, pull code, build images,
  restart services, collect logs, or run scanners.

## Safety

- No live scanner execution.
- No Git pull.
- No Docker build, run, or service startup.
- No package extraction.
- No package application.
- No customer data collection.
- No destructive filesystem operations.
