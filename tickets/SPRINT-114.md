# Sprint 114 - Debian VM Backup Manifest

## Goal

Give technicians a simple integrity manifest for backup archives before copying
or archiving them outside the appliance VM.

## Scope

- Add `scripts/debian-vm-backup-manifest.sh`.
- Require a backup archive path.
- Verify the archive with the existing backup verification helper.
- Write a sidecar manifest containing archive name, size, SHA-256, and
  verification status.
- Update deployment documentation and static safety tests.

## Acceptance Criteria

- The helper refuses missing or empty archives.
- The helper runs backup verification before writing the manifest.
- The helper writes `<backup.tgz>.manifest.txt`.
- The helper does not extract or restore data.
- The helper does not start services, collect logs, install packages, or run
  scanners.

## Safety

- No scanner execution is added.
- No network target is contacted by the application.
- The helper only reads a local backup archive and writes local checksum
  metadata.
